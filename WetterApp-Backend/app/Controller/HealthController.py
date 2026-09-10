from flask import Blueprint, jsonify

health_bp = Blueprint('health', __name__)


@health_bp.route('/api/health', methods=['GET'])
def health_check():
    """Prüft, ob das Backend erreichbar ist.
    ---
    tags:
      - System
    responses:
      200:
        description: Backend läuft.
        schema:
          type: object
          properties:
            status:
              type: string
              example: online
            message:
              type: string
              example: DWD Backend läuft erfolgreich!
    """
    return jsonify({
        "status": "online",
        "message": "DWD Backend läuft erfolgreich!"
    }), 200
