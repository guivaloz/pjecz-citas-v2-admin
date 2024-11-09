"""
Cit Clientes Recuperaciones, vistas
"""

import json

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from citas_admin.blueprints.bitacoras.models import Bitacora
from citas_admin.blueprints.cit_clientes.models import CitCliente
from citas_admin.blueprints.cit_clientes_recuperaciones.models import CitClienteRecuperacion
from citas_admin.blueprints.modulos.models import Modulo
from citas_admin.blueprints.permisos.models import Permiso
from citas_admin.blueprints.usuarios.decorators import permission_required
from lib.datatables import get_datatable_parameters, output_datatable_json
from lib.safe_string import safe_email, safe_message, safe_string

MODULO = "CIT CLIENTES RECUPERACIONES"

cit_clientes_recuperaciones = Blueprint("cit_clientes_recuperaciones", __name__, template_folder="templates")


@cit_clientes_recuperaciones.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""


@cit_clientes_recuperaciones.route("/cit_clientes_recuperaciones/datatable_json", methods=["GET", "POST"])
def datatable_json():
    """DataTable JSON para listado de Cit Clientes Recuperaciones"""
    # Tomar parámetros de Datatables
    draw, start, rows_per_page = get_datatable_parameters()
    # Consultar
    consulta = CitClienteRecuperacion.query
    # Primero filtrar por columnas propias
    if "estatus" in request.form:
        consulta = consulta.filter(CitClienteRecuperacion.estatus == request.form["estatus"])
    else:
        consulta = consulta.filter(CitClienteRecuperacion.estatus == "A")
    # Luego filtrar por columnas de otras tablas
    cit_cliente_email = ""
    if "cit_cliente_email" in request.form:
        cit_cliente_email = safe_email(request.form["cit_cliente_email"], search_fragment=True)
    cit_cliente_nombres = ""
    if "cit_cliente_nombres" in request.form:
        cit_cliente_nombres = safe_string(request.form["cit_cliente_nombres"], save_enie=True)
    cit_cliente_primer_apellido = ""
    if "cit_cliente_primer_apellido" in request.form:
        cit_cliente_primer_apellido = safe_string(request.form["cit_cliente_primer_apellido"], save_enie=True)
    if cit_cliente_email != "" or cit_cliente_nombres != "" or cit_cliente_primer_apellido != "":
        consulta = consulta.join(CitCliente)
        if cit_cliente_email != "":
            consulta = consulta.filter(CitCliente.email.contains(cit_cliente_email))
        if cit_cliente_nombres != "":
            consulta = consulta.filter(CitCliente.nombres.contains(cit_cliente_nombres))
        if cit_cliente_primer_apellido != "":
            consulta = consulta.filter(CitCliente.primer_apellido.contains(cit_cliente_primer_apellido))
    # Ordenar y paginar
    registros = consulta.order_by(CitClienteRecuperacion.id.desc()).offset(start).limit(rows_per_page).all()
    total = consulta.count()
    # Elaborar datos para DataTable
    data = []
    for resultado in registros:
        data.append(
            {
                "detalle": {
                    "id": resultado.id,
                    "url": url_for("cit_clientes_recuperaciones.detail", cit_cliente_recuperacion_id=resultado.id),
                },
                "cit_cliente": {
                    "nombre": resultado.cit_cliente.nombre,
                    "url": (
                        url_for("cit_clientes.detail", cit_cliente_id=resultado.cit_cliente.id)
                        if current_user.can_view("CIT CLIENTES")
                        else ""
                    ),
                },
                "expiracion": resultado.expiracion.strftime("%Y-%m-%dT%H:%M:%S"),
                "ya_recuperado": resultado.ya_recuperado,
            }
        )
    # Entregar JSON
    return output_datatable_json(draw, total, data)


@cit_clientes_recuperaciones.route("/cit_clientes_recuperaciones")
def list_active():
    """Listado de Cit Clientes Recuperaciones activas"""
    return render_template(
        "cit_clientes_recuperaciones/list.jinja2",
        filtros=json.dumps({"estatus": "A"}),
        titulo="Clientes Recuperaciones",
        estatus="A",
    )


@cit_clientes_recuperaciones.route("/cit_clientes_recuperaciones/inactivos")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def list_inactive():
    """Listado de Cit Clientes Recuperaciones inactivas"""
    return render_template(
        "cit_clientes_recuperaciones/list.jinja2",
        filtros=json.dumps({"estatus": "B"}),
        titulo="Clientes Recuperaciones inactivos",
        estatus="B",
    )


@cit_clientes_recuperaciones.route("/cit_clientes_recuperaciones/<int:cit_cliente_recuperacion_id>")
def detail(cit_cliente_recuperacion_id):
    """Detalle de un Cit Cliente Recuperacion"""
    cit_cliente_recuperacion = CitClienteRecuperacion.query.get_or_404(cit_cliente_recuperacion_id)
    return render_template("cit_clientes_recuperaciones/detail.jinja2", cit_cliente_recuperacion=cit_cliente_recuperacion)
