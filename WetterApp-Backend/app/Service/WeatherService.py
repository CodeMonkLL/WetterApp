from datetime import date, datetime

from app.Model.Dtos import DailyMeasurementDto, PagedResultDto, StationDto, StationOverviewDto
from app.Repository.DailyMeasurementRepository import DailyMeasurementRepository
from app.Repository.StationRepository import StationRepository


class WeatherService:
    @staticmethod
    def search_stations(
        name: str | None = None,
        state: str | None = None,
        date_from: date | str | None = None,
        date_to: date | str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> PagedResultDto[StationDto]:
        """Sucht Stationen nach Namensteil, Bundesland und Messzeitraum.

        Datumsangaben werden auch als ISO-String ("2015-01-01") akzeptiert.

        Raises:
            ValueError: Bei ungültigem Datumsformat oder verdrehten Grenzen.
        """
        date_from = _as_date(date_from, "date_from")
        date_to = _as_date(date_to, "date_to")
        _check_range(date_from, date_to)

        stations = StationRepository.search(name, state, date_from, date_to, limit, offset)
        total = StationRepository.count(name, state, date_from, date_to)
        return PagedResultDto(
            items=[StationDto.from_entity(station) for station in stations],
            total=total,
            limit=limit,
            offset=offset,
        )

    @staticmethod
    def get_station(station_id: str) -> StationDto | None:
        station = StationRepository.get(station_id)
        return StationDto.from_entity(station) if station else None

    @staticmethod
    def list_states() -> list[str]:
        return StationRepository.list_states()

    @staticmethod
    def search_measurements(
        station_id: str | None = None,
        station_name: str | None = None,
        state: str | None = None,
        date_from: date | str | None = None,
        date_to: date | str | None = None,
        newest_first: bool = True,
        limit: int = 100,
        offset: int = 0,
    ) -> PagedResultDto[DailyMeasurementDto]:
        """Sucht Tageswerte nach Station und Zeitraum.

        Raises:
            ValueError: Bei ungültigem Datumsformat oder verdrehten Grenzen.
        """
        date_from = _as_date(date_from, "date_from")
        date_to = _as_date(date_to, "date_to")
        _check_range(date_from, date_to)

        measurements = DailyMeasurementRepository.search(
            station_id, station_name, state, date_from, date_to, newest_first, limit, offset
        )
        total = DailyMeasurementRepository.count(station_id, station_name, state, date_from, date_to)
        return PagedResultDto(
            items=[DailyMeasurementDto.from_entity(m) for m in measurements],
            total=total,
            limit=limit,
            offset=offset,
        )

    @staticmethod
    def get_station_overview(station_id: str) -> StationOverviewDto | None:
        """Fasst Stammdaten, verfügbaren Zeitraum und jüngsten Messwert zusammen."""
        station = StationRepository.get(station_id)
        if not station:
            return None

        first, last = DailyMeasurementRepository.available_range(station_id)
        latest = DailyMeasurementRepository.latest(station_id)
        return StationOverviewDto(
            station=StationDto.from_entity(station),
            data_from=first.isoformat() if first else None,
            data_to=last.isoformat() if last else None,
            latest=DailyMeasurementDto.from_entity(latest) if latest else None,
        )


def _as_date(value: date | str | None, field: str) -> date | None:
    if value is None or isinstance(value, date):
        return value
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError(f"{field} muss im Format YYYY-MM-DD vorliegen, war: {value!r}") from None


def _check_range(date_from: date | None, date_to: date | None) -> None:
    if date_from and date_to and date_from > date_to:
        raise ValueError("date_from darf nicht nach date_to liegen.")
