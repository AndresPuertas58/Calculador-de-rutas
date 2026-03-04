from flask import Blueprint, jsonify, request
from services.route_service import ServicioRuta
from services.db_service import ServicioBaseDatos
from services.assignment_service import ServicioAsignacion

api_blueprint = Blueprint('api', __name__)
servicio_ruta = ServicioRuta()
servicio_bd = ServicioBaseDatos()
servicio_asignacion = ServicioAsignacion()

@api_blueprint.route('/calculate', methods=['POST'])
def calcular_ruta():
    datos = request.json
    resultado = servicio_ruta.obtener_ruta_camion(datos.get('origin'), datos.get('destination'))
    return jsonify(resultado)

@api_blueprint.route('/dashboard', methods=['GET'])
def obtener_dashboard():
    try:
        datos = servicio_bd.obtener_datos_dashboard()
        return jsonify(datos), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_blueprint.route('/conductores', methods=['GET'])
def obtener_conductores():
    try:
        datos = servicio_bd.obtener_datos_conductores()
        return jsonify(datos), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_blueprint.route('/vehiculos', methods=['GET'])
def obtener_vehiculos():
    try:
        datos = servicio_bd.obtener_datos_vehiculos()
        return jsonify(datos), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_blueprint.route('/assign/<cod_flete>', methods=['GET'])
def obtener_asignaciones(cod_flete):
    """
    Endpoint que retorna las mejores opciones de transporte para un flete.
    """
    try:
        recomendaciones = servicio_asignacion.obtener_mejores_camiones_para_flete(cod_flete)
        return jsonify(recomendaciones), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_blueprint.route('/assign', methods=['POST'])
def asignar_camion():
    """
    Endpoint para realizar la asignación física en la base de datos.
    """
    datos = request.json
    cod_flete = datos.get('cod_flete')
    cod_vehiculo = datos.get('cod_vehiculo')
    
    if not cod_flete or not cod_vehiculo:
        return jsonify({"error": "cod_flete y cod_vehiculo son requeridos"}), 400
        
    try:
        exito, mensaje = servicio_bd.asignar_camion_a_flete(cod_flete, cod_vehiculo)
        if exito:
            return jsonify({"message": mensaje}), 200
        else:
            return jsonify({"error": mensaje}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_blueprint.route('/unassign/<cod_flete>', methods=['POST'])
def desasignar_camion(cod_flete):
    """
    Endpoint para desasignar el vehículo de un flete.
    """
    try:
        exito, mensaje = servicio_bd.desasignar_camion_de_flete(cod_flete)
        if exito:
            return jsonify({"message": mensaje}), 200
        else:
            return jsonify({"error": mensaje}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500
