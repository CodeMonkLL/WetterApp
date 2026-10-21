import pytest

from app.Service import LocationAnalysisService as service_module
from app.Service.GeocodingService import GeocodingError, GeoLocation
from app.Service.LocationAnalysisService import LocationAnalysisService

from .conftest import ORIGIN

LAT, LON = ORIGIN


def analyse(**overrides):
    params = {
        "latitude": LAT,
        "longitude": LON,
        "date_from": "2020-01-01",
        "date_to": "2020-12-31",
        "resolution": "day",
    }
    params.update(overrides)
    return LocationAnalysisService.analyse(**params)


def test_uses_nearest_stations_with_data_only(seeded):
    result = analyse()

    # D ist am nächsten, hat aber keine Messwerte. C liegt außerhalb des Radius.
    assert [s.station_id for s in result.stations] == ["A", "B"]
    assert result.stations[0].distance_km == pytest.approx(11.1, abs=0.1)


def test_weights_follow_inverse_square_distance(seeded):
    result = analyse()

    weights = {s.station_id: s.weight for s in result.stations}
    assert weights == {"A": 0.8, "B": 0.2}


def test_interpolated_temperature(seeded):
    first_day = analyse().series[0]

    # (4 * 10 + 1 * 20) / 5
    assert first_day.period == "2020-01-01"
    assert first_day.tmk == 12.0
    assert first_day.txk == 14.0
    assert first_day.tnk == 10.0


def test_missing_value_redistributes_weight(seeded):
    first_day, second_day, _ = analyse().series

    # Am 2.1. fehlt A, also zählt nur B.
    assert second_day.tmk == 6.0
    # Am 1.1. fehlt B die Sonnenscheindauer, also zählt nur A.
    assert first_day.sdk == 2.0


def test_height_correction(seeded):
    first_day = analyse(target_height=100).series[0]

    # B liegt 400 m höher, also +2,6 K: (4 * 10 + 1 * 22,6) / 5 = 12,52
    assert first_day.tmk == 12.5


def test_monthly_aggregation(seeded):
    january, february = analyse(resolution="month").series

    assert january.period == "2020-01"
    assert january.days == 2
    assert january.tmk == 9.0
    # Tagessummen 2,0 (= (4 * 1 + 1 * 6) / 5) und 0,0
    assert january.rsk == 2.0
    assert february.tmk == 0.0


def test_max_stations_limits_selection(seeded):
    result = analyse(max_stations=1)

    assert [s.station_id for s in result.stations] == ["A"]
    assert result.stations[0].weight == 1.0


def test_no_station_in_radius(seeded):
    with pytest.raises(ValueError, match="Keine Station"):
        analyse(radius_km=8)


def test_period_without_data_finds_no_station(seeded):
    with pytest.raises(ValueError, match="Keine Station"):
        analyse(date_from="2021-01-01", date_to="2021-12-31")


def test_address_is_geocoded(seeded, monkeypatch):
    monkeypatch.setattr(service_module, "geocode", lambda address: GeoLocation(LAT, LON, "Teststraße 1"))

    result = analyse(latitude=None, longitude=None, address="Teststraße 1")

    assert result.display_name == "Teststraße 1"
    assert [s.station_id for s in result.stations] == ["A", "B"]


def test_coordinates_get_nearest_place_name(seeded, monkeypatch):
    monkeypatch.setattr(service_module, "reverse_geocode", lambda latitude, longitude: "Testdorf, Testkreis")

    assert analyse().display_name == "Testdorf, Testkreis"


def test_reverse_geocoding_outage_does_not_break_analysis(seeded, monkeypatch):
    def fail(latitude, longitude):
        raise GeocodingError("Dienst nicht erreichbar")

    monkeypatch.setattr(service_module, "reverse_geocode", fail)

    result = analyse()

    assert result.display_name is None
    assert [s.station_id for s in result.stations] == ["A", "B"]


@pytest.mark.parametrize(
    "overrides",
    [
        {"date_from": None},
        {"date_to": None},
        {"date_from": "2020-12-31", "date_to": "2020-01-01"},
        {"date_from": "01.01.2020"},
        {"resolution": "week"},
        {"max_stations": 0},
        {"max_stations": 11},
        {"radius_km": 0},
        {"radius_km": 500},
        {"target_height": 9000},
    ],
)
def test_invalid_input(flask_app, overrides):
    with pytest.raises(ValueError):
        analyse(**overrides)


def test_station_analysis_defaults_to_available_range(seeded):
    result = LocationAnalysisService.analyse_station("A", resolution="month")

    assert (result.date_from, result.date_to) == ("2020-01-01", "2020-02-01")
    assert [p.period for p in result.series] == ["2020-01", "2020-02"]
    # Station A allein, ohne Interpolation
    assert result.series[0].tmk == 10.0


def test_station_analysis_unknown_station(seeded):
    assert LocationAnalysisService.analyse_station("XYZ") is None


def test_station_analysis_without_measurements(seeded):
    result = LocationAnalysisService.analyse_station("D")

    assert result.series == []
    assert result.date_from is None
