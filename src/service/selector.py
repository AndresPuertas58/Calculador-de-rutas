from models.camion import Camion
from service.ruteo import obtener_ruta
from service.costos import calcular_costo_acpm, calcular_costo_peajes, costos_generales_envio
from models.envio import Envio
from models.punto_venta import PuntoVenta
from models.peaje import Peaje



def _evaluar_camion(camion, punto_carga, envio, peajes):
    """Calcula ruta y costos para un camión dado."""
    ruta1 = obtener_ruta(
        (camion.latitud, camion.longitud),
        (punto_carga.latitud, punto_carga.longitud)
    )
    ruta2 = obtener_ruta(
        (punto_carga.latitud, punto_carga.longitud),
        (envio.latitud, envio.longitud)
    )

    distancia_total = ruta1["distancia_km"] + ruta2["distancia_km"]
    tiempo_total = ruta1["tiempo_seg"] + ruta2["tiempo_seg"]
    polyline_total = ruta1["polyline"] + ruta2["polyline"]

    costo_acpm = calcular_costo_acpm(distancia_total, float(camion.consumo_km_litro))
    costo_peajes = calcular_costo_peajes(polyline_total, peajes)
    generales = costos_generales_envio(envio)

    costo_total = costo_acpm + costo_peajes + generales["total"]

    return {
        "distancia_km": distancia_total,
        "tiempo_seg": tiempo_total,
        "polyline": polyline_total
    }, {
        "acpm": costo_acpm,
        "peajes": costo_peajes,
        "valor_carga": generales["valor_carga"],
        "valor_descarga": generales["valor_descarga"],
        "escolta": generales["escolta"],
        "viaticos": generales["viaticos"],
        "generales": generales["total"],
        "total": costo_total
    }


def seleccionar_mejor_camion(db, envio_id: int):
    envio = db.query(Envio).get(envio_id)
    if not envio:
        return None, None, None

    punto_carga = db.query(PuntoVenta).get(envio.punto_venta_id)
    if not punto_carga:
        return None, None, None

    camiones = db.query(Camion).filter(Camion.estado == "disponible").all()
    peajes = db.query(Peaje).all()

    mejor_camion = None
    mejor_ruta = None
    menor_costo = float("inf")
    costos_mejor = None

    for camion in camiones:
        ruta, costos = _evaluar_camion(camion, punto_carga, envio, peajes)

        if costos["total"] < menor_costo:
            menor_costo = costos["total"]
            mejor_camion = camion
            mejor_ruta = ruta
            costos_mejor = costos

    return mejor_camion, mejor_ruta, costos_mejor


def obtener_opciones_alternativas(db, envio_id: int, camion_principal_id: int):
    envio = db.query(Envio).get(envio_id)
    punto_carga = db.query(PuntoVenta).get(envio.punto_venta_id)
    peajes = db.query(Peaje).all()

    camiones_restantes = (
        db.query(Camion)
        .filter(Camion.estado == "disponible", Camion.id != camion_principal_id)
        .all()
    )

    if not camiones_restantes:
        return []

    evaluaciones = []
    for camion in camiones_restantes:
        ruta, costos = _evaluar_camion(camion, punto_carga, envio, peajes)
        evaluaciones.append({
            "camion": camion,
            "ruta": ruta,
            "costos": costos
        })

    mas_rapida = min(evaluaciones, key=lambda x: x["ruta"]["tiempo_seg"])
    mas_rapida["etiqueta"] = "Más rápida"

    restantes = [e for e in evaluaciones if e["camion"].id != mas_rapida["camion"].id]
    alternativas = [mas_rapida]

    if restantes:
        segunda = min(restantes, key=lambda x: x["costos"]["total"])
        segunda["etiqueta"] = "Alternativa económica"
        alternativas.append(segunda)

    return alternativas