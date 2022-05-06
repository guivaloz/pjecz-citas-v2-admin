"""
Cit Dias Inhabiles, vistas
"""
from datetime import date, timedelta
import json

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from lib.datatables import get_datatable_parameters, output_datatable_json
from lib.safe_string import safe_string, safe_message

from citas_admin.blueprints.bitacoras.models import Bitacora
from citas_admin.blueprints.modulos.models import Modulo
from citas_admin.blueprints.permisos.models import Permiso
from citas_admin.blueprints.usuarios.decorators import permission_required
from citas_admin.blueprints.cit_dias_inhabiles.forms import CitDiaInhabilForm
from citas_admin.blueprints.cit_dias_inhabiles.models import CitDiaInhabil

MODULO = "CIT DIAS INHABILES"
LIMITE_FUTURO_DIAS = 365  # Las fechas pueden ser hasta un año en el futuro

cit_dias_inhabiles = Blueprint("cit_dias_inhabiles", __name__, template_folder="templates")


@cit_dias_inhabiles.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""


@cit_dias_inhabiles.route("/cit_dias_inhabiles/datatable_json", methods=["GET", "POST"])
def datatable_json():
    """DataTable JSON para listado de Dias Inhabiles"""
    # Tomar parámetros de Datatables
    draw, start, rows_per_page = get_datatable_parameters()
    # Consultar
    consulta = CitDiaInhabil.query
    if "estatus" in request.form:
        consulta = consulta.filter_by(estatus=request.form["estatus"])
    else:
        consulta = consulta.filter_by(estatus="A")
    registros = consulta.order_by(CitDiaInhabil.fecha.desc()).offset(start).limit(rows_per_page).all()
    total = consulta.count()
    # Elaborar datos para DataTable
    data = []
    for resultado in registros:
        data.append(
            {
                "detalle": {
                    "fecha": resultado.fecha.strftime("%Y-%m-%d 00:00:00"),
                    "url": url_for("cit_dias_inhabiles.detail", cit_dia_inhabil_id=resultado.id),
                },
                "descripcion": resultado.descripcion,
            }
        )
    # Entregar JSON
    return output_datatable_json(draw, total, data)


@cit_dias_inhabiles.route("/cit_dias_inhabiles")
def list_active():
    """Listado de Dias Inhabiles activos"""
    return render_template(
        "cit_dias_inhabiles/list.jinja2",
        filtros=json.dumps({"estatus": "A"}),
        titulo="Días Inhábiles",
        estatus="A",
    )


@cit_dias_inhabiles.route("/cit_dias_inhabiles/inactivos")
@permission_required(MODULO, Permiso.MODIFICAR)
def list_inactive():
    """Listado de Dias Inhabiles inactivos"""
    return render_template(
        "cit_dias_inhabiles/list.jinja2",
        filtros=json.dumps({"estatus": "B"}),
        titulo="Días Inhábiles inactivos",
        estatus="B",
    )


@cit_dias_inhabiles.route("/cit_dias_inhabiles/<int:cit_dia_inhabil_id>")
def detail(cit_dia_inhabil_id):
    """Detalle de un Dia inhabil"""
    cit_dia_inhabil = CitDiaInhabil.query.get_or_404(cit_dia_inhabil_id)
    return render_template("cit_dias_inhabiles/detail.jinja2", cit_dia_inhabil=cit_dia_inhabil)


@cit_dias_inhabiles.route("/cit_dias_inhabiles/nuevo", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.CREAR)
def new():
    """Nuevo Dia Inhabil"""
    form = CitDiaInhabilForm()
    if form.validate_on_submit():
        es_valido = True
        # Validar fecha
        fecha = form.fecha.data
        if fecha < date.today():
            flash("La fecha no puede estar en el pasado.", "warning")
            es_valido = False
        if fecha > date.today() + timedelta(days=LIMITE_FUTURO_DIAS):
            flash("La fecha sobrepasa el limite permitido.", "warning")
            es_valido = False
        if CitDiaInhabil.query.filter_by(fecha=fecha).first() is not None:
            flash("Esa fecha ya esta registrada.", "warning")
            es_valido = False
        # Si es valido, guardar
        if es_valido:
            cit_dia_inhabil = CitDiaInhabil(
                descripcion=safe_string(form.descripcion.data),
                fecha=fecha,
            )
            cit_dia_inhabil.save()
            bitacora = Bitacora(
                modulo=Modulo.query.filter_by(nombre=MODULO).first(),
                usuario=current_user,
                descripcion=safe_message(f"Nuevo Dia Inhabil {cit_dia_inhabil.fecha}"),
                url=url_for("cit_dias_inhabiles.detail", cit_dia_inhabil_id=cit_dia_inhabil.id),
            )
            bitacora.save()
            flash(bitacora.descripcion, "success")
            return redirect(url_for("cit_dias_inhabiles.list_active"))
    return render_template("cit_dias_inhabiles/new.jinja2", form=form)


@cit_dias_inhabiles.route("/cit_dias_inhabiles/edicion/<int:cit_dia_inhabil_id>", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.MODIFICAR)
def edit(cit_dia_inhabil_id):
    """Editar Dia Inhabil"""
    cit_dia_inhabil = CitDiaInhabil.query.get_or_404(cit_dia_inhabil_id)
    form = CitDiaInhabilForm()
    if form.validate_on_submit():
        es_valido = True
        # Validar fecha
        fecha = form.fecha.data
        if fecha < date.today():
            flash("La fecha no puede estar en el pasado.", "warning")
            es_valido = False
        if fecha > date.today() + timedelta(days=LIMITE_FUTURO_DIAS):
            flash("La fecha sobrepasa el limite permitido.", "warning")
            es_valido = False
        cit_dia_inhabil_posible = CitDiaInhabil.query.filter_by(fecha=fecha).first()
        if cit_dia_inhabil_posible is not None and cit_dia_inhabil.id != cit_dia_inhabil_posible.id:
            flash("Esa fecha ya esta usada en otro registro. ", "warning")
            es_valido = False
        # Si es valido, actualizar
        if es_valido:
            cit_dia_inhabil.descripcion = safe_string(form.descripcion.data)
            cit_dia_inhabil.fecha = fecha
            cit_dia_inhabil.save()
            bitacora = Bitacora(
                modulo=Modulo.query.filter_by(nombre=MODULO).first(),
                usuario=current_user,
                descripcion=safe_message(f"Editado Dia Inhabil {cit_dia_inhabil.fecha}"),
                url=url_for("cit_dias_inhabiles.detail", cit_dia_inhabil_id=cit_dia_inhabil.id),
            )
            bitacora.save()
            flash(bitacora.descripcion, "success")
            return redirect(url_for("cit_dias_inhabiles.list_active"))
    form.descripcion.data = cit_dia_inhabil.descripcion
    return render_template("cit_dias_inhabiles/edit.jinja2", form=form, cit_dia_inhabil=cit_dia_inhabil)


@cit_dias_inhabiles.route("/cit_dias_inhabiles/eliminar/<int:cit_dia_inhabil_id>")
@permission_required(MODULO, Permiso.MODIFICAR)
def delete(cit_dia_inhabil_id):
    """Eliminar Dia Inhabil"""
    cit_dia_inhabil = CitDiaInhabil.query.get_or_404(cit_dia_inhabil_id)
    if cit_dia_inhabil.estatus == "A":
        cit_dia_inhabil.delete()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Eliminado Dia In {cit_dia_inhabil.fecha}"),
            url=url_for("cit_dias_inhabiles.detail", cit_dia_inhabil_id=cit_dia_inhabil.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("cit_dias_inhabiles.detail", cit_dia_inhabil_id=cit_dia_inhabil.id))


@cit_dias_inhabiles.route("/cit_dias_inhabiles/recuperar/<int:cit_dia_inhabil_id>")
@permission_required(MODULO, Permiso.MODIFICAR)
def recover(cit_dia_inhabil_id):
    """Recuperar Dia Inhabil"""
    cit_dia_inhabil = CitDiaInhabil.query.get_or_404(cit_dia_inhabil_id)
    if cit_dia_inhabil.estatus == "B":
        cit_dia_inhabil.recover()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Recuperado Dia Inhabil {cit_dia_inhabil.fecha}"),
            url=url_for("cit_dias_inhabiles.detail", cit_dia_inhabil_id=cit_dia_inhabil.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("cit_dias_inhabiles.detail", cit_dia_inhabil_id=cit_dia_inhabil.id))
