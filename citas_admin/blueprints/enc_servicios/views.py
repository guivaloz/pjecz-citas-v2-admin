"""
Encuestas, vistas
"""

import json
from datetime import datetime, timedelta

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import func

from lib.datatables import get_datatable_parameters, output_datatable_json

from citas_admin.blueprints.bitacoras.models import Bitacora
from citas_admin.blueprints.modulos.models import Modulo
from citas_admin.blueprints.permisos.models import Permiso
from citas_admin.blueprints.usuarios.decorators import permission_required
from citas_admin.blueprints.enc_servicios.models import EncServicio
from citas_admin.blueprints.oficinas.models import Oficina
from citas_admin.blueprints.distritos.models import Distrito
from citas_admin.extensions import database

MODULO = "ENC SERVICIOS"

enc_servicios = Blueprint("enc_servicios", __name__, template_folder="templates")


@enc_servicios.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""


@enc_servicios.route("/encuestas/servicios/datatable_json", methods=["GET", "POST"])
def datatable_json():
    """DataTable JSON para listado de respuestas de la encuesta de sistema"""
    # Tomar parámetros de Datatables
    draw, start, rows_per_page = get_datatable_parameters()
    # Consultar
    consulta = EncServicio.query
    if "estatus" in request.form:
        consulta = consulta.filter_by(estatus=request.form["estatus"])
    else:
        consulta = consulta.filter_by(estatus="A")
    if "desde" in request.form:
        consulta = consulta.filter(EncServicio.modificado >= request.form["desde"])
    if "hasta" in request.form:
        consulta = consulta.filter(EncServicio.modificado <= request.form["hasta"])
    if "respuesta_01" in request.form:
        consulta = consulta.filter_by(respuesta_01=request.form["respuesta_01"])
    if "respuesta_02" in request.form:
        consulta = consulta.filter_by(respuesta_02=request.form["respuesta_02"])
    if "respuesta_03" in request.form:
        consulta = consulta.filter_by(respuesta_03=request.form["respuesta_03"])
    if "estado" in request.form:
        consulta = consulta.filter_by(estado=request.form["estado"])
    if "oficina_id" in request.form:
        consulta = consulta.filter_by(oficina_id=request.form["oficina_id"])
    else:
        if "distrito_id" in request.form:
            consulta = consulta.join(Oficina)
            consulta = consulta.join(Distrito)
            consulta = consulta.filter(Distrito.id == request.form["distrito_id"])
    # Hace el query de listado
    registros = consulta.order_by(EncServicio.modificado.desc()).offset(start).limit(rows_per_page).all()
    total = consulta.count()
    # Elaborar datos para DataTable
    data = []
    for registro in registros:
        data.append(
            {
                "id": {
                    "id": registro.id,
                    "url": url_for("enc_servicios.detail", respuesta_id=registro.id),
                },
                "creado": registro.creado.strftime("%Y-%m-%d %H:%M"),
                "respuesta_01": registro.respuesta_01,
                "respuesta_02": registro.respuesta_02,
                "respuesta_03": registro.respuesta_03,
                "respuesta_04": registro.respuesta_04,
                "oficina": {
                    "clave": registro.oficina.clave,
                    "descripcion": registro.oficina.descripcion_corta,
                    "url": url_for("oficinas.detail", oficina_id=registro.oficina.id),
                },
                "estado": registro.estado,
            }
        )
    # Entregar JSON
    return output_datatable_json(draw, total, data)


@enc_servicios.route("/encuestas/servicios")
def list_active():
    """Listado de respuestas de la encuesta de servicios"""
    return render_template(
        "enc_servicios/list.jinja2",
        filtros=json.dumps({"estatus": "A"}),
        titulo="Encuesta de Servicio",
    )


@enc_servicios.route("/encuestas/servicios/<int:respuesta_id>", methods=["GET", "POST"])
def detail(respuesta_id):
    """Detalle de una respuesta"""
    detalle = EncServicio.query.get_or_404(respuesta_id)
    return render_template(
        "enc_servicios/detail.jinja2",
        filtros=json.dumps({"estatus": "A"}),
        titulo="Encuesta de Servicio",
        detalle=detalle,
    )
