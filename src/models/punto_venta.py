from sqlalchemy import Column, Integer, String, DECIMAL, TIMESTAMP
from sqlalchemy.orm import relationship
from database import Base


class PuntoVenta(Base):
    __tablename__ = "puntos_venta"

    id = Column(Integer, primary_key=True, index=True)
    ciudad = Column(String(100), nullable=False)

    latitud = Column(DECIMAL(10, 8), nullable=False)
    longitud = Column(DECIMAL(11, 8), nullable=False)

    created_at = Column(TIMESTAMP)

    # Relación con envíos
    envios = relationship("Envio", back_populates="punto_venta")

    def __repr__(self):
        return f"<PuntoVenta id={self.id} ciudad={self.ciudad}>"
