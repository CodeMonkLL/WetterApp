from datetime import date

from app.Model.Station import Station
from app.Repository.DbContext import dbcontext

# Schützt vor versehentlichen Vollabfragen.
MAX_LIMIT = 1000


class StationRepository:
    @staticmethod
    def get(station_id: str) -> Station | None:
        return Station.query.filter(Station.station_id == station_id).one_or_none()

    @staticmethod
    def search(
        name: str | None = None,
        state: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Station]:
        """Sucht Stationen nach Name, Bundesland und Messzeitraum.

        Args:
            name: Teilstring des Stationsnamens, Groß-/Kleinschreibung egal.
            state: Bundesland, exakter Treffer.
            date_from: Nur Stationen, die ab diesem Datum noch Werte liefern.
            date_to: Nur Stationen, die bis zu diesem Datum schon Werte liefern.
            limit: Maximale Trefferzahl, hart begrenzt auf MAX_LIMIT.
            offset: Versatz für Blättern.
        """
        query = StationRepository._filtered(name, state, date_from, date_to)
        query = query.order_by(Station.name, Station.station_id)
        return query.limit(_clamp(limit)).offset(max(0, offset)).all()

    @staticmethod
    def count(
        name: str | None = None,
        state: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> int:
        """Zählt die Treffer derselben Filter wie `search`, für Seitenzahlen."""
        return StationRepository._filtered(name, state, date_from, date_to).count()

    @staticmethod
    def list_states() -> list[str]:
        """Liefert alle vorkommenden Bundesländer, z.B. für ein Filter-Dropdown."""
        rows = (
            dbcontext.session.query(Station.state)
            .filter(Station.state.isnot(None))
            .distinct()
            .order_by(Station.state)
            .all()
        )
        return [row[0] for row in rows]

    @staticmethod
    def _filtered(name: str | None, state: str | None, date_from: date | None, date_to: date | None):
        query = Station.query
        if name:
            query = query.filter(Station.name.ilike(f"%{name}%"))
        if state:
            query = query.filter(Station.state == state)
        # Überlappung: der Messzeitraum der Station muss den gesuchten Zeitraum schneiden.
        if date_from:
            query = query.filter(Station.active_to >= date_from)
        if date_to:
            query = query.filter(Station.active_from <= date_to)
        return query


def _clamp(limit: int) -> int:
    return max(1, min(limit, MAX_LIMIT))
