from flask import Flask, jsonify

from .DailyMeasurementController import measurement_bp
from .HealthController import health_bp
from .StationController import station_bp


def register_controllers(app: Flask) -> None:
    app.register_blueprint(health_bp)
    app.register_blueprint(station_bp)
    app.register_blueprint(measurement_bp)

    # Ungültige Eingaben meldet der Service als ValueError, hier zentral zu 400 übersetzt.
    @app.errorhandler(ValueError)
    def handle_invalid_input(error: ValueError):
        return jsonify({"error": str(error)}), 400
