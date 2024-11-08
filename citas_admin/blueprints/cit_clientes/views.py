"""
Cit Clientes, vistas
"""

import json

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
from lib.safe_string import safe_email, safe_message, safe_string

MODULO = "CIT CLIENTES"

cit_clientes = Blueprint("cit_clientes", __name__, template_folder="templates")


@cit_clientes.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""


@cit_clientes.route("/cit_clientes/datatable_json", methods=["GET", "POST"])
def datatable_json():
    """DataTable JSON para listado de CitCliente"""
    # Tomar parámetros de Datatables
    draw, start, rows_per_page = get_datatable_parameters()
    # Consultar
    consulta = CitCliente.query
    # Primero filtrar por columnas propias
    if "estatus" in request.form:
        consulta = consulta.filter(CitCliente.estatus == request.form["estatus"])
    else:
        consulta = consulta.filter(CitCliente.estatus == "A")
    if "email" in request.form:
        email = safe_email(request.form["email"], search_fragment=True)
        if email != "":
            consulta = consulta.filter(CitCliente.email.contains(email))
    if "nombres" in request.form:
        nombres = safe_string(request.form["nombres"], save_enie=True)
        if nombres != "":
            consulta = consulta.filter(CitCliente.nombres.contains(nombres))
    if "apellido_primero" in request.form:
        apellido_primero = safe_string(request.form["apellido_primero"], save_enie=True)
        if apellido_primero != "":
            consulta = consulta.filter(CitCliente.apellido_primero.contains(apellido_primero))
    # Ordenar y paginar
    registros = consulta.order_by(CitCliente.email).offset(start).limit(rows_per_page).all()
    total = consulta.count()
    # Elaborar datos para DataTable
    data = []
    for resultado in registros:
        data.append(
            {
                "detalle": {
                    "email": resultado.email,
                    "url": url_for("cit_clientes.detail", cit_cliente_id=resultado.id),
                },
                "nombre": resultado.nombre,
                "telefono": resultado.telefono,
            }
        )
    # Entregar JSON
    return output_datatable_json(draw, total, data)


@cit_clientes.route("/cit_clientes")
def list_active():
    """Listado de CitCliente activos"""
    return render_template(
        "cit_clientes/list.jinja2",
        filtros=json.dumps({"estatus": "A"}),
        titulo="Clientes",
        estatus="A",
    )


@cit_clientes.route("/cit_clientes/inactivos")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def list_inactive():
    """Listado de CitCliente inactivos"""
    return render_template(
        "cit_clientes/list.jinja2",
        filtros=json.dumps({"estatus": "B"}),
        titulo="Clientes inactivos",
        estatus="B",
    )


@cit_clientes.route("/cit_clientes/<int:cit_cliente_id>")
def detail(cit_cliente_id):
    """Detalle de un CitCliente"""
    # Consultar
    cit_cliente = CitCliente.query.get_or_404(cit_cliente_id)
    # Consultar PagTramiteServicio para las opciones del filtro
    pag_tramites_servicios = PagTramiteServicio.query.filter_by(estatus="A").order_by(PagTramiteServicio.clave).all()
    opciones_pag_tramites_servicios = []
    for ts in pag_tramites_servicios:
        opciones_pag_tramites_servicios.append({"id": ts.id, "clave": ts.clave, "descripcion": ts.descripcion})
    # Entregar
    return render_template(
        "cit_clientes/detail.jinja2",
        cit_cliente=cit_cliente,
        pag_pagos_estados=PagPago.ESTADOS,
        pag_tramites_servicios=opciones_pag_tramites_servicios,
    )
