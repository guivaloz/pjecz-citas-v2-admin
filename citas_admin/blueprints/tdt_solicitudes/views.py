"""
Tres de Tres - Solicitudes, vistas
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
from citas_admin.blueprints.tdt_solicitudes.models import TdtSolicitud

MODULO = "TDT SOLICITUDES"

tdt_solicitudes = Blueprint("tdt_solicitudes", __name__, template_folder="templates")


@tdt_solicitudes.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""


@tdt_solicitudes.route("/tdt_solicitudes/datatable_json", methods=["GET", "POST"])
def datatable_json():
    """DataTable JSON para listado de solicitudes"""
    # Tomar parámetros de Datatables
    draw, start, rows_per_page = get_datatable_parameters()
    # Consultar
    consulta = TdtSolicitud.query
    if "estatus" in request.form:
        consulta = consulta.filter_by(estatus=request.form["estatus"])
    else:
        consulta = consulta.filter_by(estatus="A")
    registros = consulta.order_by(TdtSolicitud.id).offset(start).limit(rows_per_page).all()
    total = consulta.count()
    # Elaborar datos para DataTable
    data = []
    for resultado in registros:
        data.append(
            {
                "detalle": {
                    "id": resultado.id,
                    "url": url_for("tdt_solicitudes.detail", tdt_solicitud_id=resultado.id),
                },
            }
        )
    # Entregar JSON
    return output_datatable_json(draw, total, data)


@tdt_solicitudes.route("/tdt_solicitudes")
def list_active():
    """Listado de solicitudes activas"""
    return render_template(
        "tdt_solicitudes/list.jinja2",
        filtros=json.dumps({"estatus": "A"}),
        titulo="Solicitudes",
        estatus="A",
    )


@tdt_solicitudes.route("/tdt_solicitudes/inactivos")
@permission_required(MODULO, Permiso.MODIFICAR)
def list_inactive():
    """Listado de solicitudes inactivas"""
    return render_template(
        "tdt_solicitudes/list.jinja2",
        filtros=json.dumps({"estatus": "B"}),
        titulo="Solicitudes inactivos",
        estatus="B",
    )


@tdt_solicitudes.route("/tdt_solicitudes/<int:tdt_solicitud_id>")
def detail(tdt_solicitud_id):
    """Detalle de una solicitud"""
    tdt_solicitud = TdtSolicitud.query.get_or_404(tdt_solicitud_id)
    return render_template("tdt_solicitudes/detail.jinja2", tdt_solicitud=tdt_solicitud)


@tdt_solicitudes.route("/tdt_solicitudes/eliminar/<int:tdt_solicitud_id>")
@permission_required(MODULO, Permiso.MODIFICAR)
def delete(tdt_solicitud_id):
    """Eliminar solicitud"""
    tdt_solicitud = TdtSolicitud.query.get_or_404(tdt_solicitud_id)
    if tdt_solicitud.estatus == "A":
        tdt_solicitud.delete()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Eliminado solicitud {tdt_solicitud.id}"),
            url=url_for("tdt_solicitudes.detail", tdt_solicitud_id=tdt_solicitud.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("tdt_solicitudes.detail", tdt_solicitud_id=tdt_solicitud.id))


@tdt_solicitudes.route("/tdt_solicitudes/recuperar/<int:tdt_solicitud_id>")
@permission_required(MODULO, Permiso.MODIFICAR)
def recover(tdt_solicitud_id):
    """Recuperar solicitud"""
    tdt_solicitud = TdtSolicitud.query.get_or_404(tdt_solicitud_id)
    if tdt_solicitud.estatus == "B":
        tdt_solicitud.recover()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Recuperado solicitud {tdt_solicitud.id}"),
            url=url_for("tdt_solicitudes.detail", tdt_solicitud_id=tdt_solicitud.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("tdt_solicitudes.detail", tdt_solicitud_id=tdt_solicitud.id))
