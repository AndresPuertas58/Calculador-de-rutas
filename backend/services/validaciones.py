"""
Servicio de Validaciones de Disponibilidad
==========================================
Funciones reutilizables para verificar si un conductor y un vehículo
pueden ser asignados a un flete.

Importar en cualquier parte del backend:
    from services.validaciones import validar_conductor, validar_vehiculo
"""

from datetime import date


# ─── Conductor ────────────────────────────────────────────────────────────────

# Estados que impiden la asignación de un conductor.
# Modifica esta lista si necesitas agregar/quitar estados en el futuro.
ESTADOS_CONDUCTOR_BLOQUEANTES = {'Vacaciones', 'Incapacidad', 'Retirado'}


def _vacaciones_vigentes(conductor) -> bool:
    """
    Retorna True si el conductor está en vacaciones activas hoy.
    Usa vacaciones_inicio / vacaciones_fin cuando están disponibles.
    """
    hoy = date.today()
    inicio = conductor.vacaciones_inicio
    fin = conductor.vacaciones_fin
    if inicio and fin:
        return inicio <= hoy <= fin
    # Si no hay fechas, confiar en el campo estado_operativo
    return conductor.estado_operativo == 'Vacaciones'


def _incapacidad_vigente(conductor) -> bool:
    """
    Retorna True si la incapacidad del conductor sigue activa hoy.
    Usa incapacidad_inicio / incapacidad_fin cuando están disponibles.
    """
    hoy = date.today()
    inicio = conductor.incapacidad_inicio
    fin = conductor.incapacidad_fin
    if inicio and fin:
        return inicio <= hoy <= fin
    return conductor.estado_operativo == 'Incapacidad'


def validar_conductor(conductor) -> dict:
    """
    Verifica si un conductor puede ser asignado a un flete.

    Parámetros
    ----------
    conductor : Conductor | None
        Instancia del modelo Conductor o None.

    Retorna
    -------
    dict con las claves:
        disponible (bool) — True si puede ser asignado
        razon      (str)  — Descripción del resultado
    """
    if conductor is None:
        return {"disponible": False, "razon": "El vehículo no tiene conductor asignado"}

    estado = conductor.estado_operativo

    if estado == 'Retirado':
        return {"disponible": False, "razon": f"El conductor {conductor.nombre} está Retirado"}

    if estado == 'Vacaciones' or _vacaciones_vigentes(conductor):
        inicio = conductor.vacaciones_inicio or "?"
        fin    = conductor.vacaciones_fin    or "?"
        return {
            "disponible": False,
            "razon": f"El conductor {conductor.nombre} está en Vacaciones ({inicio} → {fin})"
        }

    if estado == 'Incapacidad' or _incapacidad_vigente(conductor):
        inicio = conductor.incapacidad_inicio or "?"
        fin    = conductor.incapacidad_fin    or "?"
        return {
            "disponible": False,
            "razon": f"El conductor {conductor.nombre} está en Incapacidad ({inicio} → {fin})"
        }

    return {"disponible": True, "razon": f"El conductor {conductor.nombre} está Activo"}


# ─── Vehículo ─────────────────────────────────────────────────────────────────

# Estados que impiden la asignación del vehículo.
# Modifica esta lista si necesitas agregar/quitar estados.
ESTADOS_VEHICULO_BLOQUEANTES = {'Mantenimiento', 'En Ruta', 'Inactivo'}


def validar_vehiculo(vehiculo) -> dict:
    """
    Verifica si un vehículo puede ser asignado a un flete.

    Parámetros
    ----------
    vehiculo : Vehiculo | None
        Instancia del modelo Vehiculo o None.

    Retorna
    -------
    dict con las claves:
        disponible (bool) — True si puede ser asignado
        razon      (str)  — Descripción del resultado
    """
    if vehiculo is None:
        return {"disponible": False, "razon": "Vehículo no encontrado"}

    estado = vehiculo.estado or "Desconocido"

    if estado in ESTADOS_VEHICULO_BLOQUEANTES:
        mensajes = {
            'Mantenimiento': f"El vehículo {vehiculo.cod_vehiculo} ({vehiculo.placa}) está en Mantenimiento",
            'En Ruta':       f"El vehículo {vehiculo.cod_vehiculo} ({vehiculo.placa}) ya está En Ruta",
            'Inactivo':      f"El vehículo {vehiculo.cod_vehiculo} ({vehiculo.placa}) está Inactivo",
        }
        return {
            "disponible": False,
            "razon": mensajes.get(estado, f"El vehículo no está disponible (estado: {estado})")
        }

    if estado != 'Disponible':
        return {
            "disponible": False,
            "razon": f"El vehículo {vehiculo.cod_vehiculo} tiene estado desconocido: '{estado}'"
        }

    return {"disponible": True, "razon": f"El vehículo {vehiculo.cod_vehiculo} está Disponible"}
