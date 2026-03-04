from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Conductor(db.Model):
    __tablename__ = 'conductores'
    cod_empleado = db.Column(db.String(15), primary_key=True)
    cedula = db.Column(db.String(20), unique=True, nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    cod_vehiculo_habitual = db.Column(db.String(15))
    origen_ciudad = db.Column(db.String(50))
    telefono = db.Column(db.String(20))
    # Nuevos campos sugeridos para RRHH
    licencia = db.Column(db.String(10), default='C3')
    vacaciones_inicio = db.Column(db.Date)
    vacaciones_fin = db.Column(db.Date)
    incapacidad_inicio = db.Column(db.Date)
    incapacidad_fin = db.Column(db.Date)

class Vehiculo(db.Model):
    __tablename__ = 'vehiculos'
    cod_vehiculo = db.Column(db.String(15), primary_key=True)
    placa = db.Column(db.String(10), unique=True, nullable=False)
    color = db.Column(db.String(30))
    marca = db.Column(db.String(50))
    tipo_plancha = db.Column(db.String(50), default='Patineta')
    categoria = db.Column(db.Integer)
    consumo_km = db.Column(db.Numeric(10, 2))
    cod_conductor_actual = db.Column(db.String(15), db.ForeignKey('conductores.cod_empleado'))
    estado = db.Column(db.String(20), default='Disponible')
    latitud = db.Column(db.Numeric(10, 7))
    longitud = db.Column(db.Numeric(10, 7))
    cod_flete_activo = db.Column(db.String(20))

class Flete(db.Model):
    __tablename__ = 'fletes'
    cod_flete = db.Column(db.String(20), primary_key=True)
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
    estado = db.Column(db.Enum('asignado', 'sin_asignar'), default='sin_asignar')
    cod_vehiculo_asignado = db.Column(db.String(15), db.ForeignKey('vehiculos.cod_vehiculo'))
    cod_empleado_asignado = db.Column(db.String(15), db.ForeignKey('conductores.cod_empleado'))

    # Relationships
    vehiculo = db.relationship('Vehiculo', backref='fletes')
    conductor = db.relationship('Conductor', backref='fletes')

class Peaje(db.Model):
    __tablename__ = 'peajes'
    id = db.Column(db.Integer, primary_key=True)
    nombrepeaje = db.Column(db.String(100))
    latitud = db.Column(db.Numeric(10, 8))
    longitud = db.Column(db.Numeric(11, 8))
    categoriaiv = db.Column(db.Integer) # Categoría para camiones segun el usuario
    sector = db.Column(db.String(100))
    sentido = db.Column(db.String(100))
