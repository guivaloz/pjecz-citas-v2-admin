"""
Cit Citas, vistas
"""
import json
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from lib.datatables import get_datatable_parameters, output_datatable_json
from lib.safe_string import safe_message

from citas_admin.blueprints.bitacoras.models import Bitacora
from citas_admin.blueprints.modulos.models import Modulo
from citas_admin.blueprints.cit_citas.models import CitCita
from citas_admin.blueprints.permisos.models import Permiso
from citas_admin.blueprints.usuarios.decorators import permission_required

MODULO = "CIT CITAS"

cit_citas = Blueprint("cit_citas", __name__, template_folder="templates")


@cit_citas.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""


@cit_citas.route("/cit_citas/datatable_json", methods=["GET", "POST"])
def datatable_json():
    """DataTable JSON para listado de citas"""
    # Tomar parámetros de Datatables
    draw, start, rows_per_page = get_datatable_parameters()
    # Consultar
    consulta = CitCita.query
    if "estatus" in request.form:
        consulta = consulta.filter_by(estatus=request.form["estatus"])
    else:
        consulta = consulta.filter_by(estatus="A")
    if "cliente_id" in request.form:
        consulta = consulta.filter_by(cit_cliente_id=request.form["cliente_id"])
    registros = consulta.order_by(CitCita.id.desc()).offset(start).limit(rows_per_page).all()
    total = consulta.count()
    # Elaborar datos para DataTable
    data = []
    for cita in registros:
        data.append(
            {
                "detalle": {
                    "id": cita.id,
                    "url": url_for("cit_citas.detail", cit_cita_id=cita.id),
                },
                "horario": cita.inicio.strftime("%Y-%m-%d %H:%M") + " - " + cita.termino.strftime("%Y-%m-%d %H:%M"),
                "estado": cita.estado,
                "servicio": cita.cit_servicio.descripcion,
            }
        )
    # Entregar JSON
    return output_datatable_json(draw, total, data)


@cit_citas.route("/cit_citas")
def list_active():
    """Listado de Citas activas"""
    return render_template(
        "cit_citas/list.jinja2",
        filtros=json.dumps({"estatus": "A"}),
        titulo="Citas",
        estatus="A",
    )


@cit_citas.route("/cit_citas/inactivos")
@permission_required(MODULO, Permiso.MODIFICAR)
def list_inactive():
    """Listado de Citas inactivas"""
    return render_template(
        "cit_citas/list.jinja2",
        filtros=json.dumps({"estatus": "B"}),
        titulo="Citas inactivas",
        estatus="B",
    )


@cit_citas.route("/cit_citas/<int:cit_cita_id>")
def detail(cit_cita_id):
    """Detalle de una Cita"""
    cit_cita = CitCita.query.get_or_404(cit_cita_id)
    return render_template("cit_citas/detail.jinja2", cit_cita=cit_cita)


@cit_citas.route("/cit_citas/eliminar/<int:cit_cita_id>")
@permission_required(MODULO, Permiso.MODIFICAR)
def delete(cit_cita_id):
    """Eliminar Cita"""
    cit_citas = CitCita.query.get_or_404(cit_cita_id)
    if cit_citas.estatus == "A":
        cit_citas.delete()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Eliminado Cita {cit_citas.id}"),
            url=url_for("cit_citas.detail", cit_citas_id=cit_citas.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("cit_citas.detail", cit_cita_id=cit_citas.id))


@cit_citas.route("/cit_citas/recuperar/<int:cit_citas_id>")
@permission_required(MODULO, Permiso.MODIFICAR)
def recover(cit_citas_id):
    """Recuperar Cita"""
    cit_cita = CitCita.query.get_or_404(cit_citas_id)
    if cit_cita.estatus == "B":
        cit_cita.recover()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Recuperado Cita {cit_cita.id}"),
            url=url_for("cit_citas.detail", cit_cita_id=cit_cita.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("cit_citas.detail", cit_citas_id=cit_cita.id))
