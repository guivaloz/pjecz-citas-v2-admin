"""
Usuarios Oficinas, modelos
"""

from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from lib.universal_mixin import UniversalMixin
from citas_admin.extensions import database


class UsuarioOficina(database.Model, UniversalMixin):
    """UsuarioOficina"""

    # Nombre de la tabla
    __tablename__ = "usuarios_oficinas"

    # Clave primaria
    id = Column(Integer, primary_key=True)

    # Clave foránea
    oficina_id = Column(Integer, ForeignKey("oficinas.id"), index=True, nullable=False)
    oficina = relationship("Oficina", back_populates="usuarios_oficinas")
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), index=True, nullable=False)
    usuario = relationship("Usuario", back_populates="usuarios_oficinas")

    # Columnas
    descripcion = Column(String(256), nullable=False)

    def __repr__(self):
        """Representación"""
        return f"<UsuarioOficina {self.id}>"
