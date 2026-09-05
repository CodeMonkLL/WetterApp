from flask import Flask
from flask_cors import CORS
from app.routes import main_bp

def create_app():
    app = Flask(__name__)
    
    # Erlaubt Anfragen vom Angular-Frontend
    CORS(app)

    # Route registrieren
    
    app.register_blueprint(main_bp)

    return app