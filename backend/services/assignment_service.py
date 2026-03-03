from services.route_service import RouteService
from models.database import Flete, Vehiculo, db
import os

class AssignmentService:
    def __init__(self):
        self.route_service = RouteService()
        # Precio del diésel aproximado en Colombia (~9500 COP)
        self.diesel_price = float(os.getenv('DIESEL_PRICE', 10885))
        # Consumo litros por km pedido por el usuario
        self.consumption_per_km = 0.35 

    def get_tolls_on_route(self, points):
        """
        Detecta qué peajes están en la ruta.
        Recibe una lista de puntos [[lon, lat], ...]
        """
        if not points:
            return [], 0
            
        from models.database import Peaje
        import math

        # 1. Obtener Bounding Box para filtrar peajes inicialmente
        lats = [p[1] for p in points]
        lons = [p[0] for p in points]
        min_lat, max_lat = min(lats) - 0.01, max(lats) + 0.01
        min_lon, max_lon = min(lons) - 0.01, max(lons) + 0.01

        # 2. Consultar peajes candidatos en el área
        candidatos = Peaje.query.filter(
            Peaje.latitud.between(min_lat, max_lat),
            Peaje.longitud.between(min_lon, max_lon)
        ).all()

        peajes_en_ruta = []
        total_peajes_costo = 0
        
        # Umbral de cercanía (~100 metros)
        threshold = 0.0009 

        for peaje in candidatos:
            p_lat = float(peaje.latitud)
            p_lon = float(peaje.longitud)
            
            # Verificar si algún punto de la ruta está cerca del peaje
            is_near = False
            for pt in points:
                # Distancia euclidiana simple (suficiente para distancias muy cortas)
                dist = math.sqrt((p_lat - pt[1])**2 + (p_lon - pt[0])**2)
                if dist < threshold:
                    is_near = True
                    break
            
            if is_near:
                peajes_en_ruta.append({
                    "nombre": peaje.nombrepeaje,
                    "costo": int(peaje.categoriaiv or 0)
                })
                total_peajes_costo += int(peaje.categoriaiv or 0)

        return peajes_en_ruta, total_peajes_costo

    def get_best_trucks_for_flete(self, cod_flete):
        """
        Lógica principal de asignación mejorada con Peajes.
        """
        flete = Flete.query.get(cod_flete)
        if not flete:
            return {"error": "Flete no encontrado"}

        origin = (flete.origen_lat, flete.origen_lon)
        destination = (flete.destino_lat, flete.destino_lon)

        vehiculos_disponibles = Vehiculo.query.filter_by(estado='Disponible').all()
        results = []

        for v in vehiculos_disponibles:
            truck_pos = (v.latitud, v.longitud)
            dist_to_origin = self.route_service.get_truck_route(truck_pos, origin)
            dist_trip = self.route_service.get_truck_route(origin, destination)

            if not dist_to_origin or not dist_trip:
                continue

            # Cálculo de Combustible
            distancia_total_km = (dist_to_origin['distance'] + dist_trip['distance']) / 1000.0
            costo_combustible = distancia_total_km * self.consumption_per_km * self.diesel_price
            
            # Cálculo de Peajes (solo en el viaje cargado)
            peajes_lista, costo_peajes = self.get_tolls_on_route(dist_trip.get('points', []))

            # Costos fijos
            val_cargue = float(flete.valor_cargue or 0)
            val_descargue = float(flete.valor_descargue or 0)
            val_escolta = float(flete.valor_escolta or 0)
            val_viaticos = float(flete.viaticos_estimados or 0)
            
            costos_fijos = val_cargue + val_descargue + val_escolta + val_viaticos
            costo_total = costo_combustible + costos_fijos + costo_peajes

            results.append({
                "cod_vehiculo": v.cod_vehiculo,
                "placa": v.placa,
                "marca": v.marca,
                "distancia_vacio": round(dist_to_origin['distance'] / 1000, 2),
                "distancia_viaje": round(dist_trip['distance'] / 1000, 2),
                "costo_combustible": round(costo_combustible, 2),
                "valor_cargue": val_cargue,
                "valor_descargue": val_descargue,
                "valor_escolta": val_escolta,
                "viaticos_estimados": val_viaticos,
                "peajes": peajes_lista,
                "costo_peajes": costo_peajes,
                "costos_fijos": round(costos_fijos, 2),
                "costo_total": round(costo_total, 2),
                "tiempo_total_min": round((dist_to_origin['time'] + dist_trip['time']) / 60000, 2),
                "route_vacio_points": dist_to_origin.get('points', []), # Path Truck -> Origin
                "route_points": dist_trip.get('points', []), # Path Origin -> Destination
                "truck_pos": [v.latitud, v.longitud]
            })

        results.sort(key=lambda x: x['costo_total'])
        
        # Retornar objeto enriquecido con info del flete
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
            "recommendations": results[:3]
        }
