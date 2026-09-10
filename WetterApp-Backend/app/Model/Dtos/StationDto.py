from dataclasses import dataclass

from app.Model.Station import Station


@dataclass(frozen=True)
class StationDto:
    """Stammdaten einer Station. Datumsfelder sind ISO-Strings (YYYY-MM-DD)."""

    station_id: str
    name: str
    state: str | None
    height: int | None
    latitude: float | None
    longitude: float | None
    active_from: str | None
    active_to: str | None

    @classmethod
    def from_entity(cls, station: Station) -> "StationDto":
        return cls(
            station_id=station.station_id,
            name=station.name,
            state=station.state,
            height=station.height,
            latitude=station.latitude,
            longitude=station.longitude,
            active_from=station.active_from.isoformat() if station.active_from else None,
            active_to=station.active_to.isoformat() if station.active_to else None,
        )
