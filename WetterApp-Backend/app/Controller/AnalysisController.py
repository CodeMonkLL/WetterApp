from dataclasses import asdict

from flask import Blueprint, jsonify, request

from app.Controller.QueryArgs import float_arg, int_arg
from app.Service.LocationAnalysisService import DEFAULT_STATIONS, LocationAnalysisService

analysis_bp = Blueprint('analysis', __name__)


@analysis_bp.route('/api/analysis/location', methods=['GET'])
def analyse_location():
    """Wertet einen beliebigen Ort in Deutschland aus den umliegenden Stationen aus.

    Der Ort wird über `address` (Geocoding via OpenStreetMap) oder direkt über
    `lat`/`lon` angegeben. Gesucht werden die nächsten Stationen im Radius, die
    im Zeitraum Messwerte haben. Pro Tag wird jede Messgröße per Inverse
    Distance Weighting (Gewicht 1/d²) gemittelt, anschließend auf Monat oder
    Jahr verdichtet: Temperatur, Wind und Feuchte als Mittel, Niederschlag und
    Sonnenschein als Summe.
    ---
    tags:
      - Auswertung
    parameters:
      - name: address
        in: query
        type: string
        required: false
        description: Adresse in Deutschland, z.B. "Domkloster 4, Köln". Alternativ lat/lon.
      - name: lat
        in: query
        type: number
        required: false
        description: Breitengrad, wenn keine Adresse angegeben ist.
      - name: lon
        in: query
        type: number
        required: false
        description: Längengrad, wenn keine Adresse angegeben ist.
      - name: date_from
        in: query
        type: string
        format: date
        required: true
        description: Beginn des Zeitraums, einschließlich (YYYY-MM-DD).
      - name: date_to
        in: query
        type: string
        format: date
        required: true
        description: Ende des Zeitraums, einschließlich (YYYY-MM-DD).
      - name: resolution
        in: query
        type: string
        enum: [day, month, year]
        default: month
        required: false
        description: Zeitliche Auflösung des Ergebnisses.
      - name: stations
        in: query
        type: integer
        default: 5
        required: false
        description: Maximale Anzahl einbezogener Stationen (1-10).
      - name: radius_km
        in: query
        type: number
        default: 50
        required: false
        description: Suchradius um den Ort in km (max. 200).
      - name: height
        in: query
        type: number
        required: false
        description: Höhe des Ortes in m über NN. Wenn gesetzt, werden Temperaturen mit 0,65 K/100 m auf diese Höhe umgerechnet.
    responses:
      200:
        description: Koordinaten, einbezogene Stationen mit Gewicht und die Zeitreihe.
      400:
        description: Ungültige Eingabe, Adresse nicht gefunden oder keine Station in Reichweite.
      502:
        description: Geocoding-Dienst nicht erreichbar.
    """
    result = LocationAnalysisService.analyse(
        address=request.args.get('address'),
        latitude=float_arg('lat'),
        longitude=float_arg('lon'),
        date_from=request.args.get('date_from'),
        date_to=request.args.get('date_to'),
        resolution=request.args.get('resolution', 'month'),
        max_stations=int_arg('stations', DEFAULT_STATIONS),
        radius_km=float_arg('radius_km'),
        target_height=float_arg('height'),
    )
    return jsonify(asdict(result)), 200
