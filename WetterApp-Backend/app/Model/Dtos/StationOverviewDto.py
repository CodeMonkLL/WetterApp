from dataclasses import dataclass

from app.Model.Dtos.DailyMeasurementDto import DailyMeasurementDto
from app.Model.Dtos.StationDto import StationDto


@dataclass(frozen=True)
class StationOverviewDto:
    """Stammdaten einer Station samt tatsächlich vorhandenem Datenbestand."""

    station: StationDto
    data_from: str | None
    data_to: str | None
    latest: DailyMeasurementDto | None
