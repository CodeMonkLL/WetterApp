from dataclasses import asdict

from flask import Blueprint, jsonify, request

from app.Controller.QueryArgs import int_arg
from app.Service.WeatherService import WeatherService

measurement_bp = Blueprint('measurements', __name__)


@measurement_bp.route('/api/measurements', methods=['GET'])
def search_measurements():
    """Sucht Tageswerte nach Station und Zeitraum.

    Die Station lässt sich entweder exakt über `station_id` oder unscharf über
    `station_name` eingrenzen. Alle Filter sind optional und kombinierbar.
    Fehlende Messwerte stehen im DWD-Rohdatensatz als -999 und werden als null
    ausgeliefert.
    ---
    tags:
      - Messwerte
    parameters:
      - name: station_id
        in: query
        type: string
        required: false
        description: DWD-Station-ID, exakter Treffer, z.B. "00003".
      - name: station_name
        in: query
        type: string
        required: false
        description: Teil des Stationsnamens, z.B. "aachen".
      - name: state
        in: query
        type: string
        required: false
        description: Bundesland der Station, exakter Treffer.
      - name: date_from
        in: query
        type: string
        format: date
        required: false
        description: Frühestes Messdatum, einschließlich (YYYY-MM-DD).
      - name: date_to
        in: query
        type: string
        format: date
        required: false
        description: Spätestes Messdatum, einschließlich (YYYY-MM-DD).
      - name: order
        in: query
        type: string
        enum: [desc, asc]
        default: desc
        required: false
        description: Sortierung nach Datum.
      - name: limit
        in: query
        type: integer
        required: false
        default: 100
        description: Maximale Trefferzahl, maximal 5000.
      - name: offset
        in: query
        type: integer
        required: false
        default: 0
        description: Versatz zum Blättern.
    responses:
      200:
        description: Seitenweise Liste der Tageswerte.
      400:
        description: Ungültiges Datumsformat oder ungültige Zahl.
    """
    result = WeatherService.search_measurements(
        station_id=request.args.get('station_id'),
        station_name=request.args.get('station_name'),
        state=request.args.get('state'),
        date_from=request.args.get('date_from'),
        date_to=request.args.get('date_to'),
        newest_first=request.args.get('order', 'desc') != 'asc',
        limit=int_arg('limit', 100),
        offset=int_arg('offset', 0),
    )
    return jsonify(asdict(result)), 200
