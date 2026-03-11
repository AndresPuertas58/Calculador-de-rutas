"""
Módulo: Flota
Responsabilidad: Consulta y transformación de datos de vehículos.
"""
from models.database import Flete, Vehiculo


def obtener_datos_vehiculos():
    """Retorna todos los vehículos formateados para el frontend."""
    vehiculos = Vehiculo.query.all()
    resultado = []
    for v in vehiculos:
        flete_info = "Ninguno"
        if v.cod_flete_activo:
            flete = Flete.query.filter_by(cod_flete=v.cod_flete_activo).first()
            if flete:
                flete_info = f"{flete.cod_flete} - {flete.cliente} ({flete.producto})"
        resultado.append({
            "cod_vehiculo": v.cod_vehiculo,
            "placa": v.placa,
            "marca": v.marca or "N/A",
            "color": v.color or "N/A",
            "tipo_plancha": v.tipo_plancha or "N/A",
            "km_actual": v.km_actual or 0,
            "km_proximo_aceite": v.km_proximo_aceite or 0,
            "estado_llantas": v.estado_llantas or "Bueno",
            "estado": v.estado or "Disponible",
            "lat": float(v.punto_parqueo.latitud) if v.punto_parqueo else None,
            "lon": float(v.punto_parqueo.longitud) if v.punto_parqueo else None,
            "punto_parqueo": {
                "sede": v.punto_parqueo.sede,
                "direccion": v.punto_parqueo.direccion or "",
            } if v.punto_parqueo else None,
            "flete_activo": flete_info
        })
    return resultado
