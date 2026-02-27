from flask import Flask, send_file, jsonify
from database import SessionLocal
from service.servicio_camion import mostrar_todos_camiones_osm
from service.servicio_peajes import mostrar_todos_peajes_osm
from service.servicio_envio import asignar_camion_a_envio
 

app = Flask(__name__)

@app.route("/ver_camiones", methods=["GET"])
def ver_camiones():
    db = SessionLocal()
    try:
        mostrar_todos_camiones_osm(db)
        return send_file("posiciones.html")
    finally:
        db.close()


@app.route("/ver_peajes", methods=["GET"])
def ver_peajes():
    db = SessionLocal()
    try:
        mostrar_todos_peajes_osm(db)
        return send_file("peajes.html")
    finally:
        db.close()


@app.route("/envios/<int:envio_id>/asignar_camion", methods=["POST"])
def asignar_camion(envio_id):
    db = SessionLocal()
    try:
        resultado = asignar_camion_a_envio(db, envio_id)

        if not resultado:
            return jsonify({"error": "No hay camiones disponibles"}), 404

        return jsonify(resultado), 200
    finally:
        db.close()




if __name__ == "__main__":
    app.run(debug=True, port=5068, host="0.0.0.0")