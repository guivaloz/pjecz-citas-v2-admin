"""
Usuarios Oficinas, modelos
"""
from citas_admin.extensions import db
from lib.universal_mixin import UniversalMixin


class UsuarioOficina(db.Model, UniversalMixin):
    """UsuarioOficina"""

    # Nombre de la tabla
    __tablename__ = "usuarios_oficinas"

    # Clave primaria
    id = db.Column(db.Integer, primary_key=True)

    # Clave foránea
    oficina_id = db.Column(db.Integer, db.ForeignKey("oficinas.id"), index=True, nullable=False)
    oficina = db.relationship("Oficina", back_populates="usuarios_oficinas")
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), index=True, nullable=False)
    usuario = db.relationship("Usuario", back_populates="usuarios_oficinas")

    # Columnas
    descripcion = db.Column(db.String(256), nullable=False)

    def __repr__(self):
        """Representación"""
        return f"<UsuarioOficina {self.id}>"
