from datetime import date

from app.Service.download_data import find_station_ids, find_zip_name, parse_station_metadata

STATION_DESCRIPTION = """\
Stations_id von_datum bis_datum Stationshoehe geoBreite geoLaenge Stationsname Bundesland Abgabe
----------- --------- --------- ------------- --------- --------- ----------------------------------------- ---------- ------
00003 18910101 20110331            202     50.7827    6.0941 Aachen                                   Nordrhein-Westfalen                      Frei
00044 19690101 20241231             44     52.9336    8.2370 Großenkneten                             Niedersachsen                            Frei
02988 19470101 20241231            580     48.7810    8.6260 Liebenzell, Bad/ Nagold                  Baden-Württemberg                        Frei
kaputte Zeile
"""

LISTING = """
<a href="tageswerte_KL_00003_18910101_20110331_hist.zip">tageswerte_KL_00003_18910101_20110331_hist.zip</a>
<a href="tageswerte_KL_00044_19690101_20241231_hist.zip">tageswerte_KL_00044_19690101_20241231_hist.zip</a>
<a href="KL_Tageswerte_Beschreibung_Stationen.txt">KL_Tageswerte_Beschreibung_Stationen.txt</a>
"""


def test_parse_station_metadata():
    aachen, grossenkneten, liebenzell = parse_station_metadata(STATION_DESCRIPTION)

    assert aachen == {
        "station_id": "00003",
        "name": "Aachen",
        "state": "Nordrhein-Westfalen",
        "height": 202,
        "latitude": 50.7827,
        "longitude": 6.0941,
        "active_from": date(1891, 1, 1),
        "active_to": date(2011, 3, 31),
    }
    assert grossenkneten["name"] == "Großenkneten"


def test_parse_station_metadata_keeps_names_with_spaces_and_commas():
    *_, liebenzell = parse_station_metadata(STATION_DESCRIPTION)

    assert liebenzell["name"] == "Liebenzell, Bad/ Nagold"
    assert liebenzell["state"] == "Baden-Württemberg"


def test_find_station_ids_without_duplicates():
    assert find_station_ids(LISTING) == ["00003", "00044"]


def test_find_zip_name():
    assert find_zip_name(LISTING, "00044") == "tageswerte_KL_00044_19690101_20241231_hist.zip"
    assert find_zip_name(LISTING, "99999") is None
