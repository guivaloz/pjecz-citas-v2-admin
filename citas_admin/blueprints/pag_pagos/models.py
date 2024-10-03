"""
Pag Pagos, modelos
"""

from datetime import date, datetime
from typing import Optional

from sqlalchemy import Date, Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from citas_admin.extensions import database
from lib.universal_mixin import UniversalMixin


class PagPago(database.Model, UniversalMixin):
    """PagPago"""

    ESTADOS = {
        "SOLICITADO": "Solicitado",  # Cuando se crea el pago en espera de que el banco lo procese
        "CANCELADO": "Cancelado",  # Cuando pasa mucho tiempo y no hay respuesta del banco, se cancela
        "PAGADO": "Pagado",  # Cuando el banco procesa el pago con exito
        "FALLIDO": "Fallido",  # Cuando el banco reporta que falla el pago
        "ENTREGADO": "Entregado",  # Cuando el usuario entrega el trámite o servicio
    }

    # Nombre de la tabla
    __tablename__ = "pag_pagos"

    # Clave primaria
    id: Mapped[int] = mapped_column(primary_key=True)

    # Claves foráneas
    autoridad_id: Mapped[int] = mapped_column(ForeignKey("autoridades.id"))
    autoridad: Mapped["Autoridad"] = relationship(back_populates="pag_pagos")  # Quien debe de entregar el trámite o servicio
    distrito_id: Mapped[int] = mapped_column(ForeignKey("distritos.id"))
    distrito: Mapped["Distrito"] = relationship(back_populates="pag_pagos")  # Donde se solicita el trámite o servicio
    cit_cliente_id: Mapped[int] = mapped_column(ForeignKey("cit_clientes.id"))
    cit_cliente: Mapped["CitCliente"] = relationship(back_populates="pag_pagos")
    pag_tramite_servicio_id: Mapped[int] = mapped_column(ForeignKey("pag_tramites_servicios.id"))
    pag_tramite_servicio: Mapped["PagTramiteServicio"] = relationship(back_populates="pag_pagos")

    # Columnas
    caducidad: Mapped[date]
    cantidad: Mapped[int] = mapped_column(default=1)
    descripcion: Mapped[str] = mapped_column(String(256))
    estado: Mapped[str] = mapped_column(Enum(*ESTADOS, name="pag_pagos_estados", native_enum=False), index=True)
    email: Mapped[Optional[str]] = mapped_column(String(256))  # Si el cliente desea que se le envie el comprobante a otro email
    folio: Mapped[str] = mapped_column(String(256))
    resultado_tiempo: Mapped[Optional[datetime]]
    resultado_xml: Mapped[Optional[str]] = mapped_column(Text)
    total: Mapped[float] = mapped_column(Numeric(precision=8, scale=2, decimal_return_scale=2))
    ya_se_envio_comprobante: Mapped[bool] = mapped_column(default=False)

    def __repr__(self):
        """Representación"""
        return f"<PagPago {self.id}>"
