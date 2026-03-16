"""
API Routes — Flask Backend
Responsabilidad: Exponer los endpoints HTTP. No contiene lógica de negocio.

Cada endpoint delega en el módulo especializado correspondiente:
  - /conductores  → services/conductores/service.py
  - /vehiculos    → services/flota/service.py
  - /assign       → services/fletes/asignacion.py
  - /reporte      → services/reportes/service.py
"""
from flask import Blueprint, jsonify, request
from services.conductores.service import obtener_datos_conductores
from services.flota.service import obtener_datos_vehiculos
from services.fletes.asignacion import (
    obtener_mejores_camiones_para_flete,
    asignar_camion,
    desasignar_camion
)
from services.reportes.service import obtener_reporte
from services.db_service import ServicioBaseDatos
from services.route_service import ServicioRuta

api_blueprint = Blueprint('api', __name__)
servicio_bd = ServicioBaseDatos()     # Solo para dashboard (usa modelos directamente)
servicio_ruta = ServicioRuta()

# Caché temporal para pasar costos entre GET y POST de /assign
_costos_cache = {}


@api_blueprint.route('/calculate', methods=['POST'])
def calcular_ruta():
    datos = request.json
    resultado = servicio_ruta.obtener_ruta_camion(datos.get('origin'), datos.get('destination'))
    return jsonify(resultado)


@api_blueprint.route('/fletes', methods=['GET'])
def endpoint_fletes():
    try:
        return jsonify(servicio_bd.obtener_datos_fletes()), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_blueprint.route('/conductores', methods=['GET'])
def endpoint_conductores():
    try:
        return jsonify(obtener_datos_conductores()), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_blueprint.route('/vehiculos', methods=['GET'])
def endpoint_vehiculos():
    try:
        return jsonify(obtener_datos_vehiculos()), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500



@api_blueprint.route('/assign/<cod_flete>', methods=['GET'])
def endpoint_recomendar(cod_flete): 
    """
    Calcula y retorna las 3 mejores opciones de camión para el flete.
    Guarda en caché los costos calculados para usarlos al confirmar la asignación.
    """
    try:
        resultado = obtener_mejores_camiones_para_flete(cod_flete)
        for rec in resultado.get('recommendations', []):
            key = f"{cod_flete}:{rec['cod_vehiculo']}"
            _costos_cache[key] = rec.pop('_costos', {})
        return jsonify(resultado), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_blueprint.route('/assign', methods=['POST'])
def endpoint_asignar():
    """
    Confirma la asignación. Recupera los costos del caché calculado en el GET anterior.
    """
    datos = request.json
    cod_flete = datos.get('cod_flete')
    cod_vehiculo = datos.get('cod_vehiculo')

    if not cod_flete or not cod_vehiculo:
        return jsonify({"error": "cod_flete y cod_vehiculo son requeridos"}), 400

    try:
        costos = _costos_cache.pop(f"{cod_flete}:{cod_vehiculo}", None)
        exito, mensaje = asignar_camion(cod_flete, cod_vehiculo, costos=costos)
        return jsonify({"message": mensaje} if exito else {"error": mensaje}), 200 if exito else 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_blueprint.route('/unassign/<cod_flete>', methods=['POST'])
def endpoint_desasignar(cod_flete):
    """Libera el vehículo y elimina el historial del flete."""
    try:
        exito, mensaje = desasignar_camion(cod_flete)
        return jsonify({"message": mensaje} if exito else {"error": mensaje}), 200 if exito else 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_blueprint.route('/reporte', methods=['GET'])
def endpoint_reporte():
    # Capturamos los parámetros de la URL: /reporte?inicio=YYYY-MM-DD&fin=YYYY-MM-DD
    inicio = request.args.get('inicio')
    fin = request.args.get('fin')
    
    try:
        return jsonify(obtener_reporte(inicio, fin)), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500