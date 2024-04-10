"""
Oficinas, modelos
"""

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Time
from sqlalchemy.orm import relationship

from lib.universal_mixin import UniversalMixin
from citas_admin.extensions import database


class Oficina(database.Model, UniversalMixin):
    """Oficina"""

    # Nombre de la tabla
    __tablename__ = "oficinas"

    # Clave primaria
    id = Column(Integer, primary_key=True)

    # Clave foránea
    distrito_id = Column(Integer, ForeignKey("distritos.id"), index=True, nullable=False)
    distrito = relationship("Distrito", back_populates="oficinas")
    domicilio_id = Column(Integer, ForeignKey("domicilios.id"), index=True, nullable=False)
    domicilio = relationship("Domicilio", back_populates="oficinas")

    # Columnas
    clave = Column(String(32), unique=True, nullable=False)
    descripcion = Column(String(512), nullable=False)
    descripcion_corta = Column(String(64), nullable=False)
    es_jurisdiccional = Column(Boolean, nullable=False, default=False)
    puede_agendar_citas = Column(Boolean, nullable=False, default=False)
    apertura = Column(Time(), nullable=False)
    cierre = Column(Time(), nullable=False)
    limite_personas = Column(Integer(), nullable=False)
    puede_enviar_qr = Column(Boolean(), nullable=False, default=False)

    # Hijos
    usuarios = relationship("Usuario", back_populates="oficina")
    cit_citas = relationship("CitCita", back_populates="oficina")
    cit_horas_bloqueadas = relationship("CitHoraBloqueada", back_populates="oficina")
    cit_oficinas_servicios = relationship("CitOficinaServicio", back_populates="oficina")
    enc_servicios = relationship("EncServicio", back_populates="oficina")
    usuarios_oficinas = relationship("UsuarioOficina", back_populates="oficina")

    @property
    def compuesto(self):
        """Entregar clave - descripcion_corta para selects"""
        return f"{self.clave} - {self.descripcion_corta}"

    def __repr__(self):
        """Representación"""
        return f"<Oficina> {self.clave}"
