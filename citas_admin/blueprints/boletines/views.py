"""
Boletines, vistas
"""
import json
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from lib.datatables import get_datatable_parameters, output_datatable_json
from lib.safe_string import safe_string, safe_message

from citas_admin.blueprints.bitacoras.models import Bitacora
from citas_admin.blueprints.boletines.forms import BoletinForm
from citas_admin.blueprints.boletines.models import Boletin
from citas_admin.blueprints.modulos.models import Modulo
from citas_admin.blueprints.permisos.models import Permiso
from citas_admin.blueprints.usuarios.decorators import permission_required

MODULO = "BOLETINES"

boletines = Blueprint("boletines", __name__, template_folder="templates")


@boletines.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""


@boletines.route("/boletines/datatable_json", methods=["GET", "POST"])
def datatable_json():
    """DataTable JSON para listado de Boletines"""
    # Tomar parámetros de Datatables
    draw, start, rows_per_page = get_datatable_parameters()
    # Consultar
    consulta = Boletin.query
    if "estatus" in request.form:
        consulta = consulta.filter_by(estatus=request.form["estatus"])
    else:
        consulta = consulta.filter_by(estatus="A")
    if "asunto" in request.form:
        consulta = consulta.filter(Boletin.asunto.contains(request.form["asunto"]))
    if "estado" in request.form:
        consulta = consulta.filter_by(estado=request.form["estado"])
    registros = consulta.order_by(Boletin.envio_programado.desc()).offset(start).limit(rows_per_page).all()
    total = consulta.count()
    # Elaborar datos para DataTable
    data = []
    for resultado in registros:
        data.append(
            {
                "detalle": {
                    "nombre": resultado.nombre,
                    "url": url_for("boletines.detail", boletin_id=resultado.id),
                },
                "envio_programado": resultado.envio_programado.strftime("%Y-%m-%d"),
                "estado": resultado.estado,
                "asunto": resultado.asunto,
            }
        )
    # Entregar JSON
    return output_datatable_json(draw, total, data)


@boletines.route("/boletines")
def list_active():
    """Listado de Boletines activos"""
    return render_template(
        "boletines/list.jinja2",
        filtros=json.dumps({"estatus": "A"}),
        titulo="Boletines",
        estatus="A",
    )


@boletines.route("/boletines/inactivos")
@permission_required(MODULO, Permiso.MODIFICAR)
def list_inactive():
    """Listado de Boletines inactivos"""
    return render_template(
        "boletines/list.jinja2",
        filtros=json.dumps({"estatus": "B"}),
        titulo="Boletines inactivos",
        estatus="B",
    )


@boletines.route("/boletines/<int:boletin_id>")
def detail(boletin_id):
    """Detalle de un Boletin"""
    boletin = Boletin.query.get_or_404(boletin_id)
    return render_template("boletines/detail.jinja2", boletin=boletin)


@boletines.route("/boletines/nuevo", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.CREAR)
def new():
    """Nuevo Boletin"""
    form = BoletinForm()
    if form.validate_on_submit():
        boletin = Boletin(
            envio_programado=form.envio_programado.data,
            estado=form.estado.data,
            asunto=safe_string(form.asunto.data),
            cabecera=form.cabecera.data,
            contenido=form.contenido.data,
            pie=form.pie.data,
        )
        boletin.save()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Nuevo Boletin {boletin.asunto}"),
            url=url_for("boletines.detail", boletin_id=boletin.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
        return redirect(bitacora.url)
    return render_template("boletines/new.jinja2", form=form)


@boletines.route("/boletines/edicion/<int:boletin_id>", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.MODIFICAR)
def edit(boletin_id):
    """Editar Boletin"""
    boletin = Boletin.query.get_or_404(boletin_id)
    form = BoletinForm()
    if form.validate_on_submit():
        boletin.envio_programado = form.envio_programado.data
        boletin.estado = form.estado.data
        boletin.asunto = safe_string(form.asunto.data)
        boletin.cabecera = form.cabecera.data
        boletin.contenido = form.contenido.data
        boletin.pie = form.pie.data
        boletin.save()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Editado Boletin {boletin.asunto}"),
            url=url_for("boletines.detail", boletin_id=boletin.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
        return redirect(bitacora.url)
    form.asunto.data = boletin.asunto
    return render_template("boletines/edit.jinja2", form=form, boletin=boletin)


@boletines.route("/boletines/eliminar/<int:boletin_id>")
@permission_required(MODULO, Permiso.MODIFICAR)
def delete(boletin_id):
    """Eliminar Boletin"""
    boletin = Boletin.query.get_or_404(boletin_id)
    if boletin.estatus == "A":
        boletin.delete()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Eliminado Boletin {boletin.asunto}"),
            url=url_for("boletines.detail", boletin_id=boletin.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("boletines.detail", boletin_id=boletin.id))


@boletines.route("/boletines/recuperar/<int:boletin_id>")
@permission_required(MODULO, Permiso.MODIFICAR)
def recover(boletin_id):
    """Recuperar Boletin"""
    boletin = Boletin.query.get_or_404(boletin_id)
    if boletin.estatus == "B":
        boletin.recover()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Recuperado Boletin {boletin.asunto}"),
            url=url_for("boletines.detail", boletin_id=boletin.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("boletines.detail", boletin_id=boletin.id))
