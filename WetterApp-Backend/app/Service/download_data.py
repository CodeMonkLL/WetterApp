"""Import der historischen DWD-Tagesklimadaten (Datensatz "kl").

Ablauf des Gesamtimports:
    1. Verzeichnis-Listing des DWD-Open-Data-Servers laden.
    2. Stationsbeschreibung laden und Stammdaten (Name, Bundesland, Koordinaten)
       in die Tabelle `station` schreiben.
    3. Pro Station das ZIP herunterladen, die enthaltene CSV lesen und die
       Tageswerte per Upsert in die Tabelle `daily_measurement` schreiben.

Es wird nichts auf die Festplatte geschrieben: ZIP und CSV werden komplett im
Arbeitsspeicher verarbeitet.
"""

import io
import logging
import re
import threading
import zipfile
import concurrent.futures
from datetime import datetime
import pandas as pd
import requests
from flask import Flask, current_app
from requests.adapters import HTTPAdapter
from sqlalchemy.dialects.postgresql import insert
from urllib3.util.retry import Retry
from app.Model.Station import Station
from app.Model.DailyMesaurement import DailyMeasurement
from app.Repository.DbContext import dbcontext

logger = logging.getLogger(__name__)

BASE_URL = "https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/daily/kl/historical/"
STATIONS_URL = BASE_URL + "KL_Tageswerte_Beschreibung_Stationen.txt"
DEFAULT_WORKERS = 8
# Fehlwert des DWD, je nach Spalte als "-999" oder "-999.000" geschrieben.
MISSING_VALUE = -999
# Die Station-ID steckt im Dateinamen jedes historischen Tageswerte-Archivs.
STATION_ID_PATTERN = re.compile(r"tageswerte_KL_(\d+)_\d+_\d+_hist\.zip")
# Die ersten sechs Felder der Stationsbeschreibung enthalten keine Leerzeichen,
# Name und Bundesland dahinter schon - die werden separat getrennt.
STATION_LINE_PATTERN = re.compile(
    r"^(?P<station_id>\d+)\s+(?P<von>\d{8})\s+(?P<bis>\d{8})\s+"
    r"(?P<height>-?\d+)\s+(?P<lat>-?\d+\.\d+)\s+(?P<lon>-?\d+\.\d+)\s+(?P<rest>.+)$"
)
STATION_UPDATE_FIELDS = ("name", "state", "height", "latitude", "longitude", "active_from", "active_to")
# Ordnet die Spaltennamen der DWD-CSV den Spalten des Modells DailyMeasurement zu.
COLUMN_MAP = {
    "QN_3": "qn3", "FX": "fx", "FM": "fm", "QN_4": "qn4",
    "RSK": "rsk", "RSKF": "rskf", "SDK": "sdk", "SHK_TAG": "shk_tag",
    "NM": "nm", "VPM": "vpm", "PM": "pm", "TMK": "tmk",
    "UPM": "upm", "TXK": "txk", "TNK": "tnk", "TGK": "tgk",
}

def make_session(pool_size: int = DEFAULT_WORKERS) -> requests.Session:
    """Erzeugt eine HTTP-Session mit Wiederholungslogik für den DWD-Server.

    Fehlgeschlagene GET-Anfragen werden bis zu fünfmal wiederholt, mit wachsender
    Wartezeit (2s, 4s, 8s, 16s, 32s). Das fängt die Rate-Limits (429) und die
    zeitweiligen Serverfehler (5xx) ab, die bei vielen parallelen Downloads auftreten.

    Der Verbindungspool wird auf `pool_size` gesetzt, damit sich alle Threads
    bestehende Verbindungen teilen, statt für jeden Download eine neue zu öffnen.
    """
    session = requests.Session()
    retry = Retry(
        total=5,
        backoff_factor=2,  # 2s, 4s, 8s, 16s, 32s
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    adapter = HTTPAdapter(max_retries=retry, pool_connections=pool_size, pool_maxsize=pool_size)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session

def find_station_ids(listing_html: str) -> list[str]:
    """Liest alle Station-IDs aus dem HTML-Verzeichnis-Listing des DWD.

    Die IDs stammen aus den ZIP-Dateinamen, dadurch tauchen nur Stationen auf,
    für die es auch tatsächlich Daten gibt. Das Set entfernt Duplikate, weil
    jeder Dateiname im Listing zweimal vorkommt (Link-Ziel und Link-Text).
    """
    return sorted({match.group(1) for match in STATION_ID_PATTERN.finditer(listing_html)})


def parse_station_metadata(text: str) -> list[dict[str, object]]:
    """Zerlegt die Stationsbeschreibung des DWD in Datensätze.

    Die ersten beiden Zeilen sind Überschrift und Trennlinie und werden übersprungen.
    Name und Bundesland stehen in Blöcken fester Breite und sind deshalb immer durch
    mindestens zwei Leerzeichen getrennt - so bleiben Namen wie "Liebenzell, Bad/ Nagold"
    oder "Donaueschingen (Landeplatz)" unversehrt.
    """
    stations = []
    for line in text.splitlines()[2:]:
        match = STATION_LINE_PATTERN.match(line)
        if not match:
            continue

        parts = re.split(r"\s{2,}", match.group("rest").strip())
        stations.append({
            "station_id": match.group("station_id"),
            "name": parts[0],
            "state": parts[1] if len(parts) > 1 else None,
            "height": int(match.group("height")),
            "latitude": float(match.group("lat")),
            "longitude": float(match.group("lon")),
            "active_from": datetime.strptime(match.group("von"), "%Y%m%d").date(),
            "active_to": datetime.strptime(match.group("bis"), "%Y%m%d").date(),
        })
    return stations


def sync_stations(session: requests.Session) -> int:
    """Lädt die Stationsbeschreibung und schreibt die Stammdaten in `station`.

    Bestehende Stationen werden aktualisiert, neue angelegt. Die Funktion kann
    also beliebig oft aufgerufen werden und zieht dabei auch Namensänderungen nach.

    Returns:
        Anzahl der verarbeiteten Stationen.
    """
    text = session.get(STATIONS_URL, timeout=60).content.decode("latin-1")
    stations = parse_station_metadata(text)
    if not stations:
        return 0

    statement = insert(Station).values(stations)
    statement = statement.on_conflict_do_update(
        index_elements=["station_id"],
        set_={field: getattr(statement.excluded, field) for field in STATION_UPDATE_FIELDS},
    )
    dbcontext.session.execute(statement)
    dbcontext.session.commit()
    return len(stations)


def ensure_data_imported(app: Flask, workers: int = DEFAULT_WORKERS) -> bool:
    """Startet den Import beim Hochfahren, falls noch keine Messwerte da sind.

    Der Import läuft in einem Hintergrund-Thread, damit der Webserver sofort
    antwortet. Bei bereits gefüllter Datenbank passiert nichts, der Neustart
    löst also keinen erneuten Download aus.

    Returns:
        True, wenn ein Import angestoßen wurde.
    """
    if dbcontext.session.query(DailyMeasurement.id).first() is not None:
        return False

    def run() -> None:
        with app.app_context():
            try:
                results = import_all_stations(workers=workers)
                imported = sum(int(result["imported"]) for result in results)
                logger.info("Erstimport fertig: %s Stationen, %s Tageswerte.", len(results), imported)
            except Exception:
                logger.exception("Erstimport fehlgeschlagen.")
            finally:
                dbcontext.session.remove()

    logger.info("Datenbank ist leer, starte Erstimport im Hintergrund.")
    threading.Thread(target=run, daemon=True, name="dwd-initial-import").start()
    return True


def import_all_stations(workers: int = DEFAULT_WORKERS, limit: int | None = None) -> list[dict[str, int | str]]:
    """Führt den kompletten Import für alle Stationen durch.

    Das Verzeichnis-Listing ist für alle Stationen identisch und wird deshalb nur
    einmal geladen und an die Worker weitergereicht.

    Args:
        workers: Anzahl paralleler Downloads. Bei 1 läuft der Import seriell.
        limit: Optional nur die ersten N Stationen verarbeiten (zum Testen).

    Returns:
        Je Station ein Ergebnis-Dict mit `station_id`, `status`, `message` und
        `imported` (Anzahl geschriebener Tageswerte).
    """
    workers = max(1, workers)

    session = make_session(pool_size=workers)
    listing = session.get(BASE_URL, timeout=60).text

    sync_stations(session)

    # Nicht jede beschriebene Station hat ein historisches Archiv.
    available_ids = find_station_ids(listing)
    query = Station.query.filter(Station.station_id.in_(available_ids)).order_by(Station.station_id)
    if limit:
        query = query.limit(limit)
    station_ids = [station.station_id for station in query.all()]

    flask_app = current_app._get_current_object()

    # Threads erben den Flask-Kontext nicht, deshalb pro Thread ein eigener App-Kontext
    # und am Ende eine eigene DB-Session, die wieder freigegeben werden muss.
    def worker(station_id: str) -> dict[str, int | str]:
        with flask_app.app_context():
            try:
                return import_one_station(session, listing, station_id)
            except requests.exceptions.RequestException as exc:
                dbcontext.session.rollback()
                return {"station_id": station_id, "status": "download_failed", "message": str(exc), "imported": 0}
            except Exception as exc:
                dbcontext.session.rollback()
                return {"station_id": station_id, "status": "failed", "message": str(exc), "imported": 0}
            finally:
                dbcontext.session.remove()

    if workers == 1:
        return [worker(station_id) for station_id in station_ids]

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        return list(executor.map(worker, station_ids))


def import_one_station(session: requests.Session, listing_html: str, station_id: str) -> dict[str, int | str]:
    """Lädt die Tageswerte einer Station und schreibt sie in die Datenbank.

    Schritte: ZIP-Namen im Listing suchen, Archiv in den Speicher laden, die darin
    enthaltene Datei `produkt_klima_tag*` als CSV lesen, Spalten auf das Modell
    mappen und per Upsert speichern.

    Bestehende Werte zur gleichen Kombination aus Station und Datum werden
    aktualisiert statt doppelt eingefügt, der Import ist also wiederholbar.

    Returns:
        Ergebnis-Dict mit `station_id`, `status`, `message` und `imported`.
    """
    zip_name = find_zip_name(listing_html, station_id)
    if not zip_name:
        return {"station_id": station_id, "status": "not_found", "message": "Kein ZIP gefunden", "imported": 0}

    zip_bytes = session.get(BASE_URL + zip_name, timeout=120).content

    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as archive:
        produkt_file = next(name for name in archive.namelist() if name.startswith("produkt_klima_tag"))
        df = pd.read_csv(
            archive.open(produkt_file),
            sep=";",
            encoding="latin-1",
        )

    df.columns = [column.strip() for column in df.columns]
    # Nach dem Parsen maskieren, weil na_values nur exakte Textformen trifft und
    # Gleitkommaspalten "-999.000" statt "-999" enthalten.
    value_columns = [column for column in COLUMN_MAP if column in df.columns]
    df[value_columns] = df[value_columns].where(df[value_columns] != MISSING_VALUE)
    # Das DWD liefert das Datum als Zahl im Format YYYYMMDD.
    df["MESS_DATUM"] = pd.to_datetime(df["MESS_DATUM"], format="%Y%m%d").dt.date

    rows = []
    for _, row in df.iterrows():
        measurement = {
            "station_id": station_id,
            "date": row["MESS_DATUM"],
        }
        measurement.update(
            {db_column: None if pd.isna(row.get(csv_column)) else row.get(csv_column)
             for csv_column, db_column in COLUMN_MAP.items()
             if csv_column in row}
        )
        rows.append(measurement)

    if rows:
        statement = insert(DailyMeasurement).values(rows)
        update_columns = {column: getattr(statement.excluded, column) for column in COLUMN_MAP.values()}
        statement = statement.on_conflict_do_update(
            index_elements=["station_id", "date"],
            set_=update_columns,
        )
        dbcontext.session.execute(statement)
        dbcontext.session.commit()

    return {"station_id": station_id, "status": "imported", "message": zip_name, "imported": len(rows)}


def find_zip_name(listing_html: str, station_id: str) -> str | None:
    """Sucht den Dateinamen des Archivs einer Station im Verzeichnis-Listing.

    Die Jahreszahlen im Dateinamen unterscheiden sich je Station und ändern sich
    mit jeder DWD-Aktualisierung, deshalb die Suche per Muster.

    Returns:
        Den Dateinamen oder None, wenn es für die Station kein Archiv gibt.
    """
    match = re.search(rf"tageswerte_KL_{station_id}_\d+_\d+_hist\.zip", listing_html)
    return match.group(0) if match else None
 
 