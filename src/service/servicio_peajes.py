from sqlalchemy.orm import Session
from models.peaje import Peaje
import folium
from folium.plugins import MarkerCluster

def mostrar_todos_peajes_osm(db: Session):
    peajes = db.query(Peaje).all()

    mapa = folium.Map(
        location=[4.65, -74.1],  
        zoom_start=6.
    )
    
    cluster = MarkerCluster(name="Peajes").add_to(mapa)

    for p in peajes:
        
        if not p.latitud or not p.longitud:
            continue

        folium.Marker(
            location=[float(p.latitud), float(p.longitud)],
            tooltip=f"Peaje: {p.nombrepeaje}",
            popup=f"""
                <b>Nombre:</b> {p.nombrepeaje}<br>
                <b>Sector:</b> {p.sector}<br>
                <b>Ubicación:</b> {p.ubicacion}<br>
                <b>Responsable:</b> {p.responsable}<br>
                <b>Teléfono:</b> {p.telefonopeaje}<br>
            """,
            icon=folium.Icon(
                color="blue",
                icon="road",
                prefix="fa"
            )
        ).add_to(cluster)

    mapa.save("peajes.html")
