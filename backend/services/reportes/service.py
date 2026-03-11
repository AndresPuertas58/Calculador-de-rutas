"""
Módulo: Reportes
Responsabilidad: Consultar el historial de asignaciones para el reporte financiero.
"""
from models.database import AsignacionHistorial


def obtener_reporte() -> list:
    """
    Retorna todos los fletes asignados con sus costos y margen.
    Solo consulta la tabla asignaciones_historial (ya tiene los costos persistidos).
    """
    registros = AsignacionHistorial.query.all()
    resultado = []
    for h in registros:
        venta = float(h.venta or 0)
        costo = float(h.costo_total or 0)
        resultado.append({
            "cod_flete": h.cod_flete,
            "cliente": h.flete.cliente if h.flete else "",
            "producto": h.flete.producto if h.flete else "",
            "placa": h.placa or "",
            "conductor": h.conductor or "",
            "fecha_asignacion": str(h.fecha_asignacion)[:16] if h.fecha_asignacion else "",
            "distancia_vacio_km": float(h.distancia_vacio_km or 0),
            "distancia_viaje_km": float(h.distancia_viaje_km or 0),
            "tiempo_total_min": float(h.tiempo_total_min or 0),
            "costo_combustible": float(h.costo_combustible or 0),
            "costo_peajes": float(h.costo_peajes or 0),
            "costos_fijos": float(h.costos_fijos or 0),
            "costo_total": costo,
            "venta": venta,
            "margen": round(venta - costo, 2)
        })
    return resultado
