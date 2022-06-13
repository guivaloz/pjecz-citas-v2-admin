"""
Cit Horas Bloqueadas, vistas
"""
import json
from datetime import datetime, time
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from citas_admin.blueprints.oficinas.models import Oficina

from lib.datatables import get_datatable_parameters, output_datatable_json
from lib.safe_string import safe_string, safe_message

from citas_admin.blueprints.bitacoras.models import Bitacora
from citas_admin.blueprints.modulos.models import Modulo
from citas_admin.blueprints.permisos.models import Permiso
from citas_admin.blueprints.usuarios.decorators import permission_required
from citas_admin.blueprints.cit_horas_bloqueadas.models import CitHoraBloqueada
from citas_admin.blueprints.cit_horas_bloqueadas.forms import CitHoraBloqueadaForm

MODULO = "CIT HORAS BLOQUEADAS"

cit_horas_bloqueadas = Blueprint("cit_horas_bloqueadas", __name__, template_folder="templates")


@cit_horas_bloqueadas.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""


@cit_horas_bloqueadas.route("/cit_horas_bloqueadas/datatable_json", methods=["GET", "POST"])
def datatable_json():
    """DataTable JSON para listado de Horas Bloqueadas"""
    # Tomar parámetros de Datatables
    draw, start, rows_per_page = get_datatable_parameters()
    # Consultar
    consulta = CitHoraBloqueada.query
    if "estatus" in request.form:
        consulta = consulta.filter_by(estatus=request.form["estatus"])
    else:
        consulta = consulta.filter_by(estatus="A")
    registros = consulta.order_by(CitHoraBloqueada.id).offset(start).limit(rows_per_page).all()
    total = consulta.count()
    # Elaborar datos para DataTable
    data = []
    for resultado in registros:
        data.append(
            {
                "detalle": {
                    "fecha": resultado.fecha.strftime("%Y/%m/%d, %a"),
                    "url": url_for("cit_horas_bloqueadas.detail", cit_hora_bloqueada_id=resultado.id)
                },
                "oficina": {
                    "clave": resultado.oficina.clave,
                    "descripcion": resultado.oficina.descripcion,
                    "url": url_for("oficinas.detail", oficina_id=resultado.oficina.id)
                },
                "inicio": resultado.inicio.strftime("%H:%M"),
                "termino": resultado.termino.strftime("%H:%M"),
                "descripcion": resultado.descripcion,
            }
        )
    # Entregar JSON
    return output_datatable_json(draw, total, data)


@cit_horas_bloqueadas.route("/cit_horas_bloqueadas")
def list_active():
    """Listado de Horas Bloqueadas activas"""
    return render_template(
        "cit_horas_bloqueadas/list.jinja2",
        filtros=json.dumps({"estatus": "A"}),
        titulo="Horas Bloqueadas",
        estatus="A",
    )


@cit_horas_bloqueadas.route("/cit_horas_bloqueadas/inactivos")
@permission_required(MODULO, Permiso.MODIFICAR)
def list_inactive():
    """Listado de Horas Bloqueadas inactivas"""
    return render_template(
        "cit_horas_bloqueadas/list.jinja2",
        filtros=json.dumps({"estatus": "B"}),
        titulo="Horas Bloqueadas inactivas",
        estatus="B",
    )


@cit_horas_bloqueadas.route("/cit_horas_bloqueadas/<int:cit_hora_bloqueada_id>")
def detail(cit_hora_bloqueada_id):
    """Detalle de una Hora Bloqueada"""
    cit_hora_bloqueada = CitHoraBloqueada.query.get_or_404(cit_hora_bloqueada_id)
    return render_template("cit_horas_bloqueadas/detail.jinja2", cit_hora_bloqueada=cit_hora_bloqueada)


@cit_horas_bloqueadas.route("/cit_horas_bloqueadas/nuevo", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.CREAR)
def new():
    """Nueva Hora Bloqueada"""
    form = CitHoraBloqueadaForm()
    if form.validate_on_submit():
        cit_hora_bloqueada = CitHoraBloqueada(
            oficina_id=int(form.oficina.data),
            fecha=form.fecha.data,
            inicio=form.inicio_tiempo.data,
            termino=form.termino_tiempo.data,
            descripcion=safe_string(form.descripcion.data),
            )
        cit_hora_bloqueada.save()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Nuevo Hora Bloqueada {cit_hora_bloqueada.fecha}"),
            url=url_for("cit_horas_bloqueadas.detail", cit_hora_bloqueada_id=cit_hora_bloqueada.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
        return redirect(bitacora.url)
    return render_template("cit_horas_bloqueadas/new.jinja2", form=form)


@cit_horas_bloqueadas.route("/cit_horas_bloqueadas/edicion/<int:cit_hora_bloqueada_id>", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.MODIFICAR)
def edit(cit_hora_bloqueada_id):
    """Editar Hora Bloqueada"""
    cit_hora_bloqueada = CitHoraBloqueada.query.get_or_404(cit_hora_bloqueada_id)
    form = CitHoraBloqueadaForm()
    if form.validate_on_submit():
        cit_hora_bloqueada.fecha = form.fecha.data
        cit_hora_bloqueada.inicio = form.inicio_tiempo.data
        cit_hora_bloqueada.termino = form.termino_tiempo.data
        cit_hora_bloqueada.descripcion = safe_string(form.descripcion.data)
        cit_hora_bloqueada.save()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Editado Hora Bloqueada {cit_hora_bloqueada.fecha} a las {cit_hora_bloqueada.inicio}"),
            url=url_for("cit_horas_bloqueadas.detail", cit_hora_bloqueada_id=cit_hora_bloqueada.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
        return redirect(bitacora.url)
    form.fecha.data = cit_hora_bloqueada.fecha
    form.inicio_tiempo.data = cit_hora_bloqueada.inicio
    form.termino_tiempo.data = cit_hora_bloqueada.termino
    form.descripcion.data = cit_hora_bloqueada.descripcion
    return render_template("cit_horas_bloqueadas/edit.jinja2", form=form, cit_hora_bloqueada=cit_hora_bloqueada)


@cit_horas_bloqueadas.route("/cit_horas_bloqueadas/eliminar/<int:cit_hora_bloqueada_id>")
@permission_required(MODULO, Permiso.MODIFICAR)
def delete(cit_hora_bloqueada_id):
    """Eliminar Hora Bloqueada"""
    cit_hora_bloqueada = CitHoraBloqueada.query.get_or_404(cit_hora_bloqueada_id)
    if cit_hora_bloqueada.estatus == "A":
        cit_hora_bloqueada.delete()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Eliminado Hora  {cit_hora_bloqueada.fecha}"),
            url=url_for("cit_horas_bloqueadas.detail", cit_hora_bloqueada_id=cit_hora_bloqueada.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("cit_horas_bloqueadas.detail", cit_hora_bloqueada_id=cit_hora_bloqueada.id))


@cit_horas_bloqueadas.route("/cit_horas_bloqueadas/recuperar/<int:cit_hora_bloqueada_id>")
@permission_required(MODULO, Permiso.MODIFICAR)
def recover(cit_hora_bloqueada_id):
    """Recuperar Hora Bloqueada"""
    cit_hora_bloqueada = CitHoraBloqueada.query.get_or_404(cit_hora_bloqueada_id)
    if cit_hora_bloqueada.estatus == "B":
        cit_hora_bloqueada.recover()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Recuperado Hora  {cit_hora_bloqueada.fecha}"),
            url=url_for("cit_horas_bloqueadas.detail", cit_hora_bloqueada_id=cit_hora_bloqueada.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("cit_horas_bloqueadas.detail", cit_hora_bloqueada_id=cit_hora_bloqueada.id))
