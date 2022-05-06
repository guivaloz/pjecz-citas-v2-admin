"""
CITAS Días Inhábiles, vistas
"""
from datetime import datetime, time
import json

from flask import Blueprint, flash, redirect, request, render_template, url_for
from flask_login import current_user, login_required

from lib.datatables import get_datatable_parameters, output_datatable_json
from lib.safe_string import safe_string, safe_message

from citas_admin.blueprints.bitacoras.models import Bitacora
from citas_admin.blueprints.cit_servicios.models import CitServicio
from citas_admin.blueprints.cit_servicios.forms import CitServiciosForm
from citas_admin.blueprints.modulos.models import Modulo
from citas_admin.blueprints.permisos.models import Permiso
from citas_admin.blueprints.usuarios.decorators import permission_required

cit_servicios = Blueprint("cit_servicios", __name__, template_folder="templates")

MODULO = "CIT SERVICIOS"


@cit_servicios.route("/cit_servicios/datatable_json", methods=["GET", "POST"])
def datatable_json():
    """DataTable JSON para listado de servicios"""
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
                "clave": {
                    "texto": resultado.clave,
                    "url": url_for("cit_servicios.detail", servicio_id=resultado.id),
                },
                "nombre": resultado.nombre,
                "solicitar_expedientes": resultado.solicitar_expedientes,
                "duracion": resultado.duracion.strftime("%H:%M"),
            }
        )
    # Entregar JSON
    return output_datatable_json(draw, total, data)


@cit_servicios.route("/cit_servicios")
@login_required
@permission_required(MODULO, Permiso.VER)
def list_active():
    """Listado de Servicios activos"""
    return render_template(
        "cit_servicios/list.jinja2",
        filtros=json.dumps({"estatus": "A"}),
        titulo="Servicios",
        estatus="A",
    )


@cit_servicios.route("/cit_servicios/inactivos")
@login_required
@permission_required(MODULO, Permiso.MODIFICAR)
def list_inactive():
    """Listado de Servicios inactivos"""
    return render_template(
        "cit_servicios/list.jinja2",
        filtros=json.dumps({"estatus": "B"}),
        titulo="Servicios inactivos",
        estatus="B",
    )


@cit_servicios.route("/cit_servicios/<int:servicio_id>")
@login_required
@permission_required(MODULO, Permiso.VER)
def detail(servicio_id):
    """Detalle de un Servicio"""
    servicio = CitServicio.query.get_or_404(servicio_id)
    return render_template("cit_servicios/detail.jinja2", servicio=servicio)


@cit_servicios.route("/cit_servicios/nuevo", methods=["GET", "POST"])
@login_required
@permission_required(MODULO, Permiso.CREAR)
def new():
    """Nuevo Servicio"""
    form = CitServiciosForm()
    validacion = False
    if form.validate_on_submit():
        try:
            _validar(form)
            validacion = True
        except Exception as err:
            flash(f"Creación del nuevo Servicio incorrecta. {str(err)}", "warning")
            validacion = False

        if validacion:
            servicio = CitServicio(
                clave=safe_string(form.clave.data),
                nombre=safe_string(form.nombre.data),
                solicitar_expedientes=form.solicitar_expedientes.data,
                duracion=form.duracion.data,
            )
            servicio.save()
            bitacora = Bitacora(
                modulo=Modulo.query.filter_by(nombre=MODULO).first(),
                usuario=current_user,
                descripcion=safe_message(f"Nuevo Servicio {servicio.clave}"),
                url=url_for("cit_servicios.detail", servicio_id=servicio.id),
            )
            bitacora.save()
            flash(bitacora.descripcion, "success")
            return redirect(bitacora.url)
    return render_template("cit_servicios/new.jinja2", form=form)


@cit_servicios.route("/cit_servicios/edicion/<int:servicio_id>", methods=["GET", "POST"])
@login_required
@permission_required(MODULO, Permiso.MODIFICAR)
def edit(servicio_id):
    """Editar Servicio"""
    servicio = CitServicio.query.get_or_404(servicio_id)
    form = CitServiciosForm()
    validacion = False
    if form.validate_on_submit():

        try:
            _validar(form, True)
            validacion = True
        except Exception as err:
            flash(f"Actualización incorrecta del servicio. {str(err)}", "warning")
            validacion = False

        if validacion:
            servicio.clave = safe_string(form.clave.data)
            servicio.nombre = safe_string(form.nombre.data)
            servicio.solicitar_expedientes = form.solicitar_expedientes.data
            servicio.duracion = form.duracion.data
            servicio.save()
            bitacora = Bitacora(
                modulo=Modulo.query.filter_by(nombre=MODULO).first(),
                usuario=current_user,
                descripcion=safe_message(f"Editado el Servicio {servicio.clave}"),
                url=url_for("cit_servicios.detail", servicio_id=servicio.id),
            )
            bitacora.save()
            flash(bitacora.descripcion, "success")
            return redirect(bitacora.url)
    form.clave.data = servicio.clave
    form.nombre.data = servicio.nombre
    form.solicitar_expedientes.data = servicio.solicitar_expedientes
    form.duracion.data = servicio.duracion
    return render_template("cit_servicios/edit.jinja2", form=form, servicio=servicio)


def _validar(form, same=False):
    if not same:
        clave_existente = CitServicio.query.filter(CitServicio.clave == form.clave.data).first()
        if clave_existente:
            raise Exception("La clave ya se encuentra en uso.")
    min_duracion = datetime.strptime("00:15", "%H:%M")
    duracion = datetime.strptime(form.duracion.data.strftime("%H:%M"), "%H:%M")
    if duracion < min_duracion:
        min_duracion = min_duracion.strftime("%H:%M")
        raise Exception(f"La duración del servicio es muy poco, lo mínimno permitido son: {min_duracion}")
    max_duracion = datetime.strptime("08:00", "%H:%M")
    if duracion > max_duracion:
        max_duracion = max_duracion.strftime("%H:%M")
        raise Exception(f"La duración del servicio es mucho, lo máximo permitido son: {max_duracion}")
    return True


@cit_servicios.route("/cit_servicios/eliminar/<int:servicio_id>")
@login_required
@permission_required(MODULO, Permiso.MODIFICAR)
def delete(servicio_id):
    """Eliminar Servicio"""
    servicio = CitServicio.query.get_or_404(servicio_id)
    if servicio.estatus == "A":
        servicio.delete()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Eliminado el servicio {servicio.clave}"),
            url=url_for("cit_servicios.detail", servicio_id=servicio.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("cit_servicios.detail", servicio_id=servicio_id))


@cit_servicios.route("/cit_servicios/recuperar/<int:servicio_id>")
@login_required
@permission_required(MODULO, Permiso.MODIFICAR)
def recover(servicio_id):
    """Recuperar Servicio"""
    servicio = CitServicio.query.get_or_404(servicio_id)
    if servicio.estatus == "B":
        servicio.recover()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Recuperado el Servicio {servicio.clave}"),
            url=url_for("cit_servicios.detail", servicio_id=servicio.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("cit_servicios.detail", servicio_id=servicio_id))
