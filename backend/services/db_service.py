from models.database import db, Conductor, Vehiculo, Flete, AsignacionHistorial
from datetime import datetime


class ServicioBaseDatos:

    def obtener_todos_los_conductores(self):
        return Conductor.query.all()

    def obtener_vehiculo_por_id(self, cod_vehiculo):
        return Vehiculo.query.filter_by(cod_vehiculo=cod_vehiculo).first()

    def obtener_flete_por_id(self, cod_flete):
        return Flete.query.filter_by(cod_flete=cod_flete).first()

    def obtener_fletes_pendientes(self):
        return Flete.query.filter_by(estado='sin_asignar').all()

    def obtener_datos_dashboard(self):
        fletes = Flete.query.all()
        resultado = []
        for f in fletes:
            datos_flete = {
                "cod_flete": f.cod_flete,
                "cliente": f.cliente,
                "producto": f.producto,
                "peso": float(f.peso_carga) if f.peso_carga else 0,
                "punto_carga": f.punto_carga if f.punto_carga else f"Coords: {f.origen_lat}, {f.origen_lon}",
                "estado": f.estado,
                "venta": float(f.venta) if f.venta else 0,
                "vehiculo": None
            }
            if f.vehiculo:
                datos_flete["vehiculo"] = {
                    "placa": f.vehiculo.placa,
                    "marca": f.vehiculo.marca,
                    "estado": f.vehiculo.estado,
                    "lat": float(f.vehiculo.latitud) if f.vehiculo.latitud else 0,
                    "lon": float(f.vehiculo.longitud) if f.vehiculo.longitud else 0
                }
            resultado.append(datos_flete)
        return resultado

    def obtener_datos_conductores(self):
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

    def obtener_datos_vehiculos(self):
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
                "lat": float(v.latitud) if v.latitud else None,
                "lon": float(v.longitud) if v.longitud else None,
                "flete_activo": flete_info
            })
        return resultado

    def asignar_camion_a_flete(self, cod_flete, cod_vehiculo, costos=None):
        """
        Asigna un vehículo a un flete, acumula puntos al conductor
        y persiste los costos en AsignacionHistorial.

        costos: dict opcional con keys:
            dist_vacio_km, dist_viaje_km, tiempo_min,
            costo_combustible, costo_peajes, costos_fijos, costo_total
        """
        flete = Flete.query.filter_by(cod_flete=cod_flete).first()
        vehiculo = Vehiculo.query.filter_by(cod_vehiculo=cod_vehiculo).first()

        if not flete or not vehiculo:
            return False, "Flete o Vehículo no encontrado"

        conductor = Conductor.query.filter_by(
            cod_empleado=vehiculo.cod_conductor_actual
        ).first()

        try:
            # --- Sistema de puntos ---
            if costos and costos.get('dist_viaje_km', 0) > 0:
                dist_viaje_km = costos['dist_viaje_km']
                puntos_ganados = int(dist_viaje_km // 450) * 1  # +1 pt por cada 450 km
                if puntos_ganados > 0 and conductor:
                    conductor.puntos = min((conductor.puntos or 0) + puntos_ganados, 18)

            # --- Persistir historial ---
            historial_existente = AsignacionHistorial.query.filter_by(cod_flete=cod_flete).first()
            if historial_existente:
                db.session.delete(historial_existente)

            historial = AsignacionHistorial(
                cod_flete=cod_flete,
                cod_vehiculo=cod_vehiculo,
                placa=vehiculo.placa,
                conductor=conductor.nombre if conductor else "No asignado",
                fecha_asignacion=datetime.utcnow(),
                distancia_vacio_km=costos.get('dist_vacio_km', 0) if costos else 0,
                distancia_viaje_km=costos.get('dist_viaje_km', 0) if costos else 0,
                tiempo_total_min=costos.get('tiempo_min', 0) if costos else 0,
                costo_combustible=costos.get('costo_combustible', 0) if costos else 0,
                costo_peajes=costos.get('costo_peajes', 0) if costos else 0,
                costos_fijos=costos.get('costos_fijos', 0) if costos else 0,
                costo_total=costos.get('costo_total', 0) if costos else 0,
                venta=float(flete.venta or 0)
            )
            db.session.add(historial)

            # --- Actualizar estado ---
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

    def desasignar_camion_de_flete(self, cod_flete):
        """Libera el vehículo y elimina el registro del historial."""
        flete = Flete.query.filter_by(cod_flete=cod_flete).first()
        if not flete:
            return False, "Flete no encontrado"
        if not flete.cod_vehiculo_asignado:
            return False, "El flete no tiene vehículo asignado"

        try:
            vehiculo = Vehiculo.query.filter_by(cod_vehiculo=flete.cod_vehiculo_asignado).first()
            if vehiculo:
                vehiculo.estado = 'Disponible'
                vehiculo.cod_flete_activo = None

            # Eliminar historial al desasignar
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

    def obtener_reporte(self):
        """Retorna todos los fletes asignados con sus costos y venta desde el historial."""
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
