import folium
import json
from folium.plugins import MarkerCluster

def generar_mapa_ruta(
    ruta,
    costos,
    camion,
    punto_carga,
    destino,
    peajes,
    archivo,
    opciones_extra=[]
):
    centro = [punto_carga.latitud, punto_carga.longitud]
    mapa = folium.Map(location=centro, zoom_start=6, tiles="OpenStreetMap")

    colores_extra = ["green", "orange"]
    nombres_grupo = ["🟢 Más rápida", "🟠 Alternativa económica"]

    # ── Construir todos los grupos ─────────────────────────────────────────
    todas_opciones = [
        {
            "nombre": "🔵 Óptima (menor costo)",
            "color": "blue",
            "camion": camion,
            "ruta": ruta,
            "costos": costos,
            "show": True
        }
    ] + [
        {
            "nombre": nombres_grupo[i],
            "color": colores_extra[i],
            "camion": op["camion"],
            "ruta": op["ruta"],
            "costos": op["costos"],
            "show": False
        }
        for i, op in enumerate(opciones_extra)
    ]

    grupos = []
    for opcion in todas_opciones:
        grupo = folium.FeatureGroup(name=opcion["nombre"], show=opcion["show"]).add_to(mapa)

        folium.PolyLine(
            locations=[(lat, lon) for lon, lat in opcion["ruta"]["polyline"]],
            color=opcion["color"],
            weight=5 if opcion["show"] else 3,
            opacity=0.85,
            tooltip=opcion["nombre"]
        ).add_to(grupo)

        folium.Marker(
            location=[opcion["camion"].latitud, opcion["camion"].longitud],
            icon=folium.Icon(color=opcion["color"], icon="truck", prefix="fa"),
            popup=f"""
            <b>🚛 {opcion['nombre']}</b><br>
            Placa: {opcion['camion'].placa}<br>
            📏 {opcion['ruta']['distancia_km']:.1f} km &nbsp;|&nbsp;
            ⏱️ {opcion['ruta']['tiempo_seg']/3600:.1f} h<br>
            💸 ACPM: ${opcion['costos']['acpm']:,.0f}<br>
            🛣️ Peajes: ${opcion['costos']['peajes']:,.0f}<br>
            <b>💰 Total: ${opcion['costos']['total']:,.0f}</b>
            """
        ).add_to(grupo)

        grupos.append(opcion["nombre"])

    # ── Marcadores fijos ───────────────────────────────────────────────────
    folium.Marker(
        location=[punto_carga.latitud, punto_carga.longitud],
        icon=folium.Icon(color="darkblue", icon="warehouse", prefix="fa"),
        popup=f"<b>📦 Punto de carga</b><br>Ciudad: {punto_carga.ciudad}"
    ).add_to(mapa)

    folium.Marker(
        location=[destino.latitud, destino.longitud],
        icon=folium.Icon(color="red", icon="flag-checkered", prefix="fa"),
        popup=f"<b>📍 Destino</b><br>Envío ID: {destino.id}"
    ).add_to(mapa)

    # ── Peajes ─────────────────────────────────────────────────────────────
    grupo_peajes = folium.FeatureGroup(name="🛣️ Peajes", show=True).add_to(mapa)
    cluster_peajes = MarkerCluster().add_to(grupo_peajes)
    for p in peajes:
        folium.CircleMarker(
            location=[float(p.latitud), float(p.longitud)],
            radius=4, color="orange", fill=True, fill_opacity=0.7,
            popup=f"<b>🛣️ {p.nombrepeaje}</b><br>Cat. I: ${p.categoriai:,.0f}"
        ).add_to(cluster_peajes)

    folium.LayerControl(collapsed=False).add_to(mapa)

    # ── JS: comportamiento radio button ───────────────────────────────────
    nombres_js = json.dumps(grupos)  # ["🔵 Óptima...", "🟢 Más rápida", ...]

    radio_js = f"""
    <script>
    document.addEventListener("DOMContentLoaded", function() {{
        const nombresRutas = {nombres_js};

        // Esperar a que Leaflet y el LayerControl estén listos
        setTimeout(function() {{
            const checkboxes = document.querySelectorAll(
                ".leaflet-control-layers-overlays input[type=checkbox]"
            );

            // Mapear cada checkbox a su nombre de capa
            checkboxes.forEach(function(cb) {{
                const label = cb.parentElement.querySelector("span").textContent.trim();
                if (!nombresRutas.includes(label)) return;  // ignorar peajes

                cb.addEventListener("change", function() {{
                    if (!cb.checked) return;  // solo actuar al activar

                    // Desactivar los otros checkboxes de rutas
                    checkboxes.forEach(function(other) {{
                        const otherLabel = other.parentElement.querySelector("span").textContent.trim();
                        if (other !== cb && nombresRutas.includes(otherLabel) && other.checked) {{
                            other.click();  // dispara el toggle de Leaflet
                        }}
                    }});
                }});
            }});
        }}, 500);
    }});
    </script>
    """

    mapa.get_root().html.add_child(folium.Element(radio_js))

    # ── Panel resumen ──────────────────────────────────────────────────────
    filas_alternativas = ""
    for i, opcion in enumerate(opciones_extra):
        color = colores_extra[i % len(colores_extra)]
        filas_alternativas += f"""
        <hr style="margin:8px 0;">
        <span style="color:{color}; font-size:16px;">●</span>
        <b>{opcion['etiqueta']}</b><br>
        🚛 {opcion['camion'].placa} &nbsp;|&nbsp;
        📏 {opcion['ruta']['distancia_km']:.1f} km &nbsp;|&nbsp;
        ⏱️ {opcion['ruta']['tiempo_seg']/3600:.1f} h<br>
        💰 Total: ${opcion['costos']['total']:,.0f}<br>
        """

    resumen_html = f"""
    <div style="
        position: fixed; bottom: 30px; left: 30px; width: 300px;
        background: white; padding: 15px; border-radius: 10px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.3); z-index: 9999; font-size: 14px;
    ">
        <h4 style="margin: 0 0 10px 0;">📊 Resumen del envío</h4>
        <span style="color:blue; font-size:16px;">●</span> <b>Óptima (menor costo)</b><br>
        🚛 {camion.placa} &nbsp;|&nbsp;
        📏 {ruta["distancia_km"]:.1f} km &nbsp;|&nbsp;
        ⏱️ {ruta["tiempo_seg"]/3600:.1f} h<br>
        💸 ACPM: ${costos["acpm"]:,.0f}<br>
        🛣️ Peajes: ${costos["peajes"]:,.0f}<br>
        💰 <b>Total: ${costos["total"]:,.0f}</b>
        {filas_alternativas}
    </div>
    """
    mapa.get_root().html.add_child(folium.Element(resumen_html))

    mapa.save(archivo)
    return archivo