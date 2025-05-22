from sqlalchemy import Column, Integer, String, Float, DateTime, Enum
from sqlalchemy.ext.declarative import declarative_base
from enum import Enum as PyEnum
from datetime import datetime

Base = declarative_base()

class EstadoCliente(PyEnum):
    on = "on"
    off = "off"

class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, index=True)
    ec2_id = Column(String, unique=True, nullable=False)
    horas_contratadas = Column(Float, nullable=False)
    hora_inicio = Column(DateTime, nullable=True)
    fecha_apagado = Column(DateTime, nullable=True)
    state = Column(Enum(EstadoCliente), default=EstadoCliente.off, nullable=False)

    def __repr__(self):
        return f"<Cliente(id={self.id}, ec2_id={self.ec2_id}, state={self.state})>"
