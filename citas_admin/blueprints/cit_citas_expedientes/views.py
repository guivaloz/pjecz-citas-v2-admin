"""
Cit Citas Expedientes, vistas
"""
import json
from flask import Blueprint, render_template, request, url_for
from flask_login import login_required

from lib.datatables import get_datatable_parameters, output_datatable_json

from citas_admin.blueprints.cit_citas_expedientes.models import CitCitaExpediente
from citas_admin.blueprints.permisos.models import Permiso
from citas_admin.blueprints.usuarios.decorators import permission_required

MODULO = "CIT CITAS EXPEDIENTES"

cit_citas_expedientes = Blueprint("cit_citas_expedientes", __name__, template_folder="templates")


@cit_citas_expedientes.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""


@cit_citas_expedientes.route("/cit_citas_expedientes/datatable_json", methods=["GET", "POST"])
def datatable_json():
    """DataTable JSON para listado de Expedientes"""
    # Tomar parámetros de Datatables
    draw, start, rows_per_page = get_datatable_parameters()
    # Consultar
    consulta = CitCitaExpediente.query
    if "estatus" in request.form:
        consulta = consulta.filter_by(estatus=request.form["estatus"])
    else:
        consulta = consulta.filter_by(estatus="A")
    registros = consulta.order_by(CitCitaExpediente.id.desc()).offset(start).limit(rows_per_page).all()
    total = consulta.count()
    # Elaborar datos para DataTable
    data = []
    for resultado in registros:
        data.append(
            {
                "detalle": {
                    "id": resultado.id,
                    "url": url_for("cit_citas_expedientes.detail", cit_cita_expediente_id=resultado.id),
                },
                "cit_cita": {
                    "id": resultado.id,
                    "url": url_for("cit_citas.detail", cit_cita_id=resultado.cit_cita_id),
                },
                "expediente": resultado.expediente,
            }
        )
    # Entregar JSON
    return output_datatable_json(draw, total, data)


@cit_citas_expedientes.route("/cit_citas_expedientes")
def list_active():
    """Listado de Expedientes activos"""
    return render_template(
        "cit_citas_expedientes/list.jinja2",
        filtros=json.dumps({"estatus": "A"}),
        titulo="Expedientes",
        estatus="A",
    )


@cit_citas_expedientes.route("/cit_citas_expedientes/inactivos")
@permission_required(MODULO, Permiso.MODIFICAR)
def list_inactive():
    """Listado de Expedientes inactivos"""
    return render_template(
        "cit_citas_expedientes/list.jinja2",
        filtros=json.dumps({"estatus": "B"}),
        titulo="Expedientes inactivos",
        estatus="B",
    )


@cit_citas_expedientes.route("/cit_citas_expedientes/<int:cit_cita_expediente_id>")
def detail(cit_cita_expediente_id):
    """Detalle de un Expediente"""
    cit_cita_expediente = CitCitaExpediente.query.get_or_404(cit_cita_expediente_id)
    return render_template("cit_citas_expedientes/detail.jinja2", cit_cita_expediente=cit_cita_expediente)
