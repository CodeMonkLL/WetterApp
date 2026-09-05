from flask import Blueprint, jsonify

main_bp = Blueprint('main', __name__)

@main_bp.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "online",
        "message": "DWD Backend läuft erfolgreich!"
    }), 200