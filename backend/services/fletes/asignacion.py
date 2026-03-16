
import math
from datetime import datetime
from models.database import db, Flete, Vehiculo, Conductor, AsignacionHistorial, PuntoParqueo
from services.route_service import ServicioRuta
from services.fletes.costos import (
    calcular_costo_combustible,
    detectar_peajes_en_ruta,
    calcular_costos_fijos
)
from services.conductores.service import acumular_puntos
from services.validaciones import validar_conductor, validar_vehiculo

_servicio_ruta = ServicioRuta()

def _encontrar_parqueo_mas_cercano(destino_lat, destino_lon) -> object:
    """
    Busca el PuntoParqueo más cercano al destino usando distancia euclidiana.
    Retorna el objeto PuntoParqueo o None si no hay ninguno.
    """
    parqueos = PuntoParqueo.query.all()
    if not parqueos:
        return None
    return min(
        parqueos,
        key=lambda p: math.sqrt(
            (float(p.latitud) - float(destino_lat))**2 +
            (float(p.longitud) - float(destino_lon))**2
        )
    )


def obtener_mejores_camiones_para_flete(cod_flete: str) -> dict:
    """
    Evalúa todos los vehículos disponibles para un flete.
    Flujo completo del costo:
      Parqueo → Origen (vacío) → Destino (cargado) → Parqueo más cercano (retorno vacío)
    """
    flete = Flete.query.filter_by(cod_flete=cod_flete).first()
    if not flete:
        return {"error": "Flete no encontrado"}

    origen = (flete.origen_lat, flete.origen_lon)
    destino = (flete.destino_lat, flete.destino_lon)

    # Parqueo más cercano al punto de entrega (igual para todos los vehículos)
    parqueo_retorno = _encontrar_parqueo_mas_cercano(flete.destino_lat, flete.destino_lon)
    pos_retorno = (parqueo_retorno.latitud, parqueo_retorno.longitud) if parqueo_retorno else None

    vehiculos = Vehiculo.query.filter_by(estado='Disponible').all()
    resultados = []

    for v in vehiculos:
        if not v.punto_parqueo:
            continue

        conductor = Conductor.query.filter_by(cod_empleado=v.cod_conductor_actual).first()

        # ── Validaciones de disponibilidad ─────────────────────────────────
        val_vehiculo = validar_vehiculo(v)
        if not val_vehiculo['disponible']:
            continue   # Estado del vehículo impide asignación

        val_conductor = validar_conductor(conductor)
        if not val_conductor['disponible']:
            continue   # Estado del conductor impide asignación

        pos_parqueo = (v.punto_parqueo.latitud, v.punto_parqueo.longitud)

        # ── Tramo 1: Parqueo → Origen (vacío) ──────────────────────────────
        ruta_vacio = _servicio_ruta.obtener_ruta_camion(pos_parqueo, origen)
        # ── Tramo 2: Origen → Destino (cargado) ────────────────────────────
        ruta_cargado = _servicio_ruta.obtener_ruta_camion(origen, destino)
        if not ruta_vacio or not ruta_cargado:
            continue

        dist_vacio_km = round(ruta_vacio['distance'] / 1000, 2)
        dist_viaje_km = round(ruta_cargado['distance'] / 1000, 2)
        tiempo_min = round((ruta_vacio['time'] + ruta_cargado['time']) / 60000, 2)

        # ── Tramo 3: Destino → Parqueo más cercano (retorno vacío) ─────────
        dist_retorno_km = 0.0
        ruta_retorno = None
        peajes_retorno = []
        costo_peajes_retorno = 0
        nombre_parqueo_retorno = "N/A"

        if pos_retorno:
            ruta_retorno = _servicio_ruta.obtener_ruta_camion(destino, pos_retorno)
            if ruta_retorno:
                dist_retorno_km = round(ruta_retorno['distance'] / 1000, 2)
                tiempo_min += round(ruta_retorno['time'] / 60000, 2)
                peajes_retorno, costo_peajes_retorno = detectar_peajes_en_ruta(
                    ruta_retorno.get('points', [])
                )
                nombre_parqueo_retorno = parqueo_retorno.sede

        # ── Costos totales ──────────────────────────────────────────────────
        dist_total_km = dist_vacio_km + dist_viaje_km + dist_retorno_km
        costo_combustible = calcular_costo_combustible(dist_total_km)

        peajes_vacio, costo_peajes_vacio = detectar_peajes_en_ruta(ruta_vacio.get('points', []))
        peajes_viaje, costo_peajes_viaje = detectar_peajes_en_ruta(ruta_cargado.get('points', []))
        costo_peajes = costo_peajes_vacio + costo_peajes_viaje + costo_peajes_retorno

        fijos = calcular_costos_fijos(flete)
        costo_total = costo_combustible + costo_peajes + fijos['total']

        resultados.append({
            "cod_vehiculo": v.cod_vehiculo,
            "placa": v.placa,
            "marca": v.marca,
            "conductor": conductor.nombre if conductor else "No asignado",
            "licencia": conductor.licencia if conductor else "N/A",
            "puntos_conductor": conductor.puntos if conductor else 18,
            "km_actual": v.km_actual or 0,
            "km_proximo_aceite": v.km_proximo_aceite or 0,
            "estado_llantas": v.estado_llantas or "Bueno",
            "distancia_vacio": dist_vacio_km,
            "distancia_viaje": dist_viaje_km,
            "distancia_retorno": dist_retorno_km,
            "parqueo_retorno": nombre_parqueo_retorno,
            "costo_combustible": round(costo_combustible, 2),
            "valor_cargue": fijos['valor_cargue'],
            "valor_descargue": fijos['valor_descargue'],
            "valor_escolta": fijos['valor_escolta'],
            "viaticos_estimados": fijos['viaticos_estimados'],
            "valor_poliza": fijos['valor_poliza'],
            "peajes": peajes_vacio + peajes_viaje + peajes_retorno,
            "costo_peajes": costo_peajes,
            "costo_peajes_vacio": costo_peajes_vacio,
            "costos_fijos": round(fijos['total'], 2),
            "costo_total": round(costo_total, 2),
            "tiempo_total_min": round(tiempo_min, 2),
            "route_vacio_points": ruta_vacio.get('points', []),
            "route_points": ruta_cargado.get('points', []),
            "route_retorno_points": ruta_retorno.get('points', []) if ruta_retorno else [],
            "truck_pos": [float(v.punto_parqueo.latitud), float(v.punto_parqueo.longitud)],
            "_costos": {
                "dist_vacio_km": dist_vacio_km,
                "dist_viaje_km": dist_viaje_km,
                "dist_retorno_km": dist_retorno_km,
                "tiempo_min": round(tiempo_min, 2),
                "costo_combustible": round(costo_combustible, 2),
                "costo_peajes": costo_peajes,
                "costos_fijos": round(fijos['total'], 2),
                "costo_total": round(costo_total, 2)
            }
        })

    # ── Paso 1: elegir las 3 opciones más baratas ─────────────────────────────
    resultados.sort(key=lambda x: x['costo_total'])
    top3 = resultados[:3]

    # ── Paso 2: dentro de las 3 más baratas, mostrar primero al de menos puntos
    # Así el cliente ve las 3 opciones económicas ordenadas de más justo a menos justo y luego ordenar por puntos esos 3 resultados
    # La decisión final siempre la toma el cliente.
    top3.sort(key=lambda x: (x['costo_total'], x['puntos_conductor']))


    return {
        "flete": {
            "cod_flete": flete.cod_flete,
            "cliente": flete.cliente,
            "producto": flete.producto,
            "peso": float(flete.peso_carga or 0),
            "punto_carga": flete.punto_carga or f"Coords: {flete.origen_lat}, {flete.origen_lon}",
            "origen": f"{flete.origen_lat}, {flete.origen_lon}",
            "destino": f"{flete.destino_lat}, {flete.destino_lon}",
            "valor_cargue": float(flete.valor_cargue or 0),
            "valor_descargue": float(flete.valor_descargue or 0),
            "viaticos": float(flete.viaticos_estimados or 0),
            "escolta": float(flete.valor_escolta or 0),
            "destino": flete.destino
        },
        "recommendations": top3
    }


def asignar_camion(cod_flete: str, cod_vehiculo: str, costos: dict = None) -> tuple:
    """Asigna un vehículo al flete, acumula puntos y persiste el historial."""
    flete = Flete.query.filter_by(cod_flete=cod_flete).first()
    vehiculo = Vehiculo.query.filter_by(cod_vehiculo=cod_vehiculo).first()
    if not flete or not vehiculo:
        return False, "Flete o Vehículo no encontrado"

    # ── Re-validación antes de confirmar (evita asignaciones duplicadas o sobre estados incorrectos)
    val_v = validar_vehiculo(vehiculo)
    if not val_v['disponible']:
        return False, val_v['razon']

    conductor = Conductor.query.filter_by(cod_empleado=vehiculo.cod_conductor_actual).first()
    val_c = validar_conductor(conductor)
    if not val_c['disponible']:
        return False, val_c['razon']

    try:
        # Puntos al conductor
        dist = costos.get('dist_viaje_km', 0) if costos else 0
        if dist > 0 and conductor:
            acumular_puntos(conductor, dist)

        # Guardar historial
        existente = AsignacionHistorial.query.filter_by(cod_flete=cod_flete).first()
        if existente:
            db.session.delete(existente)

        db.session.add(AsignacionHistorial(
            cod_flete=cod_flete,
            cod_vehiculo=cod_vehiculo,
            placa=vehiculo.placa,
            conductor=conductor.nombre if conductor else "No asignado",
            fecha_asignacion=datetime.utcnow(),
            distancia_vacio_km=costos.get('dist_vacio_km', 0) if costos else 0,
            distancia_viaje_km=dist,
            tiempo_total_min=costos.get('tiempo_min', 0) if costos else 0,
            costo_combustible=costos.get('costo_combustible', 0) if costos else 0,
            costo_peajes=costos.get('costo_peajes', 0) if costos else 0,
            costos_fijos=costos.get('costos_fijos', 0) if costos else 0,
            costo_total=costos.get('costo_total', 0) if costos else 0,
            venta=float(flete.venta or 0),
            margin=round(((float(flete.venta) - float(costos.get('costo_total', 0))) / float(flete.venta) * 100), 2) if float(flete.venta or 0) > 0 else 0
        ))

        flete.cod_vehiculo_asignado = cod_vehiculo
        flete.cod_empleado_asignado = vehiculo.cod_conductor_actual
        flete.estado = 'asignado'
        vehiculo.estado = 'En Ruta'
        vehiculo.cod_flete_activo = cod_flete

        db.session.commit()
        return True, "Asignación exitosa"
    except Exception as e:
        db.session.rollback()
        return False, str(e)


def desasignar_camion(cod_flete: str) -> tuple:
    """Libera el vehículo y elimina el historial del flete."""
    flete = Flete.query.filter_by(cod_flete=cod_flete).first()
    if not flete or not flete.cod_vehiculo_asignado:
        return False, "Flete no encontrado o sin vehículo asignado"

    try:
        vehiculo = Vehiculo.query.filter_by(cod_vehiculo=flete.cod_vehiculo_asignado).first()
        if vehiculo:
            vehiculo.estado = 'Disponible'
            vehiculo.cod_flete_activo = None

        historial = AsignacionHistorial.query.filter_by(cod_flete=cod_flete).first()
        if historial:
            db.session.delete(historial)

        flete.cod_vehiculo_asignado = None
        flete.cod_empleado_asignado = None
        flete.estado = 'sin_asignar'

        db.session.commit()
        return True, "Desasignación exitosa"
    except Exception as e:
        db.session.rollback()
        return False, str(e)
