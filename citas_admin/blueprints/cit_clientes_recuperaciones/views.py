"""
Cit Clientes Recuperaciones, vistas
"""
import json

from flask import Blueprint, render_template, request, url_for
from flask_login import login_required

from lib.datatables import get_datatable_parameters, output_datatable_json

from citas_admin.blueprints.cit_clientes.models import CitCliente
from citas_admin.blueprints.cit_clientes_recuperaciones.models import CitClienteRecuperacion
from citas_admin.blueprints.permisos.models import Permiso
from citas_admin.blueprints.usuarios.decorators import permission_required

MODULO = "CIT CLIENTES RECUPERACIONES"

cit_clientes_recuperaciones = Blueprint("cit_clientes_recuperaciones", __name__, template_folder="templates")


@cit_clientes_recuperaciones.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""


@cit_clientes_recuperaciones.route("/cit_clientes_recuperaciones/datatable_json", methods=["GET", "POST"])
def datatable_json():
    """DataTable JSON para listado de Clientes Recuperaciones"""
    # Tomar parámetros de Datatables
    draw, start, rows_per_page = get_datatable_parameters()
    # Consultar
    consulta = CitClienteRecuperacion.query
    if "estatus" in request.form:
        consulta = consulta.filter_by(estatus=request.form["estatus"])
    else:
        consulta = consulta.filter_by(estatus="A")
    if "email" in request.form:
        consulta = consulta.join(CitCliente)
        consulta = consulta.filter(CitCliente.email.contains(request.form["email"]))
    if "ya_recuperado" in request.form:
        consulta = consulta.filter(CitClienteRecuperacion.ya_recuperado == request.form["ya_recuperado"])

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
                    "email": resultado.cit_cliente.email,
                    "url": url_for("cit_clientes.detail", cit_cliente_id=resultado.cit_cliente_id),
                },
                "expiracion": resultado.expiracion,
                "ya_recuperado": resultado.ya_recuperado,
            }
        )
    # Entregar JSON
    return output_datatable_json(draw, total, data)


@cit_clientes_recuperaciones.route("/cit_clientes_recuperaciones")
def list_active():
    """Listado de Clientes Recuperaciones activas"""
    return render_template(
        "cit_clientes_recuperaciones/list.jinja2",
        filtros=json.dumps({"estatus": "A"}),
        titulo="Clientes Recuperaciones",
        estatus="A",
    )


@cit_clientes_recuperaciones.route("/cit_clientes_recuperaciones/inactivos")
@permission_required(MODULO, Permiso.MODIFICAR)
def list_inactive():
    """Listado de Clientes Recuperaciones inactivas"""
    return render_template(
        "cit_clientes_recuperaciones/list.jinja2",
        filtros=json.dumps({"estatus": "B"}),
        titulo="Clientes Recuperaciones inactivas",
        estatus="B",
    )


@cit_clientes_recuperaciones.route("/cit_clientes_recuperaciones/<int:cit_cliente_recuperacion_id>")
def detail(cit_cliente_recuperacion_id):
    """Detalle de un Cliente Recuperacion"""
    cit_cliente_recuperacion = CitClienteRecuperacion.query.get_or_404(cit_cliente_recuperacion_id)
    return render_template("cit_clientes_recuperaciones/detail.jinja2", cit_cliente_recuperacion=cit_cliente_recuperacion)
