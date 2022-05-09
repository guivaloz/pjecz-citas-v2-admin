"""
Cit Clientes Registros, vistas
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
from citas_admin.blueprints.cit_clientes_registros.models import CitClienteRegistro

MODULO = "CIT CLIENTES REGISTROS"

cit_clientes_registros = Blueprint("cit_clientes_registros", __name__, template_folder="templates")


@cit_clientes_registros.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""


@cit_clientes_registros.route("/cit_clientes_registros/datatable_json", methods=["GET", "POST"])
def datatable_json():
    """DataTable JSON para listado de Clientes Registros"""
    # Tomar parámetros de Datatables
    draw, start, rows_per_page = get_datatable_parameters()
    # Consultar
    consulta = CitClienteRegistro.query
    if "estatus" in request.form:
        consulta = consulta.filter_by(estatus=request.form["estatus"])
    else:
        consulta = consulta.filter_by(estatus="A")
    registros = consulta.order_by(CitClienteRegistro.id).offset(start).limit(rows_per_page).all()
    total = consulta.count()
    # Elaborar datos para DataTable
    data = []
    for resultado in registros:
        data.append(
            {
                "detalle": {
                    "id": resultado.id,
                    "url": url_for("cit_clientes_registros.detail", cit_cliente_registro_id=resultado.id),
                },
                "nombres": resultado.nombres,
                "apellido_primero": resultado.apellido_primero,
                "apellido_segundo": resultado.apellido_segundo,
                "email": resultado.email,
                "expiracion": resultado.expiracion,
                "ya_registrado": resultado.ya_registrado,
            }
        )
    # Entregar JSON
    return output_datatable_json(draw, total, data)


@cit_clientes_registros.route("/cit_clientes_registros")
def list_active():
    """Listado de Clientes Registros activos"""
    return render_template(
        "cit_clientes_registros/list.jinja2",
        filtros=json.dumps({"estatus": "A"}),
        titulo="Clientes Registros",
        estatus="A",
    )


@cit_clientes_registros.route("/cit_clientes_registros/inactivos")
@permission_required(MODULO, Permiso.MODIFICAR)
def list_inactive():
    """Listado de Clientes Registros inactivos"""
    return render_template(
        "cit_clientes_registros/list.jinja2",
        filtros=json.dumps({"estatus": "B"}),
        titulo="Clientes Registros inactivos",
        estatus="B",
    )


@cit_clientes_registros.route("/cit_clientes_registros/<int:cit_cliente_registro_id>")
def detail(cit_cliente_registro_id):
    """Detalle de un Cliente Registro"""
    cit_cliente_registro = CitClienteRegistro.query.get_or_404(cit_cliente_registro_id)
    return render_template("cit_clientes_registros/detail.jinja2", cit_cliente_registro=cit_cliente_registro)
