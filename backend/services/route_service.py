import requests

class RouteService:
    def __init__(self):
        # Actualizado al nuevo puerto 8991
        self.gh_url = "http://localhost:8991/route"

    def get_truck_route(self, origin, destination):
        """
        Calcula la ruta entre origen y destino usando GraphHopper.
        Retorna la distancia en metros y el tiempo en milisegundos.
        """
        if not origin or not destination:
            return None
            
        params = {
            "point": [f"{origin[0]},{origin[1]}", f"{destination[0]},{destination[1]}"],
            "profile": "truck",
            "locale": "es",
            "calc_points": "true", # Ahora necesitamos los puntos para la geometría
            "points_encoded": "false"
        }
        
        try:
            response = requests.get(self.gh_url, params=params)
            if response.status_code == 200:
                data = response.json()
                path = data['paths'][0]
                return {
                    "distance": path['distance'], # en metros
                    "time": path['time'],         # en milisegundos
                    "points": path['points']['coordinates'] # Lista de [lon, lat]
                }
            return None
        except Exception as e:
            print(f"Error en GraphHopper: {e}")
            return None
