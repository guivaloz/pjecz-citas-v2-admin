"""
Cit Clientes Registros, vistas
"""

import json

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from citas_admin.blueprints.bitacoras.models import Bitacora
from citas_admin.blueprints.cit_clientes_registros.models import CitClienteRegistro
from citas_admin.blueprints.modulos.models import Modulo
from citas_admin.blueprints.permisos.models import Permiso
from citas_admin.blueprints.usuarios.decorators import permission_required
from lib.datatables import get_datatable_parameters, output_datatable_json
from lib.safe_string import safe_email, safe_message, safe_string

MODULO = "CIT CLIENTES REGISTROS"

cit_clientes_registros = Blueprint("cit_clientes_registros", __name__, template_folder="templates")


@cit_clientes_registros.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""


@cit_clientes_registros.route("/cit_clientes_registros/datatable_json", methods=["GET", "POST"])
def datatable_json():
    """DataTable JSON para listado de Cit Clientes Registros"""
    # Tomar parámetros de Datatables
    draw, start, rows_per_page = get_datatable_parameters()
    # Consultar
    consulta = CitClienteRegistro.query
    # Primero filtrar por columnas propias
    if "estatus" in request.form:
        consulta = consulta.filter(CitClienteRegistro.estatus == request.form["estatus"])
    else:
        consulta = consulta.filter(CitClienteRegistro.estatus == "A")
    if "email" in request.form:
        email = safe_email(request.form["email"], search_fragment=True)
        if email != "":
            consulta = consulta.filter(CitClienteRegistro.email.contains(email))
    if "nombres" in request.form:
        nombres = safe_string(request.form["nombres"], save_enie=True)
        if nombres != "":
            consulta = consulta.filter(CitClienteRegistro.nombres.contains(nombres))
    if "apellido_primero" in request.form:
        apellido_primero = safe_string(request.form["apellido_primero"], save_enie=True)
        if apellido_primero != "":
            consulta = consulta.filter(CitClienteRegistro.apellido_primero.contains(apellido_primero))
    # Ordenar y paginar
    registros = consulta.order_by(CitClienteRegistro.id.desc()).offset(start).limit(rows_per_page).all()
    total = consulta.count()
    # Elaborar datos para DataTable
    data = []
    for resultado in registros:
        data.append(
            {
                "detalle": {
                    "email": resultado.email,
                    "url": url_for("cit_clientes_registros.detail", cit_cliente_registro_id=resultado.id),
                },
                "nombre": resultado.nombre,
                "expiracion": resultado.expiracion.strftime("%Y-%m-%dT%H:%M:%S"),
                "ya_registrado": resultado.ya_registrado,
            }
        )
    # Entregar JSON
    return output_datatable_json(draw, total, data)


@cit_clientes_registros.route("/cit_clientes_registros")
def list_active():
    """Listado de Cit Clientes Regsitros activos"""
    return render_template(
        "cit_clientes_registros/list.jinja2",
        filtros=json.dumps({"estatus": "A"}),
        titulo="Clientes Registros",
        estatus="A",
    )


@cit_clientes_registros.route("/cit_clientes_registros/inactivos")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def list_inactive():
    """Listado de Cit Clientes Registros inactivos"""
    return render_template(
        "cit_clientes_registros/list.jinja2",
        filtros=json.dumps({"estatus": "B"}),
        titulo="Clientes Registros inactivos",
        estatus="B",
    )


@cit_clientes_registros.route("/cit_clientes_registros/<int:cit_cliente_registro_id>")
def detail(cit_cliente_registro_id):
    """Detalle de un Cit Cliente Registro"""
    cit_cliente_registro = CitClienteRegistro.query.get_or_404(cit_cliente_registro_id)
    return render_template("cit_clientes_registros/detail.jinja2", cit_cliente_registro=cit_cliente_registro)
