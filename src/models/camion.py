from sqlalchemy import Column, Integer, String, DECIMAL, Enum
from sqlalchemy.orm import relationship
from database import Base

class Camion(Base):
    __tablename__ = "camiones"

    id = Column(Integer, primary_key=True, index=True)
    placa = Column(String(10), unique=True, nullable=False)
    color = Column(String(30))
    tipo_plancha = Column(String(50))
    conductor = Column(String(100))
    capacidad_carga = Column(DECIMAL(10, 2))
    consumo_km_litro = Column(DECIMAL(5, 2), default=3.5)
    estado = Column(
        Enum("disponible", "en_ruta", "mantenimiento"),
        default="disponible"
    )
    latitud = Column(DECIMAL(10, 8))
    longitud = Column(DECIMAL(11, 8))

    envios = relationship("Envio", back_populates="camion")

    def __repr__(self):
        return f"<Camion id={self.id} placa={self.placa}>"
