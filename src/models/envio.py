from sqlalchemy import Column, Integer, String, DECIMAL, Enum, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


class Envio(Base):
    __tablename__ = "envios"

    id = Column(Integer, primary_key=True, index=True)
    cliente = Column(String(150), nullable=False)
    latitud = Column(DECIMAL(10, 8))
    longitud = Column(DECIMAL(11, 8))
    punto_venta_id = Column(Integer, ForeignKey("puntos_venta.id"))
    camion_id = Column(Integer, ForeignKey("camiones.id"))
    estado = Column(
        Enum("pendiente", "asignado", "en_transito", "entregado"),
        default="pendiente"
    )
    punto_venta = relationship("PuntoVenta", back_populates="envios")
    camion = relationship("Camion", back_populates="envios")
    valor_carga = Column(DECIMAL (10, 8))
    valor_descarga = Column(DECIMAL(10, 8))
    viaticos = Column(DECIMAL(10, 8))
    escolta = Column(DECIMAL (10, 8))
    