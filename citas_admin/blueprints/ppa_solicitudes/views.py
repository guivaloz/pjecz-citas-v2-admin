"""
Pago de Pensiones Alimenticias - Solicitudes, vistas
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
from citas_admin.blueprints.ppa_solicitudes.models import PpaSolicitud

MODULO = "PPA SOLICITUDES"

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
                "creado": resultado.creado,
                "cit_cliente_nombre": resultado.cit_cliente.nombre,
                "distrito_nombre": resultado.distrito.nombre,
                "autoridad_clave": resultado.autoridad.clave,
                "numero_expediente": resultado.numero_expediente,
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
        titulo="Pagos de Pensiones Alimenticias - Solicitudes",
        estatus="A",
    )


@ppa_solicitudes.route("/ppa_solicitudes/inactivos")
@permission_required(MODULO, Permiso.MODIFICAR)
def list_inactive():
    """Listado de solicitudes inactivas"""
    return render_template(
        "ppa_solicitudes/list.jinja2",
        filtros=json.dumps({"estatus": "B"}),
        titulo="Pagos de Pensiones Alimenticias - Solicitudes inactivas",
        estatus="B",
    )


@ppa_solicitudes.route("/ppa_solicitudes/<int:ppa_solicitud_id>")
def detail(ppa_solicitud_id):
    """Detalle de una solicitud"""
    ppa_solicitud = PpaSolicitud.query.get_or_404(ppa_solicitud_id)
    return render_template("ppa_solicitudes/detail.jinja2", ppa_solicitud=ppa_solicitud)


@ppa_solicitudes.route("/ppa_solicitudes/eliminar/<int:ppa_solicitud_id>")
@permission_required(MODULO, Permiso.MODIFICAR)
def delete(ppa_solicitud_id):
    """Eliminar solicitud"""
    ppa_solicitud = PpaSolicitud.query.get_or_404(ppa_solicitud_id)
    if ppa_solicitud.estatus == "A":
        ppa_solicitud.delete()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Eliminado solicitud {ppa_solicitud.id}"),
            url=url_for("ppa_solicitudes.detail", ppa_solicitud_id=ppa_solicitud.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("ppa_solicitudes.detail", ppa_solicitud_id=ppa_solicitud.id))


@ppa_solicitudes.route("/ppa_solicitudes/recuperar/<int:ppa_solicitud_id>")
@permission_required(MODULO, Permiso.MODIFICAR)
def recover(ppa_solicitud_id):
    """Recuperar solicitud"""
    ppa_solicitud = PpaSolicitud.query.get_or_404(ppa_solicitud_id)
    if ppa_solicitud.estatus == "B":
        ppa_solicitud.recover()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Recuperado solicitud {ppa_solicitud.id}"),
            url=url_for("ppa_solicitudes.detail", ppa_solicitud_id=ppa_solicitud.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("ppa_solicitudes.detail", ppa_solicitud_id=ppa_solicitud.id))
