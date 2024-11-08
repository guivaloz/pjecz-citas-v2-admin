"""
Pag Pagos, vistas
"""

import json
import re
from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from citas_admin.blueprints.bitacoras.models import Bitacora
from citas_admin.blueprints.cit_clientes.models import CitCliente
from citas_admin.blueprints.modulos.models import Modulo
from citas_admin.blueprints.pag_pagos.models import PagPago
from citas_admin.blueprints.pag_tramites_servicios.models import PagTramiteServicio
from citas_admin.blueprints.permisos.models import Permiso
from citas_admin.blueprints.usuarios.decorators import permission_required
from lib.datatables import get_datatable_parameters, output_datatable_json
from lib.safe_string import safe_message, safe_string

MODULO = "PAG PAGOS"

pag_pagos = Blueprint("pag_pagos", __name__, template_folder="templates")


@pag_pagos.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""


@pag_pagos.route("/pag_pagos/datatable_json", methods=["GET", "POST"])
def datatable_json():
    """DataTable JSON para listado de PagPago"""
    # Tomar parámetros de Datatables
    draw, start, rows_per_page = get_datatable_parameters()
    # Consultar
    consulta = PagPago.query
    # Primero filtrar por columnas propias
    if "estatus" in request.form:
        consulta = consulta.filter(PagPago.estatus == request.form["estatus"])
    else:
        consulta = consulta.filter(PagPago.estatus == "A")
    if "id" in request.form:
        consulta = consulta.filter(PagPago.id == request.form["id"])
    else:
        # Filtrar por ids que ya tenemos en esta tabla
        if "cit_cliente_id" in request.form:
            consulta = consulta.filter(PagPago.cit_cliente_id == request.form["cit_cliente_id"])
        if "pag_tramite_servicio_id" in request.form:
            consulta = consulta.filter(PagPago.pag_tramite_servicio_id == request.form["pag_tramite_servicio_id"])
        # Filtrar por estado que es un select
        if "estado" in request.form:
            consulta = consulta.filter_by(estado=request.form["estado"])
        # Filtrar por las fechas, si vienen invertidas se corrigen
        fecha_desde = None
        fecha_hasta = None
        if "fecha_desde" in request.form and re.match(r"\d{4}-\d{2}-\d{2}", request.form["fecha_desde"]):
            fecha_desde = request.form["fecha_desde"]
        if "fecha_hasta" in request.form and re.match(r"\d{4}-\d{2}-\d{2}", request.form["fecha_hasta"]):
            fecha_hasta = request.form["fecha_hasta"]
        if fecha_desde and fecha_hasta and fecha_desde > fecha_hasta:
            fecha_desde, fecha_hasta = fecha_hasta, fecha_desde
        if fecha_desde:
            consulta = consulta.filter(PagPago.fecha >= fecha_desde)
        if fecha_hasta:
            consulta = consulta.filter(PagPago.fecha <= fecha_hasta)
    # Ordenar y paginar
    registros = consulta.order_by(PagPago.id.desc()).offset(start).limit(rows_per_page).all()
    total = consulta.count()
    # Elaborar datos para DataTable
    data = []
    for resultado in registros:
        data.append(
            {
                "detalle": {
                    "id": resultado.id,
                    "url": url_for("pag_pagos.detail", pag_pago_id=resultado.id),
                },
                "creado": resultado.creado.strftime("%Y-%m-%dT%H:%M:%S"),
                "cit_cliente": {
                    "nombre": f"{resultado.cit_cliente.nombre}",
                    "url": (
                        url_for("cit_clientes.detail", cit_cliente_id=resultado.cit_cliente_id)
                        if current_user.can_view("CIT CLIENTES")
                        else ""
                    ),
                },
                "email": resultado.cit_cliente.email,
                "cantidad": resultado.cantidad,
                "pag_tramite_servicio": {
                    "clave": resultado.pag_tramite_servicio.clave,
                    "descripcion": resultado.pag_tramite_servicio.descripcion,
                    "url": (
                        url_for("pag_tramites_servicios.detail", pag_tramite_servicio_id=resultado.pag_tramite_servicio_id)
                        if current_user.can_view("PAG TRAMITES SERVICIOS")
                        else ""
                    ),
                },
                "distrito": {
                    "clave": resultado.distrito.clave,
                    "nombre_corto": resultado.distrito.nombre_corto,
                    "url": (
                        url_for("distritos.detail", distrito_id=resultado.distrito_id)
                        if current_user.can_view("DISTRITOS")
                        else ""
                    ),
                },
                "autoridad": {
                    "clave": resultado.autoridad.clave,
                    "nombre_corto": resultado.autoridad.descripcion_corta,
                    "url": (
                        url_for("autoridades.detail", autoridad_id=resultado.autoridad_id)
                        if current_user.can_view("AUTORIDADES")
                        else ""
                    ),
                },
                "folio": resultado.folio,
                "total": resultado.total,
                "estado": resultado.estado,
            }
        )
    # Entregar JSON
    return output_datatable_json(draw, total, data)


@pag_pagos.route("/pag_pagos")
def list_active():
    """Listado de PagPago activos"""
    # Consultar PagTramiteServicio para las opciones del filtro
    pag_tramites_servicios = PagTramiteServicio.query.filter_by(estatus="A").order_by(PagTramiteServicio.clave).all()
    opciones_pag_tramites_servicios = []
    for ts in pag_tramites_servicios:
        opciones_pag_tramites_servicios.append({"id": ts.id, "clave": ts.clave, "descripcion": ts.descripcion})
    # Entregar
    return render_template(
        "pag_pagos/list.jinja2",
        filtros=json.dumps({"estatus": "A"}),
        titulo="Pagos",
        estatus="A",
        pag_pagos_estados=PagPago.ESTADOS,
        pag_tramites_servicios=opciones_pag_tramites_servicios,
    )


@pag_pagos.route("/pag_pagos/inactivos")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def list_inactive():
    """Listado de PagPago inactivos"""
    # Consultar PagTramiteServicio para las opciones del filtro
    pag_tramites_servicios = PagTramiteServicio.query.filter_by(estatus="A").order_by(PagTramiteServicio.clave).all()
    opciones_pag_tramites_servicios = []
    for ts in pag_tramites_servicios:
        opciones_pag_tramites_servicios.append({"id": ts.id, "clave": ts.clave, "descripcion": ts.descripcion})
    # Entregar
    return render_template(
        "pag_pagos/list.jinja2",
        filtros=json.dumps({"estatus": "B"}),
        titulo="Pagos inactivos",
        estatus="B",
        pag_pagos_estados=PagPago.ESTADOS,
        pag_tramites_servicios=opciones_pag_tramites_servicios,
    )


@pag_pagos.route("/pag_pagos/<int:pag_pago_id>")
def detail(pag_pago_id):
    """Detalle de un PagPago"""
    pag_pago = PagPago.query.get_or_404(pag_pago_id)
    return render_template("pag_pagos/detail.jinja2", pag_pago=pag_pago)


@pag_pagos.route("/pag_pagos/tablero")
def dashboard():
    """Tablero de PagPago"""
    return render_template("pag_pagos/dashboard.jinja2")
