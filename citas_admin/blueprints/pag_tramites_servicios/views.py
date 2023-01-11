"""
Pagos Tramites y Servicios, vistas
"""
import json
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from lib.datatables import get_datatable_parameters, output_datatable_json
from lib.safe_string import safe_clave, safe_string, safe_message

from citas_admin.blueprints.bitacoras.models import Bitacora
from citas_admin.blueprints.modulos.models import Modulo
from citas_admin.blueprints.permisos.models import Permiso
from citas_admin.blueprints.usuarios.decorators import permission_required
from citas_admin.blueprints.pag_tramites_servicios.forms import PagTramiteServicioForm
from citas_admin.blueprints.pag_tramites_servicios.models import PagTramiteServicio

MODULO = "PAG TRAMITES SERVICIOS"

pag_tramites_servicios = Blueprint("pag_tramites_servicios", __name__, template_folder="templates")


@pag_tramites_servicios.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""


@pag_tramites_servicios.route("/pag_tramites_servicios/datatable_json", methods=["GET", "POST"])
def datatable_json():
    """DataTable JSON para listado de Tramites y Servicios"""
    # Tomar parámetros de Datatables
    draw, start, rows_per_page = get_datatable_parameters()
    # Consultar
    consulta = PagTramiteServicio.query
    if "estatus" in request.form:
        consulta = consulta.filter_by(estatus=request.form["estatus"])
    else:
        consulta = consulta.filter_by(estatus="A")
    registros = consulta.order_by(PagTramiteServicio.id).offset(start).limit(rows_per_page).all()
    total = consulta.count()
    # Elaborar datos para DataTable
    data = []
    for resultado in registros:
        data.append(
            {
                "detalle": {
                    "clave": resultado.clave,
                    "url": url_for("pag_tramites_servicios.detail", pag_tramite_servicio_id=resultado.id),
                },
                "descripcion": resultado.descripcion,
                "costo": resultado.costo,
                "url": resultado.url,
            }
        )
    # Entregar JSON
    return output_datatable_json(draw, total, data)


@pag_tramites_servicios.route("/pag_tramites_servicios")
def list_active():
    """Listado de Tramites y Servicios activos"""
    return render_template(
        "pag_tramites_servicios/list.jinja2",
        filtros=json.dumps({"estatus": "A"}),
        titulo="Tramites y Servicios",
        estatus="A",
    )


@pag_tramites_servicios.route("/pag_tramites_servicios/inactivos")
@permission_required(MODULO, Permiso.MODIFICAR)
def list_inactive():
    """Listado de Tramites y Servicios inactivos"""
    return render_template(
        "pag_tramites_servicios/list.jinja2",
        filtros=json.dumps({"estatus": "B"}),
        titulo="Tramites y Servicios inactivos",
        estatus="B",
    )


@pag_tramites_servicios.route("/pag_tramites_servicios/<int:pag_tramite_servicio_id>")
def detail(pag_tramite_servicio_id):
    """Detalle de un Tramite y Servicio"""
    pag_tramite_servicio = PagTramiteServicio.query.get_or_404(pag_tramite_servicio_id)
    return render_template("pag_tramites_servicios/detail.jinja2", pag_tramite_servicio=pag_tramite_servicio)


@pag_tramites_servicios.route("/pag_tramites_servicios/nuevo", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.CREAR)
def new():
    """Nuevo Tramite y Servicio"""
    form = PagTramiteServicioForm()
    if form.validate_on_submit():
        pag_tramite_servicio = PagTramiteServicio(
            clave=safe_clave(form.clave.data),
            descripcion=safe_string(form.descripcion.data, to_uppercase=True, save_enie=True),
            costo=form.costo.data,
            url=form.url.data,
        )
        pag_tramite_servicio.save()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Nuevo Tramite y Servicio {pag_tramite_servicio.clave}"),
            url=url_for("pag_tramites_servicios.detail", pag_tramite_servicio_id=pag_tramite_servicio.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
        return redirect(bitacora.url)
    return render_template("pag_tramites_servicios/new.jinja2", form=form)


@pag_tramites_servicios.route("/pag_tramites_servicios/edicion/<int:pag_tramite_servicio_id>", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.MODIFICAR)
def edit(pag_tramite_servicio_id):
    """Editar Tramite y Servicio"""
    pag_tramite_servicio = PagTramiteServicio.query.get_or_404(pag_tramite_servicio_id)
    form = PagTramiteServicioForm()
    if form.validate_on_submit():
        pag_tramite_servicio.clave = safe_clave(form.clave.data)
        pag_tramite_servicio.descripcion = safe_string(form.descripcion.data, to_uppercase=True, save_enie=True)
        pag_tramite_servicio.costo = form.costo.data
        pag_tramite_servicio.url = form.url.data
        pag_tramite_servicio.save()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Editado Tramite y Servicio {pag_tramite_servicio.nombre}"),
            url=url_for("pag_tramites_servicios.detail", pag_tramite_servicio_id=pag_tramite_servicio.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
        return redirect(bitacora.url)
    form.clave.data = pag_tramite_servicio.clave
    form.descripcion.data = pag_tramite_servicio.descripcion
    form.costo.data = pag_tramite_servicio.costo
    form.url.data = pag_tramite_servicio.url
    return render_template("pag_tramites_servicios/edit.jinja2", form=form, pag_tramite_servicio=pag_tramite_servicio)


@pag_tramites_servicios.route("/pag_tramites_servicios/eliminar/<int:pag_tramite_servicio_id>")
@permission_required(MODULO, Permiso.MODIFICAR)
def delete(pag_tramite_servicio_id):
    """Eliminar Tramite y Servicio"""
    pag_tramite_servicio = PagTramiteServicio.query.get_or_404(pag_tramite_servicio_id)
    if pag_tramite_servicio.estatus == "A":
        pag_tramite_servicio.delete()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Eliminado Tramite y Servicio {pag_tramite_servicio.nombre}"),
            url=url_for("pag_tramites_servicios.detail", pag_tramite_servicio_id=pag_tramite_servicio.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("pag_tramites_servicios.detail", pag_tramite_servicio_id=pag_tramite_servicio.id))


@pag_tramites_servicios.route("/pag_tramites_servicios/recuperar/<int:pag_tramite_servicio_id>")
@permission_required(MODULO, Permiso.MODIFICAR)
def recover(pag_tramite_servicio_id):
    """Recuperar Tramite y Servicio"""
    pag_tramite_servicio = PagTramiteServicio.query.get_or_404(pag_tramite_servicio_id)
    if pag_tramite_servicio.estatus == "B":
        pag_tramite_servicio.recover()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Recuperado Tramite y Servicio {pag_tramite_servicio.nombre}"),
            url=url_for("pag_tramites_servicios.detail", pag_tramite_servicio_id=pag_tramite_servicio.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("pag_tramites_servicios.detail", pag_tramite_servicio_id=pag_tramite_servicio.id))
