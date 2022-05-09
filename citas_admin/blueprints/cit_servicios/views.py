"""
Cit Servicios, vistas
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
from citas_admin.blueprints.cit_servicios.models import CitServicio
from citas_admin.blueprints.cit_servicios.forms import CitServicioForm

MODULO = "CIT SERVICIOS"

cit_servicios = Blueprint("cit_servicios", __name__, template_folder="templates")


@cit_servicios.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""


@cit_servicios.route("/cit_servicios/datatable_json", methods=["GET", "POST"])
def datatable_json():
    """DataTable JSON para listado de Servicios"""
    # Tomar parámetros de Datatables
    draw, start, rows_per_page = get_datatable_parameters()
    # Consultar
    consulta = CitServicio.query
    if "estatus" in request.form:
        consulta = consulta.filter_by(estatus=request.form["estatus"])
    else:
        consulta = consulta.filter_by(estatus="A")
    registros = consulta.order_by(CitServicio.id).offset(start).limit(rows_per_page).all()
    total = consulta.count()
    # Elaborar datos para DataTable
    data = []
    for resultado in registros:
        data.append(
            {
                "detalle": {
                    "clave": resultado.clave,
                    "url": url_for("cit_servicios.detail", cit_servicio_id=resultado.id),
                },
                "descripcion": resultado.descripcion,
                "duracion": resultado.duracion,
                "documentos_limite": resultado.documentos_limite,
                "categoria": resultado.categoria.nombre,
            }
        )
    # Entregar JSON
    return output_datatable_json(draw, total, data)


@cit_servicios.route("/cit_servicios")
def list_active():
    """Listado de Servicios activos"""
    return render_template(
        "cit_servicios/list.jinja2",
        filtros=json.dumps({"estatus": "A"}),
        titulo="Servicios",
        estatus="A",
    )


@cit_servicios.route("/cit_servicios/inactivos")
@permission_required(MODULO, Permiso.MODIFICAR)
def list_inactive():
    """Listado de Servicios inactivos"""
    return render_template(
        "cit_servicios/list.jinja2",
        filtros=json.dumps({"estatus": "B"}),
        titulo="Servicios inactivos",
        estatus="B",
    )


@cit_servicios.route("/cit_servicios/<int:cit_servicio_id>")
def detail(cit_servicio_id):
    """Detalle de un Servicio"""
    cit_servicio = CitServicio.query.get_or_404(cit_servicio_id)
    return render_template("cit_servicios/detail.jinja2", cit_servicio=cit_servicio)


@cit_servicios.route("/cit_servicios/nuevo", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.CREAR)
def new():
    """Nuevo Servicio"""
    form = CitServicioForm()
    if form.validate_on_submit():
        cit_servicio = CitServicio(descripcion=safe_string(form.descripcion.data))
        cit_servicio.save()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Nuevo Servicio {cit_servicio.descripcion}"),
            url=url_for("cit_servicios.detail", cit_servicio_id=cit_servicio.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
        return redirect(bitacora.url)
    return render_template("cit_servicios/new.jinja2", form=form)


@cit_servicios.route("/cit_servicios/edicion/<int:cit_servicio_id>", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.MODIFICAR)
def edit(cit_servicio_id):
    """Editar Servicio"""
    cit_servicio = CitServicio.query.get_or_404(cit_servicio_id)
    form = CitServicioForm()
    if form.validate_on_submit():
        cit_servicio.descripcion = safe_string(form.descripcion.data)
        cit_servicio.save()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Editado Ser {cit_servicio.descripcion}"),
            url=url_for("cit_servicios.detail", cit_servicio_id=cit_servicio.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
        return redirect(bitacora.url)
    form.descripcion.data = cit_servicio.descripcion
    return render_template("cit_servicios/edit.jinja2", form=form, cit_servicio=cit_servicio)


@cit_servicios.route("/cit_servicios/eliminar/<int:cit_servicio_id>")
@permission_required(MODULO, Permiso.MODIFICAR)
def delete(cit_servicio_id):
    """Eliminar Servicio"""
    cit_servicio = CitServicio.query.get_or_404(cit_servicio_id)
    if cit_servicio.estatus == "A":
        cit_servicio.delete()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Eliminado Servi {cit_servicio.descripcion}"),
            url=url_for("cit_servicios.detail", cit_servicio_id=cit_servicio.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("cit_servicios.detail", cit_servicio_id=cit_servicio.id))


@cit_servicios.route("/cit_servicios/recuperar/<int:cit_servicio_id>")
@permission_required(MODULO, Permiso.MODIFICAR)
def recover(cit_servicio_id):
    """Recuperar Servicio"""
    cit_servicio = CitServicio.query.get_or_404(cit_servicio_id)
    if cit_servicio.estatus == "B":
        cit_servicio.recover()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Recuperado Servicio {cit_servicio.descripcion}"),
            url=url_for("cit_servicios.detail", cit_servicio_id=cit_servicio.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("cit_servicios.detail", cit_servicio_id=cit_servicio.id))
