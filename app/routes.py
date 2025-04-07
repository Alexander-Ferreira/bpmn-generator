from flask import Blueprint, request, jsonify, current_app
from app.services.gemini_service import generate_bpmn as generate_bpmn_xml  
bp = Blueprint('api', __name__)

@bp.route('/generate', methods=['POST'])
def handle_generate():
    try:
        data = request.get_json()
        
        # Validación más estricta
        if not data or not isinstance(data, dict) or 'description' not in data:
            current_app.logger.error("Datos de entrada inválidos")
            return jsonify({"error": "Se requiere una descripción del proceso"}), 400
        
        description = data['description'].strip()
        
        if len(description) < 20:
            current_app.logger.warning(f"Descripción demasiado corta: {description}")
            return jsonify({"error": "La descripción debe tener al menos 20 caracteres"}), 400
        
        # Llamada al servicio
        bpmn_xml = generate_bpmn_xml(description)
        return jsonify({"bpmn": bpmn_xml})
        
    except Exception as e:
        current_app.logger.error(f"Error en handle_generate: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500