"""
Cit Oficinas Servicios, vistas
"""

import json
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from lib.datatables import get_datatable_parameters, output_datatable_json
from lib.safe_string import safe_clave, safe_string, safe_message

from citas_admin.blueprints.bitacoras.models import Bitacora
from citas_admin.blueprints.cit_servicios.models import CitServicio
from citas_admin.blueprints.modulos.models import Modulo
from citas_admin.blueprints.oficinas.models import Oficina
from citas_admin.blueprints.permisos.models import Permiso
from citas_admin.blueprints.usuarios.decorators import permission_required
from citas_admin.blueprints.cit_oficinas_servicios.models import CitOficinaServicio

MODULO = "CIT OFICINAS SERVICIOS"

cit_oficinas_servicios = Blueprint("cit_oficinas_servicios", __name__, template_folder="templates")


@cit_oficinas_servicios.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""


@cit_oficinas_servicios.route("/cit_oficinas_servicios/datatable_json", methods=["GET", "POST"])
def datatable_json():
    """DataTable JSON para listado de Cit Oficinas Servicios"""
    # Tomar parámetros de Datatables
    draw, start, rows_per_page = get_datatable_parameters()
    # Consultar
    consulta = CitOficinaServicio.query
    # Primero filtrar por columnas propias
    if "estatus" in request.form:
        consulta = consulta.filter_by(estatus=request.form["estatus"])
    else:
        consulta = consulta.filter_by(estatus="A")
    # Luego filtrar por columnas de otras tablas
    oficina_clave = ""
    if "oficina_clave" in request.form:
        oficina_clave = safe_clave(request.form["oficina_clave"])
    oficina_descripcion_corta = ""
    if "oficina_descripcion_corta" in request.form:
        oficina_descripcion_corta = safe_string(request.form["oficina_descripcion_corta"], save_enie=True)
    if oficina_clave != "" or oficina_descripcion_corta != "":
        consulta = consulta.join(Oficina)
        if oficina_clave != "":
            consulta = consulta.filter(Oficina.clave.contains(oficina_clave))
        if oficina_descripcion_corta != "":
            consulta = consulta.filter(Oficina.descripcion_corta.contains(oficina_descripcion_corta))
    cit_servicio_clave = ""
    if "cit_servicio_clave" in request.form:
        cit_servicio_clave = safe_clave(request.form["cit_servicio_clave"])
    cit_servicio_descripcion = ""
    if "cit_servicio_descripcion" in request.form:
        cit_servicio_descripcion = safe_string(request.form["cit_servicio_descripcion"], save_enie=True)
    if cit_servicio_clave != "" or cit_servicio_descripcion != "":
        consulta = consulta.join(CitServicio)
        if cit_servicio_clave != "":
            consulta = consulta.filter(CitServicio.clave.contains(cit_servicio_clave))
        if cit_servicio_descripcion != "":
            consulta = consulta.filter(CitServicio.descripcion.contains(cit_servicio_descripcion))
    # Ordenar y paginar
    registros = consulta.order_by(CitOficinaServicio.id).offset(start).limit(rows_per_page).all()
    total = consulta.count()
    # Elaborar datos para DataTable
    data = []
    for resultado in registros:
        data.append(
            {
                "detalle": {
                    "nombre": resultado.nombre,
                    "url": url_for("cit_oficinas_servicios.detail", cit_oficina_servicio_id=resultado.id),
                },
            }
        )
    # Entregar JSON
    return output_datatable_json(draw, total, data)


@cit_oficinas_servicios.route("/cit_oficinas_servicios")
def list_active():
    """Listado de Cit Oficinas Servicios activos"""
    return render_template(
        "cit_oficinas_servicios/list.jinja2",
        filtros=json.dumps({"estatus": "A"}),
        titulo="Oficinas-Servicios",
        estatus="A",
    )


@cit_oficinas_servicios.route("/cit_oficinas_servicios/inactivos")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def list_inactive():
    """Listado de Cit Oficinas Servicios inactivos"""
    return render_template(
        "cit_oficinas_servicios/list.jinja2",
        filtros=json.dumps({"estatus": "B"}),
        titulo="Oficinas-Servicios inactivos",
        estatus="B",
    )


@cit_oficinas_servicios.route("/cit_oficinas_servicios/<int:cit_oficina_servicio_id>")
def detail(cit_oficina_servicio_id):
    """Detalle de un Cit Oficina Servicio"""
    cit_oficina_servicio = CitOficinaServicio.query.get_or_404(cit_oficina_servicio_id)
    return render_template("cit_oficinas_servicios/detail.jinja2", cit_oficina_servicio=cit_oficina_servicio)