"""
Cit Clientes, vistas
"""
import json
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from lib.datatables import get_datatable_parameters, output_datatable_json
from lib.safe_string import safe_string, safe_message

from citas_admin.blueprints.bitacoras.models import Bitacora
from citas_admin.blueprints.modulos.models import Modulo
from citas_admin.blueprints.permisos.models import Permiso
from citas_admin.blueprints.usuarios.decorators import permission_required
from citas_admin.blueprints.cit_clientes.models import CitCliente

MODULO = "CIT CLIENTES"

cit_clientes = Blueprint("cit_clientes", __name__, template_folder="templates")


@cit_clientes.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""


@cit_clientes.route("/cit_clientes/datatable_json", methods=["GET", "POST"])
def datatable_json():
    """DataTable JSON para listado de Clientes"""
    # Tomar parámetros de Datatables
    draw, start, rows_per_page = get_datatable_parameters()
    # Consultar
    consulta = CitCliente.query
    if "estatus" in request.form:
        consulta = consulta.filter_by(estatus=request.form["estatus"])
    else:
        consulta = consulta.filter_by(estatus="A")
    registros = consulta.order_by(CitCliente.id).offset(start).limit(rows_per_page).all()
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
                "curp": resultado.curp,
                "telefono": resultado.telefono,
            }
        )
    # Entregar JSON
    return output_datatable_json(draw, total, data)


@cit_clientes.route("/cit_clientes")
def list_active():
    """Listado de Clientes activos"""
    return render_template(
        "cit_clientes/list.jinja2",
        filtros=json.dumps({"estatus": "A"}),
        titulo="Clientes",
        estatus="A",
    )


@cit_clientes.route("/cit_clientes/inactivos")
@permission_required(MODULO, Permiso.MODIFICAR)
def list_inactive():
    """Listado de Clientes inactivos"""
    return render_template(
        "cit_clientes/list.jinja2",
        filtros=json.dumps({"estatus": "B"}),
        titulo="Clientes inactivos",
        estatus="B",
    )


@cit_clientes.route("/cit_clientes/<int:cit_cliente_id>")
def detail(cit_cliente_id):
    """Detalle de un Cliente"""
    cit_cliente = CitCliente.query.get_or_404(cit_cliente_id)
    return render_template(
        "cit_clientes/detail.jinja2",
        filtros=json.dumps({"estatus": "A", "cliente_id": cit_cliente_id}),
        cit_cliente=cit_cliente,
    )
