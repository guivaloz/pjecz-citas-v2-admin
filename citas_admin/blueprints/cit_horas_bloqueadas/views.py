"""
Cit Horas Bloqueadas, vistas
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
from citas_admin.blueprints.cit_horas_bloqueadas.models import CitHoraBloqueada

MODULO = "CIT HORAS BLOQUEADAS"

cit_horas_bloqueadas = Blueprint("cit_horas_bloqueadas", __name__, template_folder="templates")


@cit_horas_bloqueadas.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""


@cit_horas_bloqueadas.route("/cit_horas_bloqueadas/datatable_json", methods=["GET", "POST"])
def datatable_json():
    """DataTable JSON para listado de Cit Horas Bloqueadas"""
    # Tomar parámetros de Datatables
    draw, start, rows_per_page = get_datatable_parameters()
    # Consultar
    consulta = CitHoraBloqueada.query
    # Primero filtrar por columnas propias
    if "estatus" in request.form:
        consulta = consulta.filter_by(estatus=request.form["estatus"])
    else:
        consulta = consulta.filter_by(estatus="A")
    if "descripcion" in request.form:
        descripcion = safe_string(request.form["descripcion"], save_enie=True)
        if descripcion != "":
            consulta = consulta.filter(CitHoraBloqueada.descripcion.contains(descripcion))
    # Ordenar y paginar
    registros = consulta.order_by(CitHoraBloqueada.id).offset(start).limit(rows_per_page).all()
    total = consulta.count()
    # Elaborar datos para DataTable
    data = []
    for resultado in registros:
        data.append(
            {
                "detalle": {
                    "fecha": resultado.fecha,
                    "url": url_for("cit_horas_bloqueadas.detail", cit_hora_bloqueada_id=resultado.id),
                },
                "oficina": {
                    "clave": resultado.oficina.clave,
                    "descripcion": resultado.oficina.descripcion,
                    "url": url_for("oficinas.detail", oficina_id=resultado.oficina.id),
                },
                "inicio": resultado.inicio.strftime("%H:%M"),
                "termino": resultado.termino.strftime("%H:%M"),
                "descripcion": resultado.descripcion,
            }
        )
    # Entregar JSON
    return output_datatable_json(draw, total, data)


@cit_horas_bloqueadas.route("/cit_horas_bloqueadas")
def list_active():
    """Listado de Cit Horas Bloqueadas activas"""
    return render_template(
        "cit_horas_bloqueadas/list.jinja2",
        filtros=json.dumps({"estatus": "A"}),
        titulo="Horas Bloqueadas",
        estatus="A",
    )


@cit_horas_bloqueadas.route("/cit_horas_bloqueadas/inactivos")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def list_inactive():
    """Listado de Cit Horas Bloqueadas inactivas"""
    return render_template(
        "cit_horas_bloqueadas/list.jinja2",
        filtros=json.dumps({"estatus": "B"}),
        titulo="Horas Bloqueadas inactivas",
        estatus="B",
    )


@cit_horas_bloqueadas.route("/cit_horas_bloqueadas/<int:cit_hora_bloqueada_id>")
def detail(cit_hora_bloqueada_id):
    """Detalle de un Cit Hora Bloqueada"""
    cit_hora_bloqueada = CitHoraBloqueada.query.get_or_404(cit_hora_bloqueada_id)
    return render_template("cit_horas_bloqueadas/detail.jinja2", cit_hora_bloqueada=cit_hora_bloqueada)
