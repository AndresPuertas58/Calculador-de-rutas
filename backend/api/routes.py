from flask import Blueprint, jsonify, request
from services.route_service import RouteService
from services.db_service import DbService
from services.assignment_service import AssignmentService

api_blueprint = Blueprint('api', __name__)
route_service = RouteService()
db_service = DbService()
assignment_service = AssignmentService()

@api_blueprint.route('/calculate', methods=['POST'])
def calculate_route():
    data = request.json
    result = route_service.get_truck_route(data.get('origin'), data.get('destination'))
    return jsonify(result)

@api_blueprint.route('/dashboard', methods=['GET'])
def get_dashboard():
    try:
        data = db_service.get_dashboard_data()
        return jsonify(data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_blueprint.route('/conductores', methods=['GET'])
def get_conductores():
    try:
        data = db_service.get_conductores_data()
        return jsonify(data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_blueprint.route('/vehiculos', methods=['GET'])
def get_vehiculos():
    try:
        data = db_service.get_vehiculos_data()
        return jsonify(data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_blueprint.route('/assign/<cod_flete>', methods=['GET'])
def get_assignments(cod_flete):
    """
    Endpoint que retorna las mejores opciones de transporte para un flete.
    """
    try:
        recommendations = assignment_service.get_best_trucks_for_flete(cod_flete)
        return jsonify(recommendations), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_blueprint.route('/assign', methods=['POST'])
def assign_truck():
    """
    Endpoint para realizar la asignación física en la base de datos.
    Recibe cod_flete y cod_vehiculo.
    """
    data = request.json
    cod_flete = data.get('cod_flete')
    cod_vehiculo = data.get('cod_vehiculo')
    
    if not cod_flete or not cod_vehiculo:
        return jsonify({"error": "cod_flete y cod_vehiculo son requeridos"}), 400
        
    try:
        success, message = db_service.assign_truck_to_flete(cod_flete, cod_vehiculo)
        if success:
            return jsonify({"message": message}), 200
        else:
            return jsonify({"error": message}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_blueprint.route('/unassign/<cod_flete>', methods=['POST'])
def unassign_truck(cod_flete):
    """
    Endpoint para desasignar el vehículo de un flete y devolverlo a disponible.
    """
    try:
        success, message = db_service.unassign_truck_from_flete(cod_flete)
        if success:
            return jsonify({"message": message}), 200
        else:
            return jsonify({"error": message}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500
