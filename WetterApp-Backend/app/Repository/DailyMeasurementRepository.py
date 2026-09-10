from datetime import date

from sqlalchemy import func

from app.Model.DailyMesaurement import DailyMeasurement
from app.Model.Station import Station
from app.Repository.DbContext import dbcontext

# Die Messwerttabelle wird sehr groß, deshalb nie unbegrenzt abfragen.
MAX_LIMIT = 5000


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
