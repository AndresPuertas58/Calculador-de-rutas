from service.selector import seleccionar_mejor_camion, obtener_opciones_alternativas
from service.ruteo import guardar_ruta_envio
from service.costos import filtrar_peajes_en_ruta
from models.envio import Envio
from models.punto_venta import PuntoVenta
from models.peaje import Peaje


def asignar_camion_a_envio(db, envio_id: int):
    camion, ruta, costos = seleccionar_mejor_camion(db, envio_id)

    if not camion:
        return None

    envio = db.query(Envio).get(envio_id)
    envio.camion_id = camion.id
    db.commit()

    # Consultas necesarias para el response
    peajes = db.query(Peaje).all()
    punto_carga = db.query(PuntoVenta).get(envio.punto_venta_id)

    # Guardar opción principal
    ruta_guardada = guardar_ruta_envio(
        db=db,
        envio_id=envio_id,
        camion_id=camion.id,
        ruta=ruta,
        costo_acpm=costos["acpm"],
        costo_peajes=costos["peajes"],
        tipo_opcion="optima",
        asignada=True
    )

    # Obtener y guardar opciones alternativas
    opciones_extra = obtener_opciones_alternativas(db, envio_id, camion.id)
    tipos = ["rapida", "alternativa"]

    rutas_extra_guardadas = []
    for i, opcion in enumerate(opciones_extra):
        r = guardar_ruta_envio(
            db=db,
            envio_id=envio_id,
            camion_id=opcion["camion"].id,
            ruta=opcion["ruta"],
            costo_acpm=opcion["costos"]["acpm"],
            costo_peajes=opcion["costos"]["peajes"],
            tipo_opcion=tipos[i],
            asignada=False
        )
        rutas_extra_guardadas.append((r, opcion))

    # Helper para serializar peajes cercanos a una ruta
    def serializar_peajes(polyline):
        return [
            {
                "id": p.id,
                "nombre": p.nombrepeaje,
                "latitud": float(p.latitud),
                "longitud": float(p.longitud),
                "costo": float(p.categoriai)
            }
            for p in filtrar_peajes_en_ruta(polyline, peajes)
        ]

    return {
        "envio_id": envio_id,
        "punto_carga": {
            "latitud": float(punto_carga.latitud),
            "longitud": float(punto_carga.longitud),
            "ciudad": punto_carga.ciudad
        },
        "destino": {
            "latitud": float(envio.latitud),
            "longitud": float(envio.longitud)
        },
        "opciones": [
            {
                "ruta_id": ruta_guardada.id,
                "tipo": "optima",
                "etiqueta": "Óptima (menor costo)",
                "asignada": True,
                "camion": {
                    "id": camion.id,
                    "placa": camion.placa,
                    "latitud": float(camion.latitud),
                    "longitud": float(camion.longitud)
                },
                "distancia_km": float(ruta_guardada.distancia_km),
                "tiempo_horas": round(ruta_guardada.tiempo_seg / 3600, 1),
                "costo_acpm": float(ruta_guardada.costo_acpm),
                "costo_peajes": float(ruta_guardada.costo_peajes),
                "costo_total": float(ruta_guardada.costo_total),
                "polyline": ruta["polyline"],
                "peajes": serializar_peajes(ruta["polyline"])
            }
        ] + [
            {
                "ruta_id": r.id,
                "tipo": tipos[i],
                "etiqueta": op["etiqueta"],
                "asignada": False,
                "camion": {
                    "id": op["camion"].id,
                    "placa": op["camion"].placa,
                    "latitud": float(op["camion"].latitud),
                    "longitud": float(op["camion"].longitud)
                },
                "distancia_km": float(r.distancia_km),
                "tiempo_horas": round(r.tiempo_seg / 3600, 1),
                "costo_acpm": float(r.costo_acpm),
                "costo_peajes": float(r.costo_peajes),
                "costo_total": float(r.costo_total),
                "polyline": op["ruta"]["polyline"],
                "peajes": serializar_peajes(op["ruta"]["polyline"])
            }
            for i, (r, op) in enumerate(rutas_extra_guardadas)
        ]
    }