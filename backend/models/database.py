from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Conductor(db.Model):
    __tablename__ = 'conductores'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    cod_empleado = db.Column(db.String(15), unique=True, nullable=False)
    cedula = db.Column(db.String(20), unique=True, nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    cod_vehiculo_habitual = db.Column(db.String(15))
    origen_ciudad = db.Column(db.String(50))
    telefono = db.Column(db.String(20))
    licencia = db.Column(db.String(10), default='C3')
    estado_operativo = db.Column(db.Enum('Activo', 'Vacaciones', 'Incapacidad', 'Retirado'), default='Activo')
    vacaciones_inicio = db.Column(db.Date)
    vacaciones_fin = db.Column(db.Date)
    incapacidad_inicio = db.Column(db.Date)
    incapacidad_fin = db.Column(db.Date)
    puntos = db.Column(db.Integer, default=0)   # Sistema de puntos por km recorridos


class PuntoParqueo(db.Model):
    """
    Sede/base donde los vehículos están estacionados cuando están disponibles.
    El algoritmo de enrutamiento toma las coordenadas de este modelo
    en lugar de las del vehículo directamente.
    """
    __tablename__ = 'puntos_parqueo'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sede = db.Column(db.String(100), nullable=False)
    direccion = db.Column(db.String(200))
    telefono = db.Column(db.String(20))
    correo = db.Column(db.String(100))
    latitud = db.Column(db.Numeric(10, 7), nullable=False)
    longitud = db.Column(db.Numeric(10, 7), nullable=False)


class Vehiculo(db.Model):
    __tablename__ = 'vehiculos'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    cod_vehiculo = db.Column(db.String(15), unique=True, nullable=False)
    placa = db.Column(db.String(10), unique=True, nullable=False)
    color = db.Column(db.String(30))
    marca = db.Column(db.String(50))
    tipo_plancha = db.Column(db.String(50), default='Patineta')
    categoria = db.Column(db.Integer)
    consumo_km = db.Column(db.Numeric(10, 2))
    km_actual = db.Column(db.Integer, default=0)
    km_proximo_aceite = db.Column(db.Integer, default=0)
    fecha_ultimo_preventivo = db.Column(db.Date)
    estado_llantas = db.Column(db.Enum('Bueno', 'Regular', 'Crítico'), default='Bueno')
    cod_conductor_actual = db.Column(db.String(15), db.ForeignKey('conductores.cod_empleado'))
    estado = db.Column(db.String(20), default='Disponible')
    latitud = db.Column(db.Numeric(10, 7))    # Reservado / no se usa en el algoritmo
    longitud = db.Column(db.Numeric(10, 7))   # Reservado / no se usa en el algoritmo
    cod_flete_activo = db.Column(db.String(20))
    id_punto_parqueo = db.Column(db.Integer, db.ForeignKey('puntos_parqueo.id'), nullable=True)

    punto_parqueo = db.relationship('PuntoParqueo', backref='vehiculos')


class Flete(db.Model):
    __tablename__ = 'fletes'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    cod_flete = db.Column(db.String(20), unique=True, nullable=False)
    cliente = db.Column(db.String(100))
    producto = db.Column(db.String(50))
    peso_carga = db.Column(db.Numeric(10, 2))
    punto_carga = db.Column(db.String(100))
    origen_lat = db.Column(db.Numeric(10, 7))
    origen_lon = db.Column(db.Numeric(10, 7))
    destino_lat = db.Column(db.Numeric(10, 7))
    destino_lon = db.Column(db.Numeric(10, 7))
    valor_cargue = db.Column(db.Numeric(15, 2))
    valor_descargue = db.Column(db.Numeric(15, 2))
    valor_escolta = db.Column(db.Numeric(15, 2), default=0)
    viaticos_estimados = db.Column(db.Numeric(15, 2))
    venta = db.Column(db.Numeric(15, 2), default=0)   # Valor de venta del servicio
    estado = db.Column(db.Enum('asignado', 'sin_asignar'), default='sin_asignar')
    cod_vehiculo_asignado = db.Column(db.String(15), db.ForeignKey('vehiculos.cod_vehiculo'))
    cod_empleado_asignado = db.Column(db.String(15), db.ForeignKey('conductores.cod_empleado'))

    # Relationships
    vehiculo = db.relationship('Vehiculo', backref='fletes', foreign_keys=[cod_vehiculo_asignado])
    conductor = db.relationship('Conductor', backref='fletes', foreign_keys=[cod_empleado_asignado])


class AsignacionHistorial(db.Model):
    """
    Persiste los costos calculados al momento de la asignación.
    Se crea al asignar un flete y se elimina al desasignar.
    """
    __tablename__ = 'asignaciones_historial'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    cod_flete = db.Column(db.String(20), db.ForeignKey('fletes.cod_flete'), unique=True, nullable=False)
    cod_vehiculo = db.Column(db.String(15))
    placa = db.Column(db.String(10))
    conductor = db.Column(db.String(100))
    fecha_asignacion = db.Column(db.DateTime, default=datetime.utcnow)
    distancia_vacio_km = db.Column(db.Numeric(10, 2))
    distancia_viaje_km = db.Column(db.Numeric(10, 2))
    tiempo_total_min = db.Column(db.Numeric(10, 2))
    costo_combustible = db.Column(db.Numeric(15, 2))
    costo_peajes = db.Column(db.Numeric(15, 2))
    costos_fijos = db.Column(db.Numeric(15, 2))
    costo_total = db.Column(db.Numeric(15, 2))
    venta = db.Column(db.Numeric(15, 2))

    flete = db.relationship('Flete', backref=db.backref('historial', uselist=False))


class Peaje(db.Model):
    __tablename__ = 'peajes'
    id = db.Column(db.Integer, primary_key=True)
    nombrepeaje = db.Column(db.String(100))
    latitud = db.Column(db.Numeric(10, 8))
    longitud = db.Column(db.Numeric(11, 8))
    categoriaiv = db.Column(db.Integer)
    sector = db.Column(db.String(100))
    sentido = db.Column(db.String(100))
