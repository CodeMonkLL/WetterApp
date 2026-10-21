import pytest
import requests

from app.Service import GeocodingService
from app.Service.GeocodingService import GeocodingError, geocode, reverse_geocode


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")

    def json(self):
        return self._payload


def test_geocode_returns_first_hit(monkeypatch):
    calls = []

    def fake_get(url, params, headers, timeout):
        calls.append(params)
        return FakeResponse([{"lat": "50.9413", "lon": "6.9583", "display_name": "Kölner Dom"}])

    monkeypatch.setattr(GeocodingService.requests, "get", fake_get)

    location = geocode("Domkloster 4, Köln")

    assert (location.latitude, location.longitude) == (50.9413, 6.9583)
    assert location.display_name == "Kölner Dom"
    assert calls[0]["countrycodes"] == "de"


def test_geocode_caches_repeated_addresses(monkeypatch):
    calls = []

    def fake_get(url, params, headers, timeout):
        calls.append(params)
        return FakeResponse([{"lat": "50", "lon": "7"}])

    monkeypatch.setattr(GeocodingService.requests, "get", fake_get)

    geocode("Bonn")
    geocode("Bonn")

    assert len(calls) == 1


def test_geocode_unknown_address(monkeypatch):
    monkeypatch.setattr(GeocodingService.requests, "get", lambda *args, **kwargs: FakeResponse([]))

    with pytest.raises(ValueError, match="nicht gefunden"):
        geocode("Gibtsnicht 999")


@pytest.mark.parametrize(
    "fake_get",
    [
        lambda *args, **kwargs: FakeResponse([], status_code=503),
        lambda *args, **kwargs: (_ for _ in ()).throw(requests.ConnectionError("offline")),
    ],
)
def test_geocode_service_failure(monkeypatch, fake_get):
    monkeypatch.setattr(GeocodingService.requests, "get", fake_get)

    with pytest.raises(GeocodingError):
        geocode("Köln")


@pytest.mark.parametrize(
    "address, expected",
    [
        ({"village": "Bollstedt", "county": "Unstrut-Hainich-Kreis", "state": "Thüringen"},
         "Bollstedt, Unstrut-Hainich-Kreis"),
        # Kreisfreie Städte haben keinen Landkreis.
        ({"suburb": "Ehrenfeld", "city": "Köln", "state": "Nordrhein-Westfalen"}, "Köln, Nordrhein-Westfalen"),
        ({"city": "Berlin", "state": "Berlin"}, "Berlin"),
        ({"hamlet": "Hof", "village": "Dorf", "county": "Kreis"}, "Hof, Kreis"),
    ],
)
def test_reverse_geocode_names_nearest_place(monkeypatch, address, expected):
    calls = []

    def fake_get(url, params, headers, timeout):
        calls.append(params)
        return FakeResponse({"address": address, "display_name": "lang"})

    monkeypatch.setattr(GeocodingService.requests, "get", fake_get)

    assert reverse_geocode(51.2, 10.4) == expected
    assert (calls[0]["lat"], calls[0]["lon"]) == (51.2, 10.4)


def test_reverse_geocode_without_locality_uses_display_name(monkeypatch):
    payload = {"address": {"state": "Bayern"}, "display_name": "Nationalpark, Bayern"}
    monkeypatch.setattr(GeocodingService.requests, "get", lambda *args, **kwargs: FakeResponse(payload))

    assert reverse_geocode(48.9, 13.4) == "Nationalpark, Bayern"


def test_reverse_geocode_nothing_found(monkeypatch):
    payload = {"error": "Unable to geocode"}
    monkeypatch.setattr(GeocodingService.requests, "get", lambda *args, **kwargs: FakeResponse(payload))

    assert reverse_geocode(54.5, 5.0) is None


def test_reverse_geocode_caches_nearby_clicks(monkeypatch):
    calls = []

    def fake_get(url, params, headers, timeout):
        calls.append(params)
        return FakeResponse({"address": {"town": "Ort"}})

    monkeypatch.setattr(GeocodingService.requests, "get", fake_get)

    reverse_geocode(51.20001, 10.40001)
    reverse_geocode(51.20004, 10.40004)

    assert len(calls) == 1


def test_reverse_geocode_service_failure(monkeypatch):
    monkeypatch.setattr(GeocodingService.requests, "get", lambda *args, **kwargs: FakeResponse({}, status_code=503))

    with pytest.raises(GeocodingError):
        reverse_geocode(51.2, 10.4)
