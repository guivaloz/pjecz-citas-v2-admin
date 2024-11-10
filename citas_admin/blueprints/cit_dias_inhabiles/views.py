"""
Cit Dias Inhábiles, vistas
"""

import json

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from citas_admin.blueprints.bitacoras.models import Bitacora
from citas_admin.blueprints.cit_dias_inhabiles.forms import CitDiaInhabilForm
from citas_admin.blueprints.cit_dias_inhabiles.models import CitDiaInhabil
from citas_admin.blueprints.modulos.models import Modulo
from citas_admin.blueprints.permisos.models import Permiso
from citas_admin.blueprints.usuarios.decorators import permission_required
from lib.datatables import get_datatable_parameters, output_datatable_json
from lib.safe_string import safe_message, safe_string

MODULO = "CIT DIAS INHABILES"

cit_dias_inhabiles = Blueprint("cit_dias_inhabiles", __name__, template_folder="templates")


@cit_dias_inhabiles.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""


@cit_dias_inhabiles.route("/cit_dias_inhabiles/datatable_json", methods=["GET", "POST"])
def datatable_json():
    """DataTable JSON para listado de Cit Dias Inhábiles"""
    # Tomar parámetros de Datatables
    draw, start, rows_per_page = get_datatable_parameters()
    # Consultar
    consulta = CitDiaInhabil.query
    # Primero filtrar por columnas propias
    if "estatus" in request.form:
        consulta = consulta.filter(CitDiaInhabil.estatus == request.form["estatus"])
    else:
        consulta = consulta.filter(CitDiaInhabil.estatus == "A")
    if "descripcion" in request.form:
        descripcion = safe_string(request.form["descripcion"])
        if descripcion != "":
            consulta = consulta.filter(CitDiaInhabil.descripcion.contains(descripcion))
    # Ordenar y paginar
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
    """Listado de Cit Dias Inhábiles activos"""
    return render_template(
        "cit_dias_inhabiles/list.jinja2",
        filtros=json.dumps({"estatus": "A"}),
        titulo="Días Inhábiles",
        estatus="A",
    )


@cit_dias_inhabiles.route("/cit_dias_inhabiles/inactivos")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def list_inactive():
    """Listado de Cit Dias Inhábiles inactivos"""
    return render_template(
        "cit_dias_inhabiles/list.jinja2",
        filtros=json.dumps({"estatus": "B"}),
        titulo="Días Inhábiles inactivos",
        estatus="B",
    )


@cit_dias_inhabiles.route("/cit_dias_inhabiles/<int:cit_dia_inhabil_id>")
def detail(cit_dia_inhabil_id):
    """Detalle de un Cit Dia Inhábil"""
    cit_dia_inhabil = CitDiaInhabil.query.get_or_404(cit_dia_inhabil_id)
    return render_template("cit_dias_inhabiles/detail.jinja2", cit_dia_inhabil=cit_dia_inhabil)


@cit_dias_inhabiles.route("/cit_dias_inhabiles/nuevo", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.CREAR)
def new():
    """Nuevo Dia Inhábil"""
    form = CitDiaInhabilForm()
    if form.validate_on_submit():
        # Validar que la fecha no exista
        fecha = form.fecha.data
        if CitDiaInhabil.query.filter_by(fecha=fecha).first():
            flash(f"Ya se tiene {fecha} como un Día Inhábil", "warning")
            return render_template("cit_dias_inhabiles/new.jinja2", form=form)
        # Guardar
        cit_dia_inhabil = CitDiaInhabil(
            fecha=fecha,
            descripcion=safe_string(form.descripcion.data, save_enie=True),
        )
        cit_dia_inhabil.save()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Nuevo Dia Inhábil {cit_dia_inhabil.fecha}"),
            url=url_for("cit_dias_inhabiles.detail", cit_dia_inhabil_id=cit_dia_inhabil.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
        return redirect(bitacora.url)
    return render_template("cit_dias_inhabiles/new.jinja2", form=form)


@cit_dias_inhabiles.route("/cit_dias_inhabiles/edicion/<int:cit_dia_inhabil_id>", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.MODIFICAR)
def edit(cit_dia_inhabil_id):
    """Editar Dia Inhábil"""
    cit_dia_inhabil = CitDiaInhabil.query.get_or_404(cit_dia_inhabil_id)
    form = CitDiaInhabilForm()
    if form.validate_on_submit():
        # Validar que la fecha no exista
        fecha = form.fecha.data
        posible_cit_dia_inhabil = CitDiaInhabil.query.filter_by(fecha=fecha).first()
        if posible_cit_dia_inhabil and posible_cit_dia_inhabil.id != cit_dia_inhabil.id:
            flash(f"Ya se tiene {fecha} como un Día Inhábil", "warning")
            return render_template("cit_dias_inhabiles/edit.jinja2", form=form, cit_dia_inhabil=cit_dia_inhabil)
        # Guardar
        cit_dia_inhabil.fecha = fecha
        cit_dia_inhabil.descripcion = safe_string(form.descripcion.data, save_enie=True)
        cit_dia_inhabil.save()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Editado Dia Inhábil {cit_dia_inhabil.fecha}"),
            url=url_for("cit_dias_inhabiles.detail", cit_dia_inhabil_id=cit_dia_inhabil.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
        return redirect(bitacora.url)
    form.fecha.data = cit_dia_inhabil.fecha
    form.descripcion.data = cit_dia_inhabil.descripcion
    return render_template("cit_dias_inhabiles/edit.jinja2", form=form, cit_dia_inhabil=cit_dia_inhabil)


@cit_dias_inhabiles.route("/cit_dias_inhabiles/eliminar/<int:cit_dia_inhabil_id>")
@permission_required(MODULO, Permiso.MODIFICAR)
def delete(cit_dia_inhabil_id):
    """Eliminar Dia Inhábil"""
    cit_dia_inhabil = CitDiaInhabil.query.get_or_404(cit_dia_inhabil_id)
    if cit_dia_inhabil.estatus == "A":
        cit_dia_inhabil.delete()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Eliminado Dia Inhábil {cit_dia_inhabil.fecha}"),
            url=url_for("cit_dias_inhabiles.detail", cit_dia_inhabil_id=cit_dia_inhabil.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("cit_dias_inhabiles.detail", cit_dia_inhabil_id=cit_dia_inhabil.id))


@cit_dias_inhabiles.route("/cit_dias_inhabiles/recuperar/<int:cit_dia_inhabil_id>")
@permission_required(MODULO, Permiso.MODIFICAR)
def recover(cit_dia_inhabil_id):
    """Recuperar Dia Inhábil"""
    cit_dia_inhabil = CitDiaInhabil.query.get_or_404(cit_dia_inhabil_id)
    if cit_dia_inhabil.estatus == "B":
        cit_dia_inhabil.recover()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Recuperado Dia Inhábil {cit_dia_inhabil.fecha}"),
            url=url_for("cit_dias_inhabiles.detail", cit_dia_inhabil_id=cit_dia_inhabil.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("cit_dias_inhabiles.detail", cit_dia_inhabil_id=cit_dia_inhabil.id))
