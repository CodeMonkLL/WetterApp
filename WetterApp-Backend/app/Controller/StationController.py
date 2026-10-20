from dataclasses import asdict

from flask import Blueprint, jsonify, request

from app.Controller.QueryArgs import int_arg
from app.Service.LocationAnalysisService import LocationAnalysisService
from app.Service.WeatherService import WeatherService

station_bp = Blueprint('stations', __name__)


@station_bp.route('/api/stations', methods=['GET'])
def search_stations():
    """Sucht Wetterstationen nach Name, Bundesland und Messzeitraum.

    Der Name wird als Teilstring verglichen, Groß- und Kleinschreibung spielt
    keine Rolle. Die Datumsgrenzen filtern über die Überlappung: gefunden wird
    jede Station, deren Messzeitraum den gesuchten Zeitraum schneidet.
    ---
    tags:
      - Stationen
    parameters:
      - name: name
        in: query
        type: string
        required: false
        description: Teil des Stationsnamens, z.B. "aachen".
      - name: state
        in: query
        type: string
        required: false
        description: Bundesland, exakter Treffer, z.B. "Nordrhein-Westfalen".
      - name: date_from
        in: query
        type: string
        format: date
        required: false
        description: Nur Stationen, die ab diesem Datum noch Werte liefern (YYYY-MM-DD).
      - name: date_to
        in: query
        type: string
        format: date
        required: false
        description: Nur Stationen, die bis zu diesem Datum schon Werte liefern (YYYY-MM-DD).
      - name: limit
        in: query
        type: integer
        required: false
        default: 50
        description: Maximale Trefferzahl.
      - name: offset
        in: query
        type: integer
        required: false
        default: 0
        description: Versatz zum Blättern.
    responses:
      200:
        description: Seitenweise Liste passender Stationen.
      400:
        description: Ungültiges Datumsformat oder ungültige Zahl.
    """
    result = WeatherService.search_stations(
        name=request.args.get('name'),
        state=request.args.get('state'),
        date_from=request.args.get('date_from'),
        date_to=request.args.get('date_to'),
        limit=int_arg('limit', 50),
        offset=int_arg('offset', 0),
    )
    return jsonify(asdict(result)), 200


@station_bp.route('/api/stations/<station_id>', methods=['GET'])
def get_station(station_id: str):
    """Liefert die Stammdaten einer einzelnen Station.
    ---
    tags:
      - Stationen
    parameters:
      - name: station_id
        in: path
        type: string
        required: true
        description: DWD-Station-ID, fünfstellig mit führenden Nullen, z.B. "00003".
    responses:
      200:
        description: Stammdaten der Station.
      404:
        description: Station existiert nicht.
    """
    station = WeatherService.get_station(station_id)
    if station is None:
        return jsonify({"error": f"Station {station_id} nicht gefunden."}), 404
    return jsonify(asdict(station)), 200


@station_bp.route('/api/stations/<station_id>/overview', methods=['GET'])
def get_station_overview(station_id: str):
    """Fasst Stammdaten, tatsächlich vorhandenen Datenbestand und jüngsten Messwert zusammen.

    Der Zeitraum aus den Stammdaten sagt, wann die Station laut DWD gemessen hat.
    `data_from` und `data_to` sagen, was davon wirklich importiert wurde.
    ---
    tags:
      - Stationen
    parameters:
      - name: station_id
        in: path
        type: string
        required: true
        description: DWD-Station-ID, z.B. "00003".
    responses:
      200:
        description: Station, Datenbestand und jüngster Messwert.
      404:
        description: Station existiert nicht.
    """
    overview = WeatherService.get_station_overview(station_id)
    if overview is None:
        return jsonify({"error": f"Station {station_id} nicht gefunden."}), 404
    return jsonify(asdict(overview)), 200


@station_bp.route('/api/stations/<station_id>/analysis', methods=['GET'])
def get_station_analysis(station_id: str):
    """Verdichtet die Tageswerte einer Station auf Tag, Monat oder Jahr.

    Gleiches Antwortformat wie die Zeitreihe von `/api/analysis/location`.
    Temperatur, Wind und Feuchte werden gemittelt, Niederschlag und
    Sonnenschein summiert. Ohne Datumsgrenzen wird der gesamte importierte
    Bestand ausgewertet.
    ---
    tags:
      - Stationen
    parameters:
      - name: station_id
        in: path
        type: string
        required: true
        description: DWD-Station-ID, z.B. "00003".
      - name: date_from
        in: query
        type: string
        format: date
        required: false
        description: Beginn des Zeitraums, einschließlich (YYYY-MM-DD).
      - name: date_to
        in: query
        type: string
        format: date
        required: false
        description: Ende des Zeitraums, einschließlich (YYYY-MM-DD).
      - name: resolution
        in: query
        type: string
        enum: [day, month, year]
        default: month
        required: false
        description: Zeitliche Auflösung.
    responses:
      200:
        description: Zeitreihe der Station.
      400:
        description: Ungültiges Datum oder ungültige Auflösung.
      404:
        description: Station existiert nicht.
    """
    analysis = LocationAnalysisService.analyse_station(
        station_id,
        date_from=request.args.get('date_from'),
        date_to=request.args.get('date_to'),
        resolution=request.args.get('resolution', 'month'),
    )
    if analysis is None:
        return jsonify({"error": f"Station {station_id} nicht gefunden."}), 404
    return jsonify(asdict(analysis)), 200


@station_bp.route('/api/states', methods=['GET'])
def list_states():
    """Liefert alle vorkommenden Bundesländer, z.B. für ein Filter-Dropdown.
    ---
    tags:
      - Stationen
    responses:
      200:
        description: Alphabetisch sortierte Liste der Bundesländer.
        schema:
          type: array
          items:
            type: string
          example: ["Baden-Württemberg", "Bayern"]
    """
    return jsonify(WeatherService.list_states()), 200
