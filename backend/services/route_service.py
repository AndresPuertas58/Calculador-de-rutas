import requests
import os

class ServicioRuta:
    def __init__(self):
        # Lee la URL de GraphHopper desde env (docker-compose define http://graphhopper:8991)
        # En desarrollo local sin Docker, el fallback es localhost:8991
        base_url = os.getenv("GRAPHHOPPER_URL", "http://localhost:8991")
        self.url_graphhopper = f"{base_url.rstrip('/')}/route"

    def obtener_ruta_camion(self, origen, destino):
        """
        Calcula la ruta entre origen y destino usando GraphHopper.
        Retorna la distancia en metros, el tiempo en milisegundos y los puntos de la ruta.
        """
        if not origen or not destino:
            return None
            
        parametros = {
            "point": [f"{origen[0]},{origen[1]}", f"{destino[0]},{destino[1]}"],
            "profile": "truck",
            "locale": "es",
            "calc_points": "true",
            "points_encoded": "false"
        }
        
        try:
            respuesta = requests.get(self.url_graphhopper, params=parametros)
            if respuesta.status_code == 200:
                datos = respuesta.json()
                trayecto = datos['paths'][0]
                return {
                    "distance": trayecto['distance'], # mantenemos llaves de GraphHopper o mapeamos? Mapeamos para consistencia.
                    "time": trayecto['time'],
                    "points": trayecto['points']['coordinates']
                }
            return None
        except Exception as e:
            print(f"Error en GraphHopper: {e}")
            return None
