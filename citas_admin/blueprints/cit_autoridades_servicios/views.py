"""
Cit Autoridades-Servicios, vistas
"""
import json
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from lib.datatables import get_datatable_parameters, output_datatable_json
from lib.safe_string import safe_message

from citas_admin.blueprints.bitacoras.models import Bitacora
from citas_admin.blueprints.modulos.models import Modulo
from citas_admin.blueprints.permisos.models import Permiso
from citas_admin.blueprints.usuarios.decorators import permission_required
from citas_admin.blueprints.cit_autoridades_servicios.models import CitAutoridadServicio

MODULO = "CIT AUTORIDADES SERVICIOS"

cit_autoridades_servicios = Blueprint("cit_autoridades_servicios", __name__, template_folder="templates")


@cit_autoridades_servicios.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""


@cit_autoridades_servicios.route("/cit_autoridades_servicios/datatable_json", methods=["GET", "POST"])
def datatable_json():
    """DataTable JSON para listado de Autoridades-Servicios"""
    # Tomar parámetros de Datatables
    draw, start, rows_per_page = get_datatable_parameters()
    # Consultar
    consulta = CitAutoridadServicio.query
    if "estatus" in request.form:
        consulta = consulta.filter_by(estatus=request.form["estatus"])
    else:
        consulta = consulta.filter_by(estatus="A")
    registros = consulta.order_by(CitAutoridadServicio.id).offset(start).limit(rows_per_page).all()
    total = consulta.count()
    # Elaborar datos para DataTable
    data = []
    for resultado in registros:
        data.append(
            {
                "detalle": {
                    "id": resultado.id,
                    "url": url_for("cit_autoridades_servicios.detail", cit_autoridad_servicio_id=resultado.id),
                },
                "autoridad": {
                    "autoridad_clave": resultado.autoridad.clave,
                    "url": url_for("autoridades.detail", autoridad_id=resultado.autoridad_id),
                },
                "cit_servicio": {
                    "cit_servicio_clave": resultado.cit_servicio.clave,
                    "url": url_for("cit_servicios.detail", cit_servicio_id=resultado.cit_servicio_id),
                },
            }
        )
    # Entregar JSON
    return output_datatable_json(draw, total, data)


@cit_autoridades_servicios.route("/cit_autoridades_servicios")
def list_active():
    """Listado de Autoridades-Servicios activos"""
    return render_template(
        "cit_autoridades_servicios/list.jinja2",
        filtros=json.dumps({"estatus": "A"}),
        titulo="Autoridades-Servicios",
        estatus="A",
    )


@cit_autoridades_servicios.route("/cit_autoridades_servicios/inactivos")
@permission_required(MODULO, Permiso.MODIFICAR)
def list_inactive():
    """Listado de Autoridades-Servicios inactivos"""
    return render_template(
        "cit_autoridades_servicios/list.jinja2",
        filtros=json.dumps({"estatus": "B"}),
        titulo="Autoridades-Servicios inactivos",
        estatus="B",
    )


@cit_autoridades_servicios.route("/cit_autoridades_servicios/<int:cid_autoridad_servicio_id>")
def detail(cid_autoridad_servicio_id):
    """Detalle de un Autoridad-Servicio"""
    cit_autoridad_servicio = CitAutoridadServicio.query.get_or_404(cid_autoridad_servicio_id)
    return render_template("cit_autoridades_servicios/detail.jinja2", cid_autoridad_servicio=cit_autoridad_servicio)


@cit_autoridades_servicios.route("/cit_autoridades_servicios/eliminar/<int:cit_autoridad_servicio_id>")
@permission_required(MODULO, Permiso.MODIFICAR)
def delete(cit_autoridad_servicio_id):
    """Eliminar Autoridad-Servicio"""
    cit_autoridad_servicio = CitAutoridadServicio.query.get_or_404(cit_autoridad_servicio_id)
    if cit_autoridad_servicio.estatus == "A":
        cit_autoridad_servicio.delete()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Eliminado Autoridad-Servicio {cit_autoridad_servicio.id}"),
            url=url_for("cit_autoridades_servicios.detail", cit_autoridad_servicio_id=cit_autoridad_servicio.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("cit_autoridades_servicios.detail", cit_autoridad_servicio_id=cit_autoridad_servicio.id))


@cit_autoridades_servicios.route("/cit_autoridades_servicios/recuperar/<int:cit_autoridad_servicio_id>")
@permission_required(MODULO, Permiso.MODIFICAR)
def recover(cit_autoridad_servicio_id):
    """Recuperar Autoridad-Servicio"""
    cit_autoridad_servicio = CitAutoridadServicio.query.get_or_404(cit_autoridad_servicio_id)
    if cit_autoridad_servicio.estatus == "B":
        cit_autoridad_servicio.recover()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Recuperado Autoridad-Servicio {cit_autoridad_servicio.id}"),
            url=url_for("cit_autoridades_servicios.detail", cit_autoridad_servicio_id=cit_autoridad_servicio.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("cit_autoridades_servicios.detail", cit_autoridad_servicio_id=cit_autoridad_servicio.id))
