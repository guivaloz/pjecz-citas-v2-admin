"""
Cit Tramites Servicios, vistas
"""
import json
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from lib.datatables import get_datatable_parameters, output_datatable_json
from lib.safe_string import safe_string, safe_message, safe_text

from citas_admin.blueprints.bitacoras.models import Bitacora
from citas_admin.blueprints.modulos.models import Modulo
from citas_admin.blueprints.permisos.models import Permiso
from citas_admin.blueprints.usuarios.decorators import permission_required

from citas_admin.blueprints.cit_tramites_servicios.models import CitTramiteServicio
from citas_admin.blueprints.cit_tramites_servicios.forms import CitTramiteServicioForm

MODULO = "CIT TRAMITES SERVICIOS"

cit_tramites_servicios = Blueprint("cit_tramites_servicios", __name__, template_folder="templates")


@cit_tramites_servicios.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""


@cit_tramites_servicios.route("/cit_tramites_servicios/datatable_json", methods=["GET", "POST"])
def datatable_json():
    """DataTable JSON para listado de Cit Tramites y Servicios"""
    # Tomar parámetros de Datatables
    draw, start, rows_per_page = get_datatable_parameters()
    # Consultar
    consulta = CitTramiteServicio.query
    if "estatus" in request.form:
        consulta = consulta.filter_by(estatus=request.form["estatus"])
    else:
        consulta = consulta.filter_by(estatus="A")
    registros = consulta.order_by(CitTramiteServicio.id).offset(start).limit(rows_per_page).all()
    total = consulta.count()
    # Elaborar datos para DataTable
    data = []
    for resultado in registros:
        data.append(
            {
                "nombre": {
                    "nombre": resultado.nombre,
                    "url": url_for("cit_tramites_servicios.detail", cit_tramite_servicio_id=resultado.id),
                },
                "costo": format(resultado.costo, ","),
                "url": resultado.url,
            }
        )
    # Entregar JSON
    return output_datatable_json(draw, total, data)


@cit_tramites_servicios.route("/cit_tramites_servicios")
def list_active():
    """Listado de Cit Tramites y Servicios activos"""
    return render_template(
        "cit_tramites_servicios/list.jinja2",
        filtros=json.dumps({"estatus": "A"}),
        titulo="Tramites y Servicios",
        estatus="A",
    )


@cit_tramites_servicios.route("/cit_tramites_servicios/inactivos")
@permission_required(MODULO, Permiso.MODIFICAR)
def list_inactive():
    """Listado de Cit Tramites y Servicios inactivos"""
    return render_template(
        "cit_tramites_servicios/list.jinja2",
        filtros=json.dumps({"estatus": "B"}),
        titulo="Tramites y Servicios inactivos",
        estatus="B",
    )


@cit_tramites_servicios.route("/cit_tramites_servicios/<int:cit_tramite_servicio_id>")
def detail(cit_tramite_servicio_id):
    """Detalle de un Cit Tramite y Servicio"""
    cit_tramite_servicio = CitTramiteServicio.query.get_or_404(cit_tramite_servicio_id)
    return render_template("cit_tramites_servicios/detail.jinja2", cit_tramite_servicio=cit_tramite_servicio)


@cit_tramites_servicios.route("/cit_tramites_servicios/nuevo", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.CREAR)
def new():
    """Nuevo Cit Tramites y Servicios"""
    form = CitTramiteServicioForm()
    if form.validate_on_submit():
        cit_tramite_servicio = CitTramiteServicio(
            nombre=safe_string(form.nombre.data),
            costo=form.costo.data,
            url=safe_text(form.url.data, to_uppercase=False),
        )
        cit_tramite_servicio.save()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Nuevo Cit Tramites y Servicios {cit_tramite_servicio.nombre}"),
            url=url_for("cit_tramites_servicios.detail", cit_tramite_servicio_id=cit_tramite_servicio.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
        return redirect(bitacora.url)
    return render_template("cit_tramites_servicios/new.jinja2", form=form)


@cit_tramites_servicios.route("/cit_tramites_servicios/edicion/<int:cit_tramite_servicio_id>", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.MODIFICAR)
def edit(cit_tramite_servicio_id):
    """Editar Tramites y Servicios"""
    cit_tramite_servicio = CitTramiteServicio.query.get_or_404(cit_tramite_servicio_id)
    form = CitTramiteServicioForm()
    if form.validate_on_submit():
        cit_tramite_servicio.nombre = safe_string(form.nombre.data)
        cit_tramite_servicio.costo = form.costo.data
        cit_tramite_servicio.url = safe_text(form.url.data, to_uppercase=False)
        cit_tramite_servicio.save()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Editado Tramites y Servicios {cit_tramite_servicio.nombre}"),
            url=url_for("cit_tramites_servicios.detail", cit_tramite_servicio_id=cit_tramite_servicio.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
        return redirect(bitacora.url)
    form.nombre.data = cit_tramite_servicio.nombre
    form.costo.data = cit_tramite_servicio.costo
    form.url.data = cit_tramite_servicio.url
    return render_template("cit_tramites_servicios/edit.jinja2", form=form, cit_tramite_servicio=cit_tramite_servicio)


@cit_tramites_servicios.route("/cit_tramites_servicios/eliminar/<int:cit_tramite_servicio_id>")
@permission_required(MODULO, Permiso.MODIFICAR)
def delete(cit_tramite_servicio_id):
    """Eliminar Tramite y Servicio"""
    cit_tramite_servicio = CitTramiteServicio.query.get_or_404(cit_tramite_servicio_id)
    if cit_tramite_servicio.estatus == "A":
        cit_tramite_servicio.delete()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Eliminado Tramite y Servicio {cit_tramite_servicio.nombre}"),
            url=url_for("cit_tramites_servicios.detail", cit_tramite_servicio_id=cit_tramite_servicio.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("cit_tramites_servicios.detail", cit_tramite_servicio_id=cit_tramite_servicio.id))


@cit_tramites_servicios.route("/cit_tramites_servicios/recuperar/<int:cit_tramite_servicio_id>")
@permission_required(MODULO, Permiso.MODIFICAR)
def recover(cit_tramite_servicio_id):
    """Recuperar Tramites y Servicios"""
    cit_tramite_servicio = CitTramiteServicio.query.get_or_404(cit_tramite_servicio_id)
    if cit_tramite_servicio.estatus == "B":
        cit_tramite_servicio.recover()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Recuperado Tramites y Servicios {cit_tramite_servicio.nombre}"),
            url=url_for("cit_tramites_servicios.detail", cit_tramite_servicio_id=cit_tramite_servicio.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("cit_tramites_servicios.detail", cit_tramite_servicio_id=cit_tramite_servicio.id))
