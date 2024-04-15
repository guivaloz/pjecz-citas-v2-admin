"""
Encuestas, vistas
"""

import json
from datetime import datetime, timedelta

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from lib.datatables import get_datatable_parameters, output_datatable_json

from citas_admin.blueprints.bitacoras.models import Bitacora
from citas_admin.blueprints.modulos.models import Modulo
from citas_admin.blueprints.permisos.models import Permiso
from citas_admin.blueprints.usuarios.decorators import permission_required

from citas_admin.blueprints.enc_sistemas.models import EncSistema

MODULO = "ENC SISTEMAS"

enc_sistemas = Blueprint("enc_sistemas", __name__, template_folder="templates")


@enc_sistemas.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""


@enc_sistemas.route("/encuestas/sistemas/datatable_json", methods=["GET", "POST"])
def datatable_json():
    """DataTable JSON para listado de respuestas de la encuesta de sistema"""
    # Tomar parámetros de Datatables
    draw, start, rows_per_page = get_datatable_parameters()
    # Consultar
    consulta = EncSistema.query
    if "estatus" in request.form:
        consulta = consulta.filter_by(estatus=request.form["estatus"])
    else:
        consulta = consulta.filter_by(estatus="A")
    if "desde" in request.form:
        consulta = consulta.filter(EncSistema.modificado >= request.form["desde"])
    if "hasta" in request.form:
        consulta = consulta.filter(EncSistema.modificado <= request.form["hasta"])
    if "respuesta_01" in request.form:
        consulta = consulta.filter_by(respuesta_01=request.form["respuesta_01"])
    if "estado" in request.form:
        consulta = consulta.filter_by(estado=request.form["estado"])
    # Hace el query de listado
    registros = consulta.order_by(EncSistema.id.desc()).offset(start).limit(rows_per_page).all()
    total = consulta.count()
    # Elaborar datos para DataTable
    data = []
    for registro in registros:
        data.append(
            {
                "id": {
                    "id": registro.id,
                    "url": url_for("enc_sistemas.detail", respuesta_id=registro.id),
                },
                "creado": registro.creado.strftime("%Y-%m-%d %H:%M"),
                "respuesta_01": registro.respuesta_01,
                "respuesta_02": registro.respuesta_02,
                "respuesta_03": registro.respuesta_03,
                "estado": registro.estado,
            }
        )
    # Entregar JSON
    return output_datatable_json(draw, total, data)


@enc_sistemas.route("/encuestas/sistemas")
def list_active():
    """Listado de respuestas dela encuesta del sistema"""
    return render_template(
        "enc_sistemas/list.jinja2",
        filtros=json.dumps({"estatus": "A"}),
        titulo="Encuesta del Sistema",
    )


@enc_sistemas.route("/encuestas/sistemas/<int:respuesta_id>", methods=["GET", "POST"])
def detail(respuesta_id):
    """Detalle de una respuesta"""
    detalle = EncSistema.query.get_or_404(respuesta_id)
    return render_template(
        "enc_sistemas/detail.jinja2",
        filtros=json.dumps({"estatus": "A"}),
        titulo="Encuesta del Sistema",
        detalle=detalle,
    )
