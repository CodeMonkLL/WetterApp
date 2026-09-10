import os
from flask import Flask
from flask_cors import CORS
from flasgger import Swagger
from app.Repository.DbContext import dbcontext

SWAGGER_TEMPLATE = {
    "info": {
        "title": "WetterApp API",
        "description": "Historische Tagesklimadaten des DWD: Stationen und Messwerte.",
        "version": "1.0.0",
    },
}

def create_app():
    app = Flask(__name__)

    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
    # Erlaubt Anfragen vom Angular-Frontend
    CORS(app)

    dbcontext.init_app(app)

    from app.Model import DailyMeasurement, Station  # noqa: F401  Modelle bei SQLAlchemy registrieren
    from app.Controller import register_controllers
    from app.cli import register_cli

    with app.app_context():
        dbcontext.create_all()

    Swagger(app, template=SWAGGER_TEMPLATE)
    register_controllers(app)
    register_cli(app)

    return app