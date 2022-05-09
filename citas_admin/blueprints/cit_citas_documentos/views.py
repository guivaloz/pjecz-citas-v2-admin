"""
Cit Citas Documentos, vistas
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
from citas_admin.blueprints.cit_citas_documentos.models import CitCitaDocumento

MODULO = "CIT CITAS DOCUMENTOS"

cit_citas_documentos = Blueprint("cit_citas_documentos", __name__, template_folder="templates")


@cit_citas_documentos.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""


@cit_citas_documentos.route("/cit_citas_documentos/datatable_json", methods=["GET", "POST"])
def datatable_json():
    """DataTable JSON para listado de Citas Documentos"""
    # Tomar parámetros de Datatables
    draw, start, rows_per_page = get_datatable_parameters()
    # Consultar
    consulta = CitCitaDocumento.query
    if "estatus" in request.form:
        consulta = consulta.filter_by(estatus=request.form["estatus"])
    else:
        consulta = consulta.filter_by(estatus="A")
    registros = consulta.order_by(CitCitaDocumento.id).offset(start).limit(rows_per_page).all()
    total = consulta.count()
    # Elaborar datos para DataTable
    data = []
    for resultado in registros:
        data.append(
            {
                "detalle": {
                    "nombre": resultado.nombre,
                    "url": url_for("cit_citas_documentos.detail", cit_cita_documento_id=resultado.id),
                },
            }
        )
    # Entregar JSON
    return output_datatable_json(draw, total, data)


@cit_citas_documentos.route("/cit_citas_documentos")
def list_active():
    """Listado de Citas Documentos activos"""
    return render_template(
        "cit_citas_documentos/list.jinja2",
        filtros=json.dumps({"estatus": "A"}),
        titulo="Citas Documentos",
        estatus="A",
    )


@cit_citas_documentos.route("/cit_citas_documentos/inactivos")
@permission_required(MODULO, Permiso.MODIFICAR)
def list_inactive():
    """Listado de Citas Documentos inactivos"""
    return render_template(
        "cit_citas_documentos/list.jinja2",
        filtros=json.dumps({"estatus": "B"}),
        titulo="Citas Documentos inactivos",
        estatus="B",
    )


@cit_citas_documentos.route("/cit_citas_documentos/<int:cit_citas_documentos_id>")
def detail(cit_citas_documentos_id):
    """Detalle de un Cita Documento"""
    cit_cita_documento = CitCitaDocumento.query.get_or_404(cit_citas_documentos_id)
    return render_template("cit_citas_documentos/detail.jinja2", cit_cita_documento=cit_cita_documento)
