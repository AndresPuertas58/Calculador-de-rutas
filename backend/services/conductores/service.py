"""
Módulo: Conductores
Responsabilidad: Consulta y transformación de datos de conductores.
                 Reglas de negocio del sistema de puntos.

Variables clave:
    - PUNTOS_POR_TRAMO: puntos ganados por cada bloque de km completado
    - KM_POR_TRAMO:     km requeridos para ganar un tramo
    - MAX_PUNTOS:       tope máximo de puntos por conductor
"""
from models.database import Conductor

# ─── Constantes del sistema de puntos ────────────────────────────────────────
PUNTOS_POR_TRAMO = 1   # puntos ganados por cada bloque de km
KM_POR_TRAMO = 450     # km necesarios para ganar un bloque
MAX_PUNTOS = 18        # tope máximo de puntos
# ─────────────────────────────────────────────────────────────────────────────


def obtener_datos_conductores():
    """Retorna todos los conductores formateados para el frontend."""
    conductores = Conductor.query.all()
    return [{
        "cod_empleado": c.cod_empleado,
        "nombre": c.nombre,
        "cedula": c.cedula,
        "licencia": c.licencia or "C3",
        "estado_operativo": c.estado_operativo or "Activo",
        "vacaciones": f"{c.vacaciones_inicio} a {c.vacaciones_fin}" if c.vacaciones_inicio else "Activo",
        "incapacidad": f"{c.incapacidad_inicio} a {c.incapacidad_fin}" if c.incapacidad_inicio else "No",
        "telefono": c.telefono or "N/A",
        "puntos": c.puntos or 0,
        "vehiculo_habitual": c.cod_vehiculo_habitual or "Sin asignar"
    } for c in conductores]


def calcular_puntos_ganados(dist_viaje_km: float) -> int:
    """
    Calcula los puntos que gana un conductor según los km del viaje cargado.

    Regla: PUNTOS_POR_TRAMO por cada bloque de KM_POR_TRAMO km completados.
    Ejemplo con valores por defecto: 900 km → 2 puntos, 450 km → 1 punto.
    """
    return int(dist_viaje_km // KM_POR_TRAMO) * PUNTOS_POR_TRAMO


def acumular_puntos(conductor: Conductor, dist_viaje_km: float) -> int:
    """
    Aplica los puntos ganados al conductor (con tope MAX_PUNTOS).
    Retorna los puntos ganados en esta asignación.
    """
    puntos_ganados = calcular_puntos_ganados(dist_viaje_km)
    if puntos_ganados > 0:
        conductor.puntos = min((conductor.puntos or 0) + puntos_ganados, MAX_PUNTOS)
    return puntos_ganados
