from dataclasses import dataclass


@dataclass(frozen=True)
class NeighborStationDto:
    station_id: str
    name: str
    state: str | None
    height: int | None
    latitude: float
    longitude: float
    distance_km: float
    weight: float  # Anteil am Mittel, wenn an dem Tag alle Stationen einen Wert liefern


@dataclass(frozen=True)
class AnalysisPeriodDto:
    """Interpolierte Werte für einen Tag, Monat oder ein Jahr.

    `days` zählt die Tage mit mindestens einem Messwert. Summen (`rsk`, `sdk`)
    beziehen sich nur auf diese Tage.
    """

    period: str  # "YYYY-MM-DD", "YYYY-MM" oder "YYYY"
    days: int

    tmk: float | None  # Mittel der Tagesmittel (°C)
    txk: float | None  # Mittel der Tagesmaxima (°C)
    tnk: float | None  # Mittel der Tagesminima (°C)
    fm: float | None   # Mittlere Windgeschwindigkeit (m/s)
    upm: float | None  # Mittlere relative Feuchte (%)
    rsk: float | None  # Niederschlagssumme (mm)
    sdk: float | None  # Sonnenscheinsumme (Stunden)


@dataclass(frozen=True)
class LocationAnalysisDto:
    address: str | None
    display_name: str | None
    latitude: float
    longitude: float
    target_height: float | None
    date_from: str
    date_to: str
    resolution: str
    stations: list[NeighborStationDto]
    series: list[AnalysisPeriodDto]


@dataclass(frozen=True)
class StationAnalysisDto:
    """Verdichtete Werte einer einzelnen Station. Ohne Messwerte sind die Datumsangaben null."""

    station_id: str
    date_from: str | None
    date_to: str | None
    resolution: str
    series: list[AnalysisPeriodDto]
