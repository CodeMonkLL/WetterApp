import math
from datetime import date
from typing import NamedTuple

import pandas as pd

from app.Model.Dtos import AnalysisPeriodDto, LocationAnalysisDto, NeighborStationDto, StationAnalysisDto
from app.Model.Station import Station
from app.Repository.DailyMeasurementRepository import DailyMeasurementRepository
from app.Repository.StationRepository import StationRepository
from app.Service.GeocodingService import GeocodingError, GeoLocation, geocode, reverse_geocode
from app.Service.WeatherService import _as_date, _check_range

EARTH_RADIUS_KM = 6371.0
# Temperaturabnahme der Standardatmosphäre pro Meter Höhe.
LAPSE_RATE_K_PER_M = 0.0065
IDW_POWER = 2
# Verhindert Division durch null, wenn die Adresse direkt an einer Station liegt.
MIN_DISTANCE_KM = 0.1

DEFAULT_STATIONS = 5
MAX_STATIONS = 10
DEFAULT_RADIUS_KM = 50.0
MAX_RADIUS_KM = 200.0
MAX_ADDRESS_LENGTH = 200
MIN_HEIGHT_M = -100
MAX_HEIGHT_M = 3000

TEMPERATURE_COLUMNS = ["tmk", "txk", "tnk"]
MEAN_COLUMNS = TEMPERATURE_COLUMNS + ["fm", "upm"]
SUM_COLUMNS = ["rsk", "sdk"]
VALUE_COLUMNS = MEAN_COLUMNS + SUM_COLUMNS
RESOLUTION_FORMATS = {"day": "%Y-%m-%d", "month": "%Y-%m", "year": "%Y"}


class _Neighbor(NamedTuple):
    station: Station
    distance_km: float


class LocationAnalysisService:
    @staticmethod
    def analyse(
        address: str | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
        date_from: date | str | None = None,
        date_to: date | str | None = None,
        resolution: str = "month",
        max_stations: int = DEFAULT_STATIONS,
        radius_km: float | None = None,
        target_height: float | None = None,
    ) -> LocationAnalysisDto:
        """Wertet einen beliebigen Ort aus den umliegenden Stationen aus.

        Pro Tag wird jede Messgröße per Inverse Distance Weighting gemittelt.
        Fehlt einer Station an einem Tag ein Wert, verteilen sich die Gewichte
        auf die übrigen. Mit `target_height` werden Temperaturen auf die Höhe
        des Ortes umgerechnet. Danach wird auf Monat oder Jahr verdichtet.

        Raises:
            ValueError: Bei ungültiger Eingabe oder wenn keine Station in Reichweite ist.
            GeocodingError: Wenn der Geocoding-Dienst nicht erreichbar ist.
        """
        date_from = _as_date(date_from, "date_from")
        date_to = _as_date(date_to, "date_to")
        if not date_from or not date_to:
            raise ValueError("date_from und date_to sind Pflichtangaben.")
        _check_range(date_from, date_to)
        _check_resolution(resolution)
        if not 1 <= max_stations <= MAX_STATIONS:
            raise ValueError(f"stations muss zwischen 1 und {MAX_STATIONS} liegen.")
        radius_km = DEFAULT_RADIUS_KM if radius_km is None else radius_km
        if not 0 < radius_km <= MAX_RADIUS_KM:
            raise ValueError(f"radius_km muss größer 0 und höchstens {MAX_RADIUS_KM} sein.")
        if target_height is not None and not MIN_HEIGHT_M <= target_height <= MAX_HEIGHT_M:
            raise ValueError(f"height muss zwischen {MIN_HEIGHT_M} und {MAX_HEIGHT_M} m liegen.")

        location = _resolve_location(address, latitude, longitude)
        neighbors = _find_neighbors(location, date_from, date_to, max_stations, radius_km)
        if not neighbors:
            raise ValueError(f"Keine Station mit Messwerten im Umkreis von {radius_km:g} km gefunden.")

        weights = {n.station.station_id: _idw_weight(n.distance_km) for n in neighbors}
        daily = _interpolate_daily(neighbors, weights, date_from, date_to, target_height)
        total_weight = sum(weights.values())

        return LocationAnalysisDto(
            address=address,
            display_name=location.display_name,
            latitude=location.latitude,
            longitude=location.longitude,
            target_height=target_height,
            date_from=date_from.isoformat(),
            date_to=date_to.isoformat(),
            resolution=resolution,
            stations=[
                NeighborStationDto(
                    station_id=n.station.station_id,
                    name=n.station.name,
                    state=n.station.state,
                    height=n.station.height,
                    latitude=n.station.latitude,
                    longitude=n.station.longitude,
                    distance_km=round(n.distance_km, 1),
                    weight=round(weights[n.station.station_id] / total_weight, 3),
                )
                for n in neighbors
            ],
            series=_aggregate(daily, resolution),
        )

    @staticmethod
    def analyse_station(
        station_id: str,
        date_from: date | str | None = None,
        date_to: date | str | None = None,
        resolution: str = "month",
    ) -> StationAnalysisDto | None:
        """Verdichtet die Tageswerte einer Station wie `analyse`, nur ohne Interpolation.

        Fehlende Datumsgrenzen werden mit dem importierten Bestand aufgefüllt.

        Returns:
            None, wenn die Station nicht existiert.

        Raises:
            ValueError: Bei ungültigem Datum oder ungültiger Auflösung.
        """
        date_from = _as_date(date_from, "date_from")
        date_to = _as_date(date_to, "date_to")
        _check_range(date_from, date_to)
        _check_resolution(resolution)
        if StationRepository.get(station_id) is None:
            return None

        if not date_from or not date_to:
            first, last = DailyMeasurementRepository.available_range(station_id)
            date_from = date_from or first
            date_to = date_to or last

        series = []
        if date_from and date_to and date_from <= date_to:
            daily = _interpolate_daily([], {station_id: 1.0}, date_from, date_to, None)
            series = _aggregate(daily, resolution)

        return StationAnalysisDto(
            station_id=station_id,
            date_from=date_from.isoformat() if date_from else None,
            date_to=date_to.isoformat() if date_to else None,
            resolution=resolution,
            series=series,
        )


def _resolve_location(address: str | None, latitude: float | None, longitude: float | None) -> GeoLocation:
    address = (address or "").strip()
    if address:
        if len(address) > MAX_ADDRESS_LENGTH:
            raise ValueError(f"address darf höchstens {MAX_ADDRESS_LENGTH} Zeichen lang sein.")
        return geocode(address)
    if latitude is None or longitude is None:
        raise ValueError("Entweder address oder lat und lon angeben.")
    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        raise ValueError("lat/lon liegen außerhalb des gültigen Bereichs.")
    try:
        place = reverse_geocode(latitude, longitude)
    except GeocodingError:
        # Der Ortsname ist nur Beiwerk, die Auswertung klappt auch ohne.
        place = None
    return GeoLocation(latitude, longitude, place)


def _find_neighbors(
    location: GeoLocation, date_from: date, date_to: date, max_stations: int, radius_km: float
) -> list[_Neighbor]:
    """Liefert die nächsten Stationen im Radius, die im Zeitraum wirklich Messwerte haben."""
    candidates = []
    for station in StationRepository.with_coordinates(date_from, date_to):
        distance = _haversine_km(location.latitude, location.longitude, station.latitude, station.longitude)
        if distance <= radius_km:
            candidates.append(_Neighbor(station, distance))
    if not candidates:
        return []

    candidates.sort(key=lambda n: n.distance_km)
    with_data = DailyMeasurementRepository.stations_with_data(
        [n.station.station_id for n in candidates], date_from, date_to
    )
    return [n for n in candidates if n.station.station_id in with_data][:max_stations]


def _interpolate_daily(
    neighbors: list[_Neighbor],
    weights: dict[str, float],
    date_from: date,
    date_to: date,
    target_height: float | None,
) -> pd.DataFrame:
    """Berechnet pro Tag den gewichteten Mittelwert jeder Messgröße über alle Nachbarstationen."""
    rows = DailyMeasurementRepository.values_for_stations(list(weights), date_from, date_to, VALUE_COLUMNS)
    df = pd.DataFrame(rows, columns=["station_id", "date", *VALUE_COLUMNS])
    values = df[VALUE_COLUMNS].astype(float)

    if target_height is not None:
        heights = {n.station.station_id: n.station.height for n in neighbors}
        station_height = df["station_id"].map(heights).astype(float)
        # Stationen ohne Höhenangabe bleiben unkorrigiert.
        correction = ((station_height - target_height) * LAPSE_RATE_K_PER_M).fillna(0)
        values[TEMPERATURE_COLUMNS] = values[TEMPERATURE_COLUMNS].add(correction, axis=0)

    weight = df["station_id"].map(weights)
    numerator = values.mul(weight, axis=0).groupby(df["date"]).sum()
    denominator = values.notna().mul(weight, axis=0).groupby(df["date"]).sum()
    return numerator / denominator.where(denominator > 0)


def _aggregate(daily: pd.DataFrame, resolution: str) -> list[AnalysisPeriodDto]:
    if daily.empty:
        return []
    fmt = RESOLUTION_FORMATS[resolution]
    period = pd.Index([day.strftime(fmt) for day in daily.index], name="period")
    grouped = daily.groupby(period)

    table = grouped[MEAN_COLUMNS].mean().join(grouped[SUM_COLUMNS].sum(min_count=1))
    table["days"] = daily.notna().any(axis=1).groupby(period).sum()

    return [
        AnalysisPeriodDto(
            period=key,
            days=int(row["days"]),
            **{column: _round(row[column]) for column in VALUE_COLUMNS},
        )
        for key, row in table.to_dict("index").items()
    ]


def _idw_weight(distance_km: float) -> float:
    return 1 / max(distance_km, MIN_DISTANCE_KM) ** IDW_POWER


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = phi2 - phi1
    d_lambda = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def _round(value) -> float | None:
    return None if pd.isna(value) else round(float(value), 1)


def _check_resolution(resolution: str) -> None:
    if resolution not in RESOLUTION_FORMATS:
        raise ValueError(f"resolution muss eins von {list(RESOLUTION_FORMATS)} sein, war: {resolution!r}")
