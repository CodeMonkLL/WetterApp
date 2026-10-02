from datetime import date
from typing import NamedTuple

from sqlalchemy import func

from app.Model.DailyMesaurement import DailyMeasurement
from app.Model.Station import Station
from app.Repository.DbContext import dbcontext

# Die Messwerttabelle wird sehr groß, deshalb nie unbegrenzt abfragen.
MAX_LIMIT = 5000


class TemperatureAverageRow(NamedTuple):
    """Aggregat über eine gefilterte Messwertmenge.

    `first_date`/`last_date` sind der tatsächlich ausgewertete Zeitraum, der
    ohne Datumsfilter dem gesamten Datenbestand entspricht.
    """

    avg_tmk: float | None
    avg_txk: float | None
    avg_tnk: float | None
    days: int
    first_date: date | None
    last_date: date | None


class DailyMeasurementRepository:
    @staticmethod
    def search(
        station_id: str | None = None,
        station_name: str | None = None,
        state: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        newest_first: bool = True,
        limit: int = 100,
        offset: int = 0,
    ) -> list[DailyMeasurement]:
        """Sucht Tageswerte nach Station und Zeitraum.

        Args:
            station_id: Exakte DWD-Station-ID, z.B. "00003".
            station_name: Teilstring des Stationsnamens, Groß-/Kleinschreibung egal.
            state: Bundesland der Station, exakter Treffer.
            date_from: Frühestes Messdatum, einschließlich.
            date_to: Spätestes Messdatum, einschließlich.
            newest_first: Sortierung nach Datum absteigend statt aufsteigend.
            limit: Maximale Trefferzahl, hart begrenzt auf MAX_LIMIT.
            offset: Versatz für Blättern.
        """
        query = DailyMeasurementRepository._filtered(
            station_id, station_name, state, date_from, date_to
        )
        sort_column = DailyMeasurement.date.desc() if newest_first else DailyMeasurement.date.asc()
        query = query.order_by(sort_column, DailyMeasurement.station_id)
        return query.limit(_clamp(limit)).offset(max(0, offset)).all()

    @staticmethod
    def count(
        station_id: str | None = None,
        station_name: str | None = None,
        state: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> int:
        """Zählt die Treffer derselben Filter wie `search`, für Seitenzahlen."""
        return DailyMeasurementRepository._filtered(
            station_id, station_name, state, date_from, date_to
        ).count()

    @staticmethod
    def temperature_average(
        station_id: str | None = None,
        station_name: str | None = None,
        state: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> TemperatureAverageRow:
        """Mittelt Tagesmittel, -maximum und -minimum über dieselben Filter wie `search`.

        Die Aggregation läuft in der Datenbank, also über den kompletten
        Zeitraum statt nur über eine Ergebnisseite. Fehlende Messwerte sind
        NULL und fließen nicht ein.
        """
        avg_tmk, avg_txk, avg_tnk, days, first_date, last_date = (
            DailyMeasurementRepository._filtered(
                station_id, station_name, state, date_from, date_to
            )
            .with_entities(
                func.avg(DailyMeasurement.tmk),
                func.avg(DailyMeasurement.txk),
                func.avg(DailyMeasurement.tnk),
                func.count(DailyMeasurement.tmk),
                func.min(DailyMeasurement.date),
                func.max(DailyMeasurement.date),
            )
            .one()
        )
        return TemperatureAverageRow(
            _as_float(avg_tmk),
            _as_float(avg_txk),
            _as_float(avg_tnk),
            days,
            first_date,
            last_date,
        )

    @staticmethod
    def get(station_id: str, measured_on: date) -> DailyMeasurement | None:
        return DailyMeasurement.query.filter(
            DailyMeasurement.station_id == station_id,
            DailyMeasurement.date == measured_on,
        ).one_or_none()

    @staticmethod
    def latest(station_id: str) -> DailyMeasurement | None:
        """Liefert den jüngsten Tageswert einer Station."""
        return (
            DailyMeasurement.query
            .filter(DailyMeasurement.station_id == station_id)
            .order_by(DailyMeasurement.date.desc())
            .first()
        )

    @staticmethod
    def available_range(station_id: str) -> tuple[date | None, date | None]:
        """Liefert erstes und letztes vorhandenes Messdatum einer Station."""
        first, last = (
            dbcontext.session.query(func.min(DailyMeasurement.date), func.max(DailyMeasurement.date))
            .filter(DailyMeasurement.station_id == station_id)
            .one()
        )
        return first, last

    @staticmethod
    def _filtered(
        station_id: str | None,
        station_name: str | None,
        state: str | None,
        date_from: date | None,
        date_to: date | None,
    ):
        query = DailyMeasurement.query
        if station_name or state:
            query = query.join(Station, Station.station_id == DailyMeasurement.station_id)
        if station_id:
            query = query.filter(DailyMeasurement.station_id == station_id)
        if station_name:
            query = query.filter(Station.name.ilike(f"%{station_name}%"))
        if state:
            query = query.filter(Station.state == state)
        if date_from:
            query = query.filter(DailyMeasurement.date >= date_from)
        if date_to:
            query = query.filter(DailyMeasurement.date <= date_to)
        return query


def _clamp(limit: int) -> int:
    return max(1, min(limit, MAX_LIMIT))


# Postgres liefert AVG als Decimal.
def _as_float(value) -> float | None:
    return float(value) if value is not None else None
