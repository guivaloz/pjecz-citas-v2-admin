"""
Pago de Pensiones Alimenticias - Solicitudes, vistas
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
from citas_admin.blueprints.ppa_solicitudes.models import PpaSolicitud

MODULO = "Ppa SOLICITUDES"

ppa_solicitudes = Blueprint("ppa_solicitudes", __name__, template_folder="templates")


@ppa_solicitudes.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""


@ppa_solicitudes.route("/ppa_solicitudes/datatable_json", methods=["GET", "POST"])
def datatable_json():
    """DataTable JSON para listado de solicitudes"""
    # Tomar parámetros de Datatables
    draw, start, rows_per_page = get_datatable_parameters()
    # Consultar
    consulta = PpaSolicitud.query
    if "estatus" in request.form:
        consulta = consulta.filter_by(estatus=request.form["estatus"])
    else:
        consulta = consulta.filter_by(estatus="A")
    registros = consulta.order_by(PpaSolicitud.id).offset(start).limit(rows_per_page).all()
    total = consulta.count()
    # Elaborar datos para DataTable
    data = []
    for resultado in registros:
        data.append(
            {
                "detalle": {
                    "id": resultado.id,
                    "url": url_for("ppa_solicitudes.detail", ppa_solicitud_id=resultado.id),
                },
            }
        )
    # Entregar JSON
    return output_datatable_json(draw, total, data)


@ppa_solicitudes.route("/ppa_solicitudes")
def list_active():
    """Listado de solicitudes activas"""
    return render_template(
        "ppa_solicitudes/list.jinja2",
        filtros=json.dumps({"estatus": "A"}),
        titulo="solicitudes",
        estatus="A",
    )
