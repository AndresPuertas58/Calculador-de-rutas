from sqlalchemy import Column, Integer, ForeignKey, DECIMAL, Text, TIMESTAMP, JSON, Enum
from sqlalchemy.sql import func
from database import Base


class RutaEnvio(Base):
    __tablename__ = "rutas_envio"

    id = Column(Integer, primary_key=True, index=True)

    envio_id = Column(Integer, ForeignKey("envios.id"), nullable=False)
    camion_id = Column(Integer, ForeignKey("camiones.id"), nullable=False)
    polyline = Column(JSON)
    distancia_km = Column(DECIMAL(10, 2), nullable=False)
    tiempo_seg = Column(Integer, nullable=False)
    costo_acpm = Column(DECIMAL(12, 2), nullable=False)
    costo_peajes = Column(DECIMAL(12, 2), nullable=False)
    costo_total = Column(DECIMAL(12, 2), nullable=False)
    tipo_opcion = Column(
        Enum("optima", "rapida", "alternativa"),
        default="optima"
    )
    created_at = Column(TIMESTAMP, server_default=func.now())
    asignada = Column(Integer, nullable=False, default=0, server_default='0')