from datetime import date

import pytest

from app import create_app
from app.Model.DailyMesaurement import DailyMeasurement
from app.Model.Station import Station
from app.Repository.DbContext import dbcontext
from app.Service import LocationAnalysisService as service_module
from app.Service.GeocodingService import _reverse_geocode, geocode

# Bezugspunkt der Tests. 0,1° Breite entsprechen ca. 11,1 km.
ORIGIN = (50.0, 7.0)


@pytest.fixture
def flask_app(monkeypatch):
    """App mit leerer In-Memory-SQLite statt Postgres, ohne DWD-Import."""
    monkeypatch.setenv("DATABASE_URL", "sqlite://")
    monkeypatch.setenv("AUTO_IMPORT", "0")
    app = create_app()
    app.config["TESTING"] = True
    with app.app_context():
        yield app
        dbcontext.session.remove()
        dbcontext.drop_all()


@pytest.fixture
def client(flask_app):
    return flask_app.test_client()


@pytest.fixture(autouse=True)
def clear_geocode_cache():
    geocode.cache_clear()
    _reverse_geocode.cache_clear()
    yield
    geocode.cache_clear()
    _reverse_geocode.cache_clear()


@pytest.fixture(autouse=True)
def offline_reverse_geocode(monkeypatch):
    """Auswertungen per lat/lon sollen in Tests nicht bei Nominatim anfragen."""
    monkeypatch.setattr(service_module, "reverse_geocode", lambda latitude, longitude: None)


@pytest.fixture
def seeded(flask_app):
    """Vier Stationen nördlich und südlich von ORIGIN.

    A: 11,1 km, 100 m, hat Daten
    B: 22,2 km, 500 m, hat Daten (doppelte Entfernung -> Viertel des Gewichts von A)
    C: 111 km, außerhalb des Standardradius
    D: 5,6 km, am nächsten, aber ohne Messwerte
    """
    lat, lon = ORIGIN
    stations = [
        _station("A", lat + 0.1, lon, 100),
        _station("B", lat - 0.2, lon, 500),
        _station("C", lat + 1.0, lon, 100),
        _station("D", lat + 0.05, lon, 100),
    ]
    measurements = [
        _measurement("A", date(2020, 1, 1), tmk=10.0, txk=12.0, tnk=8.0, rsk=1.0, sdk=2.0),
        _measurement("B", date(2020, 1, 1), tmk=20.0, txk=22.0, tnk=18.0, rsk=6.0, sdk=None),
        _measurement("A", date(2020, 1, 2), tmk=None, txk=None, tnk=None, rsk=None, sdk=None),
        _measurement("B", date(2020, 1, 2), tmk=6.0, txk=7.0, tnk=5.0, rsk=0.0, sdk=4.0),
        _measurement("A", date(2020, 2, 1), tmk=0.0, txk=1.0, tnk=-1.0, rsk=2.0, sdk=1.0),
        _measurement("C", date(2020, 1, 1), tmk=-50.0, txk=-50.0, tnk=-50.0, rsk=99.0, sdk=0.0),
    ]
    dbcontext.session.add_all(stations + measurements)
    dbcontext.session.commit()
    return flask_app


def _station(station_id: str, latitude: float, longitude: float, height: int) -> Station:
    return Station(
        station_id=station_id,
        name=f"Station {station_id}",
        state="Testland",
        height=height,
        latitude=latitude,
        longitude=longitude,
        active_from=date(1990, 1, 1),
        active_to=date(2030, 12, 31),
    )


def _measurement(station_id: str, day: date, **values) -> DailyMeasurement:
    return DailyMeasurement(station_id=station_id, date=day, fm=3.0, upm=80.0, **values)
