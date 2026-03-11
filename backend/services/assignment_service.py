from services.route_service import ServicioRuta
from models.database import Flete, Vehiculo, Conductor, db
import os


class ServicioAsignacion:
    def __init__(self):
        self.servicio_ruta = ServicioRuta()
        self.precio_diesel = float(os.getenv('DIESEL_PRICE', 10885))
        self.consumo_por_km = 0.35

    def obtener_peajes_en_ruta(self, puntos):
        """Detecta qué peajes están en la ruta usando geofencing."""
        if not puntos:
            return [], 0

        from models.database import Peaje
        import math

        lats = [p[1] for p in puntos]
        lons = [p[0] for p in puntos]
        min_lat, max_lat = min(lats) - 0.01, max(lats) + 0.01
        min_lon, max_lon = min(lons) - 0.01, max(lons) + 0.01

        candidatos = Peaje.query.filter(
            Peaje.latitud.between(min_lat, max_lat),
            Peaje.longitud.between(min_lon, max_lon)
        ).all()

        peajes_en_ruta = []
        costo_total_peajes = 0
        umbral = 0.0045  # ~500m

        for peaje in candidatos:
            p_lat = float(peaje.latitud)
            p_lon = float(peaje.longitud)
            is_near = any(
                ((p_lat - pt[1])**2 + (p_lon - pt[0])**2) ** 0.5 < umbral
                for pt in puntos
            )
            if is_near:
                peajes_en_ruta.append({
                    "nombre": peaje.nombrepeaje,
                    "costo": int(peaje.categoriaiv or 0),
                    "lat": float(peaje.latitud),
                    "lon": float(peaje.longitud)
                })
                costo_total_peajes += int(peaje.categoriaiv or 0)

        return peajes_en_ruta, costo_total_peajes

    def obtener_mejores_camiones_para_flete(self, cod_flete):
        """
        Lógica principal de asignación.
        Incluye sistema de puntos y ordena por (puntos_conductor, costo_total).
        """
        flete = Flete.query.filter_by(cod_flete=cod_flete).first()
        if not flete:
            return {"error": "Flete no encontrado"}

        origen = (flete.origen_lat, flete.origen_lon)
        destino = (flete.destino_lat, flete.destino_lon)

        vehiculos_disponibles = Vehiculo.query.filter_by(estado='Disponible').all()
        resultados = []

        for v in vehiculos_disponibles:
            conductor = Conductor.query.filter_by(cod_empleado=v.cod_conductor_actual).first()
            nombre_conductor = conductor.nombre if conductor else "No asignado"
            licencia_conductor = conductor.licencia if conductor else "N/A"
            puntos_conductor = conductor.puntos if conductor else 18

            pos_camion = (v.latitud, v.longitud)
            dist_a_origen = self.servicio_ruta.obtener_ruta_camion(pos_camion, origen)
            dist_viaje = self.servicio_ruta.obtener_ruta_camion(origen, destino)

            if not dist_a_origen or not dist_viaje:
                continue

            # Costos de combustible (vacío + cargado)
            distancia_total_km = (dist_a_origen['distance'] + dist_viaje['distance']) / 1000.0
            costo_combustible = distancia_total_km * self.consumo_por_km * self.precio_diesel

            # Peajes
            peajes_vacio, costo_peajes_vacio = self.obtener_peajes_en_ruta(dist_a_origen.get('points', []))
            peajes_viaje, costo_peajes_viaje = self.obtener_peajes_en_ruta(dist_viaje.get('points', []))
            costo_total_peajes = costo_peajes_vacio + costo_peajes_viaje
            peajes_totales_lista = peajes_vacio + peajes_viaje

            # Costos fijos
            val_cargue = float(flete.valor_cargue or 0)
            val_descargue = float(flete.valor_descargue or 0)
            val_escolta = float(flete.valor_escolta or 0)
            val_viaticos = float(flete.viaticos_estimados or 0)
            costos_fijos = val_cargue + val_descargue + val_escolta + val_viaticos
            costo_total = costo_combustible + costos_fijos + costo_total_peajes

            dist_vacio_km = round(dist_a_origen['distance'] / 1000, 2)
            dist_viaje_km = round(dist_viaje['distance'] / 1000, 2)
            tiempo_min = round((dist_a_origen['time'] + dist_viaje['time']) / 60000, 2)

            resultados.append({
                "cod_vehiculo": v.cod_vehiculo,
                "placa": v.placa,
                "marca": v.marca,
                "conductor": nombre_conductor,
                "licencia": licencia_conductor,
                "puntos_conductor": puntos_conductor,   # Para el sistema de puntos
                "km_actual": v.km_actual or 0,
                "km_proximo_aceite": v.km_proximo_aceite or 0,
                "estado_llantas": v.estado_llantas or "Bueno",
                "distancia_vacio": dist_vacio_km,
                "distancia_viaje": dist_viaje_km,
                "costo_combustible": round(costo_combustible, 2),
                "valor_cargue": val_cargue,
                "valor_descargue": val_descargue,
                "valor_escolta": val_escolta,
                "viaticos_estimados": val_viaticos,
                "peajes": peajes_totales_lista,
                "costo_peajes": costo_total_peajes,
                "costo_peajes_vacio": costo_peajes_vacio,
                "costos_fijos": round(costos_fijos, 2),
                "costo_total": round(costo_total, 2),
                "tiempo_total_min": tiempo_min,
                "route_vacio_points": dist_a_origen.get('points', []),
                "route_points": dist_viaje.get('points', []),
                "truck_pos": [float(v.latitud or 0), float(v.longitud or 0)],
                # Costos para persistir en historial al asignar
                "_costos": {
                    "dist_vacio_km": dist_vacio_km,
                    "dist_viaje_km": dist_viaje_km,
                    "tiempo_min": tiempo_min,
                    "costo_combustible": round(costo_combustible, 2),
                    "costo_peajes": costo_total_peajes,
                    "costos_fijos": round(costos_fijos, 2),
                    "costo_total": round(costo_total, 2)
                }
            })

        # Ordenar: primero por puntos (menos puntos primero), luego por costo
        resultados.sort(key=lambda x: (x['puntos_conductor'], x['costo_total']))

        return {
            "flete": {
                "cod_flete": flete.cod_flete,
                "cliente": flete.cliente,
                "producto": flete.producto,
                "peso": float(flete.peso_carga or 0),
                "punto_carga": flete.punto_carga if flete.punto_carga else f"Coords: {flete.origen_lat}, {flete.origen_lon}",
                "origen": f"{flete.origen_lat}, {flete.origen_lon}",
                "destino": f"{flete.destino_lat}, {flete.destino_lon}",
                "valor_cargue": float(flete.valor_cargue or 0),
                "valor_descargue": float(flete.valor_descargue or 0),
                "viaticos": float(flete.viaticos_estimados or 0),
                "escolta": float(flete.valor_escolta or 0)
            },
            "recommendations": resultados[:3]
        }
