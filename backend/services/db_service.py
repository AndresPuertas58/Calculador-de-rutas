from models.database import db, Conductor, Vehiculo, Flete

class ServicioBaseDatos:
    def obtener_todos_los_conductores(self):
        return Conductor.query.all()

    def obtener_vehiculo_por_id(self, cod_vehiculo):
        return Vehiculo.query.get(cod_vehiculo)

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
            "origen_ciudad": c.origen_ciudad or "N/A",
            "telefono": c.telefono or "N/A",
            "licencia": c.licencia or "C3",
            "vacaciones": f"{c.vacaciones_inicio} a {c.vacaciones_fin}" if c.vacaciones_inicio else "Activo",
            "incapacidad": f"{c.incapacidad_inicio} a {c.incapacidad_fin}" if c.incapacidad_inicio else "No",
            "vehiculo_habitual": c.cod_vehiculo_habitual or "Sin asignar"
        } for c in conductores]

    def obtener_datos_vehiculos(self):
        vehiculos = Vehiculo.query.all()
        return [{
            "cod_vehiculo": v.cod_vehiculo,
            "placa": v.placa,
            "marca": v.marca or "N/A",
            "color": v.color or "N/A",
            "tipo_plancha": v.tipo_plancha or "N/A",
            "estado": v.estado or "Disponible",
            "lat": float(v.latitud) if v.latitud else None,
            "lon": float(v.longitud) if v.longitud else None,
            "flete_activo": v.cod_flete_activo or "Ninguno"
        } for v in vehiculos]

    def asignar_camion_a_flete(self, cod_flete, cod_vehiculo):
        """
        Actualiza el flete con el vehículo seleccionado y cambia su estado.
        """
        flete = Flete.query.get(cod_flete)
        vehiculo = Vehiculo.query.get(cod_vehiculo)
        
        if not flete or not vehiculo:
            return False, "Flete o Vehículo no encontrado"
            
        try:
            # 1. Asignar vehículo al flete
            flete.cod_vehiculo_asignado = cod_vehiculo
            flete.estado = 'asignado'
            
            # 2. Cambiar estado del vehículo
            vehiculo.estado = 'En Ruta'
            
            db.session.commit()
            return True, "Asignación exitosa"
        except Exception as e:
            db.session.rollback()
            return False, str(e)

    def desasignar_camion_de_flete(self, cod_flete):
        """
        Desasigna el vehículo de un flete.
        """
        flete = Flete.query.get(cod_flete)
        if not flete:
            return False, "Flete no encontrado"
        if not flete.cod_vehiculo_asignado:
            return False, "El flete no tiene vehículo asignado"

        try:
            vehiculo = Vehiculo.query.get(flete.cod_vehiculo_asignado)
            if vehiculo:
                vehiculo.estado = 'Disponible'
                vehiculo.cod_flete_activo = None
            
            flete.cod_vehiculo_asignado = None
            flete.estado = 'sin_asignar'
            db.session.commit()
            return True, "Desasignación exitosa"
        except Exception as e:
            db.session.rollback()
            return False, str(e)
