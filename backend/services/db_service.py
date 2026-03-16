from models.database import Flete

class ServicioBaseDatos:

    def obtener_datos_fletes(self):
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
                "vehiculo": None,
                "destino": f.destino
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
