from app.Service import LocationAnalysisService as service_module
from app.Service.GeocodingService import GeocodingError

ANALYSIS_URL = "/api/analysis/location"
PERIOD = {"date_from": "2020-01-01", "date_to": "2020-12-31"}


def test_health(client):
    assert client.get("/api/health").status_code == 200


def test_location_analysis(seeded, client):
    response = client.get(ANALYSIS_URL, query_string={"lat": 50.0, "lon": 7.0, "resolution": "day", **PERIOD})

    assert response.status_code == 200
    body = response.get_json()
    assert [s["station_id"] for s in body["stations"]] == ["A", "B"]
    assert body["series"][0]["tmk"] == 12.0


def test_location_analysis_requires_period(seeded, client):
    response = client.get(ANALYSIS_URL, query_string={"lat": 50.0, "lon": 7.0})

    assert response.status_code == 400
    assert "date_from" in response.get_json()["error"]


def test_location_analysis_rejects_non_numeric_coordinates(seeded, client):
    response = client.get(ANALYSIS_URL, query_string={"lat": "abc", "lon": 7.0, **PERIOD})

    assert response.status_code == 400


def test_geocoding_outage_is_bad_gateway(seeded, client, monkeypatch):
    def fail(address):
        raise GeocodingError("Dienst nicht erreichbar")

    monkeypatch.setattr(service_module, "geocode", fail)

    response = client.get(ANALYSIS_URL, query_string={"address": "Köln", **PERIOD})

    assert response.status_code == 502


def test_station_analysis(seeded, client):
    response = client.get("/api/stations/A/analysis", query_string={"resolution": "year"})

    assert response.status_code == 200
    body = response.get_json()
    assert [p["period"] for p in body["series"]] == ["2020"]


def test_station_analysis_unknown_station(seeded, client):
    assert client.get("/api/stations/XYZ/analysis").status_code == 404


def test_station_analysis_invalid_resolution(seeded, client):
    assert client.get("/api/stations/A/analysis", query_string={"resolution": "week"}).status_code == 400
