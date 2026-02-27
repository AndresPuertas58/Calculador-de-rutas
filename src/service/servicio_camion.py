from sqlalchemy.orm import Session
from models.camion import Camion
import webbrowser
import os, folium
from folium.plugins import MarkerCluster

import models 

def mostrar_todos_camiones_osm(db):
    camiones = db.query(Camion).all()

    mapa = folium.Map(
        location=[4.65, -74.1],  
        zoom_start=6
    )

    cluster = MarkerCluster(camiones="Camiones").add_to(mapa)

    for c in camiones:
        color = "green" if c.estado == "disponible" else "red"

        folium.Marker(
            location=[c.latitud, c.longitud],
            tooltip=f"Camión {c.placa}",
            popup=f"""
                <b>Placa:</b> {c.placa}<br>
                <b>Estado:</b> {c.estado}<br>
            """,
            icon=folium.Icon(
                color=color,
                icon="truck",
                prefix="fa"
            )
        ).add_to(cluster)

    mapa.save("posiciones.html")