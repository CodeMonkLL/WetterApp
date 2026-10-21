from datetime import date

import pandas as pd
import pytest

from app.Service.LocationAnalysisService import (
    MIN_DISTANCE_KM,
    _aggregate,
    _haversine_km,
    _idw_weight,
    _resolve_location,
)


def test_haversine_koeln_bonn():
    assert _haversine_km(50.94, 6.96, 50.73, 7.10) == pytest.approx(25.3, abs=0.1)


def test_haversine_same_point_is_zero():
    assert _haversine_km(50.0, 7.0, 50.0, 7.0) == 0


def test_idw_weight_halves_distance_quadruples_weight():
    assert _idw_weight(10.0) / _idw_weight(20.0) == pytest.approx(4.0)


def test_idw_weight_is_finite_at_zero_distance():
    assert _idw_weight(0.0) == _idw_weight(MIN_DISTANCE_KM)


def _daily(rows: dict[date, dict]) -> pd.DataFrame:
    columns = ["tmk", "txk", "tnk", "fm", "upm", "rsk", "sdk"]
    return pd.DataFrame.from_dict(rows, orient="index", columns=columns, dtype=float)


def test_aggregate_month_means_and_sums():
    daily = _daily({
        date(2020, 1, 1): {"tmk": 10, "txk": 12, "tnk": 8, "fm": 2, "upm": 80, "rsk": 1.5, "sdk": 3},
        date(2020, 1, 2): {"tmk": 20, "txk": 22, "tnk": 18, "fm": 4, "upm": 90, "rsk": 2.5, "sdk": 5},
        date(2020, 2, 1): {"tmk": 0, "txk": 1, "tnk": -1, "fm": 1, "upm": 70, "rsk": 0, "sdk": 1},
    })

    january, february = _aggregate(daily, "month")

    assert january.period == "2020-01"
    assert january.days == 2
    assert january.tmk == 15.0
    assert january.fm == 3.0
    assert january.rsk == 4.0
    assert january.sdk == 8.0
    assert february.period == "2020-02"
    assert february.days == 1


def test_aggregate_year_and_day_period_format():
    daily = _daily({
        date(2019, 12, 31): {"tmk": 1},
        date(2020, 1, 1): {"tmk": 2},
    })

    assert [p.period for p in _aggregate(daily, "year")] == ["2019", "2020"]
    assert [p.period for p in _aggregate(daily, "day")] == ["2019-12-31", "2020-01-01"]


def test_aggregate_sum_without_values_is_none_not_zero():
    daily = _daily({date(2020, 1, 1): {"tmk": 5, "rsk": None}})

    (period,) = _aggregate(daily, "month")

    assert period.rsk is None
    assert period.tmk == 5.0


def test_aggregate_counts_only_days_with_values():
    daily = _daily({
        date(2020, 1, 1): {"tmk": 5},
        date(2020, 1, 2): {},
    })

    (period,) = _aggregate(daily, "month")

    assert period.days == 1


def test_aggregate_empty():
    assert _aggregate(_daily({}), "month") == []


def test_resolve_location_with_coordinates():
    location = _resolve_location(None, 50.0, 7.0)

    assert (location.latitude, location.longitude, location.display_name) == (50.0, 7.0, None)


@pytest.mark.parametrize(
    "address, lat, lon",
    [
        (None, None, None),
        ("   ", 50.0, None),
        (None, 91.0, 7.0),
        (None, 50.0, float("nan")),
        ("x" * 201, None, None),
    ],
)
def test_resolve_location_rejects_invalid_input(address, lat, lon):
    with pytest.raises(ValueError):
        _resolve_location(address, lat, lon)
