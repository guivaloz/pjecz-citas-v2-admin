"""
Cit Autoridades-Servicios, vistas
"""
import json
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from lib.datatables import get_datatable_parameters, output_datatable_json
from lib.safe_string import safe_message, safe_string

from citas_admin.blueprints.autoridades.models import Autoridad
from citas_admin.blueprints.bitacoras.models import Bitacora
from citas_admin.blueprints.cit_autoridades_servicios.models import CitAutoridadServicio
from citas_admin.blueprints.cit_autoridades_servicios.forms import CitAutoridadServicioFormWithAutoridad, CitAutoridadServicioFormWithCitServicio
from citas_admin.blueprints.cit_servicios.models import CitServicio
from citas_admin.blueprints.modulos.models import Modulo
from citas_admin.blueprints.permisos.models import Permiso
from citas_admin.blueprints.usuarios.decorators import permission_required

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
    if "autoridad_id" in request.form:
        consulta = consulta.filter_by(autoridad_id=request.form["autoridad_id"])
    if "cit_servicio_id" in request.form:
        consulta = consulta.filter_by(cit_servicio_id=request.form["cit_servicio_id"])
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


@cit_autoridades_servicios.route("/cit_autoridades_servicios/nuevo_con_autoridad/<int:autoridad_id>", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.CREAR)
def new_with_autoridad(autoridad_id):
    """Nuevo Autoridad-Servicio con Autoridad"""
    autoridad = Autoridad.query.get_or_404(autoridad_id)
    form = CitAutoridadServicioFormWithAutoridad()
    if form.validate_on_submit():
        cit_servicio = form.cit_servicio.data
        descripcion = safe_string(f"{autoridad.clave} con {cit_servicio.clave}")
        cit_autoridad_servicio_existente = CitAutoridadServicio.query.filter(CitAutoridadServicio.autoridad == autoridad).filter(CitAutoridadServicio.cit_servicio == cit_servicio).first()
        if cit_autoridad_servicio_existente is not None:
            flash(f"CONFLICTO: Ya existe {descripcion}. Si esta eliminado, recupere.", "warning")
            return redirect(url_for("cit_autoridades_servicios.detail", cit_autoridad_servicio_id=cit_autoridad_servicio_existente.id))
        cit_autoridad_servicio = CitAutoridadServicio(
            autoridad=autoridad,
            cit_servicio=cit_servicio,
        )
        cit_autoridad_servicio.save()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Nuevo Autoridad-Servicio {descripcion}"),
            url=url_for("cit_autoridades_servicios.detail", cit_autoridad_servicio_id=cit_autoridad_servicio.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
        return redirect(bitacora.url)
    return render_template("cit_autoridades_servicios/new_with_autoridad.jinja2", form=form)


@cit_autoridades_servicios.route("/cit_autoridades_servicios/nuevo_con_cit_servicio/<int:cit_servicio_id>", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.CREAR)
def new_with_cit_servicio(cit_servicio_id):
    """Nuevo Autoridad-Servicio con Servicio"""
    cit_servicio = CitServicio.query.get_or_404(cit_servicio_id)
    form = CitAutoridadServicioFormWithCitServicio()
    if form.validate_on_submit():
        autoridad = form.autoridad.data
        descripcion = safe_string(f"{autoridad.clave} con {cit_servicio.clave}")
        cit_autoridad_servicio_existente = CitAutoridadServicio.query.filter(CitAutoridadServicio.autoridad == autoridad).filter(CitAutoridadServicio.cit_servicio == cit_servicio).first()
        if cit_autoridad_servicio_existente is not None:
            flash(f"CONFLICTO: Ya existe {descripcion}. Si esta eliminado, recupere.", "warning")
            return redirect(url_for("cit_autoridades_servicios.detail", cit_autoridad_servicio_id=cit_autoridad_servicio_existente.id))
        cit_autoridad_servicio = CitAutoridadServicio(
            autoridad=autoridad,
            cit_servicio=cit_servicio,
        )
        cit_autoridad_servicio.save()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Nuevo Autoridad-Servicio {descripcion}"),
            url=url_for("cit_autoridades_servicios.detail", cit_autoridad_servicio_id=cit_autoridad_servicio.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
        return redirect(bitacora.url)
    return render_template("cit_autoridades_servicios/new_with_cit_servicio.jinja2", form=form)


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
