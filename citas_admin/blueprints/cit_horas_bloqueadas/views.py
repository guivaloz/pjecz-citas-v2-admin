"""
Cit Horas Bloqueadas, vistas
"""
import json
from datetime import date
from dateutil.relativedelta import relativedelta

from flask import Blueprint, flash, redirect, render_template, url_for, request
from flask_login import current_user, login_required
from sqlalchemy import or_

from lib.safe_string import safe_message, safe_string

from citas_admin.blueprints.bitacoras.models import Bitacora
from citas_admin.blueprints.cit_horas_bloqueadas.models import CitHoraBloqueada
from citas_admin.blueprints.cit_horas_bloqueadas.forms import CitHoraBloqueadaForm
from citas_admin.blueprints.modulos.models import Modulo
from citas_admin.blueprints.oficinas.models import Oficina
from citas_admin.blueprints.permisos.models import Permiso
from citas_admin.blueprints.usuarios.decorators import permission_required

MODULO = "CIT HORAS BLOQUEADAS"
MESES_FUTUROS = 12  # Un año a futuro, para las fechas

cit_horas_bloqueadas = Blueprint("cit_horas_bloqueadas", __name__, template_folder="templates")


@cit_horas_bloqueadas.route("/cit_horas_bloqueadas")
@login_required
@permission_required(MODULO, Permiso.VER)
def list_active():
    """Listado de Horas Bloqueadas activas"""
    activos = CitHoraBloqueada.query.filter(CitHoraBloqueada.estatus == "A").all()
    return render_template(
        "cit_horas_bloqueadas/list.jinja2",
        horas_bloqueadas=activos,
        titulo="Horas Bloqueadas",
        estatus="A",
    )


@cit_horas_bloqueadas.route("/cit_horas_bloqueadas/inactivos")
@login_required
@permission_required(MODULO, Permiso.MODIFICAR)
def list_inactive():
    """Listado de Horas Bloqueadas inactivas"""
    inactivos = CitHoraBloqueada.query.filter(CitHoraBloqueada.estatus == "B").all()
    return render_template(
        "cit_horas_bloqueadas/list.jinja2",
        horas_bloqueadas=inactivos,
        titulo="Horas Bloqueadas inactivas",
        estatus="B",
    )


@cit_horas_bloqueadas.route("/cit_horas_bloqueadas/<int:hora_bloqueada_id>")
@login_required
@permission_required(MODULO, Permiso.VER)
def detail(hora_bloqueada_id):
    """Detalle de una Hora Bloqueada"""
    hora_bloqueada = CitHoraBloqueada.query.get_or_404(hora_bloqueada_id)
    return render_template("cit_horas_bloqueadas/detail.jinja2", hora_bloqueada=hora_bloqueada)


def _validar(form: CitHoraBloqueadaForm):
    # validar fechas
    fecha = form.fecha.data
    if fecha < date.today():
        raise Exception("La fecha no puede estar en el pasado.")
    fecha_max_futura = date.today() + relativedelta(months=+MESES_FUTUROS)
    if fecha > fecha_max_futura:
        raise Exception(f"La fecha es muy futura, lo máximo permitido es: {fecha_max_futura}")
    # validar horarios
    inicio = form.inicio_tiempo.data
    termino = form.termino_tiempo.data
    if inicio > termino:
        raise Exception("El tiempo de inicio es mayor al de termino.")
    elif inicio == termino:
        raise Exception("El tiempo no tiene diferencia, contienen el mismo horario.")
    # regresar True si todo va bien
    return True


@cit_horas_bloqueadas.route("/cit_horas_bloqueadas/nuevo", methods=["GET", "POST"])
@login_required
@permission_required(MODULO, Permiso.CREAR)
def new():
    """Nuevo Hora Bloqueda"""
    form = CitHoraBloqueadaForm()
    validacion = False
    if form.validate_on_submit():
        try:
            _validar(form)
            validacion = True
        except Exception as err:
            flash(f"Error de validación: {str(err)}", "warning")
            validacion = False
        if validacion:
            hora_bloqueada = CitHoraBloqueada(
                oficina_id=form.oficina_id.data,
                fecha=form.fecha.data,
                inicio_tiempo=form.inicio_tiempo.data,
                termino_tiempo=form.termino_tiempo.data,
                descripcion=safe_string(form.descripcion.data),
            )
            hora_bloqueada.save()
            bitacora = Bitacora(
                modulo=Modulo.query.filter_by(nombre=MODULO).first(),
                usuario=current_user,
                descripcion=safe_message(f"Nueva Hora Bloqueada {hora_bloqueada.fecha}, {hora_bloqueada.inicio_tiempo}-{hora_bloqueada.termino_tiempo}"),
                url=url_for("cit_horas_bloqueadas.detail", hora_bloqueada_id=hora_bloqueada.id),
            )
            bitacora.save()
            flash(bitacora.descripcion, "success")
            return redirect(bitacora.url)
    return render_template("cit_horas_bloqueadas/new.jinja2", form=form)


@cit_horas_bloqueadas.route("/cit_horas_bloqueadas/edicion/<int:hora_bloqueada_id>", methods=["GET", "POST"])
@login_required
@permission_required(MODULO, Permiso.MODIFICAR)
def edit(hora_bloqueada_id):
    """Editar Cliente, solo al escribir la contraseña se cambia"""
    hora_bloqueada = CitHoraBloqueada.query.get_or_404(hora_bloqueada_id)
    form = CitHoraBloqueadaForm()
    validacion = False
    if form.validate_on_submit():
        try:
            _validar(form)
            validacion = True
        except Exception as err:
            flash(f"Error de validación: {str(err)}", "warning")
            validacion = False
        if validacion:
            hora_bloqueada.oficina_id = form.oficina_id.data
            hora_bloqueada.fecha = form.fecha.data
            hora_bloqueada.inicio_tiempo = (form.inicio_tiempo.data,)
            hora_bloqueada.termino_tiempo = (form.termino_tiempo.data,)
            hora_bloqueada.descripcion = safe_string(form.descripcion.data)
            hora_bloqueada.save()
            bitacora = Bitacora(
                modulo=Modulo.query.filter_by(nombre=MODULO).first(),
                usuario=current_user,
                descripcion=safe_message(f"Editado Hora Bloqueada {hora_bloqueada.fecha}, {hora_bloqueada.inicio_tiempo}-{hora_bloqueada.termino_tiempo}"),
                url=url_for("cit_horas_bloqueadas.detail", hora_bloqueada_id=hora_bloqueada.id),
            )
            bitacora.save()
            flash(bitacora.descripcion, "success")
            return redirect(bitacora.url)
    form.fecha.data = hora_bloqueada.fecha
    form.inicio_tiempo.data = hora_bloqueada.inicio_tiempo
    form.termino_tiempo.data = hora_bloqueada.termino_tiempo
    form.descripcion.data = hora_bloqueada.descripcion
    return render_template("cit_horas_bloqueadas/edit.jinja2", form=form, hora_bloqueada=hora_bloqueada)


@cit_horas_bloqueadas.route("/cit_horas_bloqueadas/eliminar/<int:hora_bloqueada_id>")
@login_required
@permission_required(MODULO, Permiso.MODIFICAR)
def delete(hora_bloqueada_id):
    """Eliminar Hora Bloqueada"""
    hora_bloqueada = CitHoraBloqueada.query.get_or_404(hora_bloqueada_id)
    if hora_bloqueada.estatus == "A":
        hora_bloqueada.delete()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Eliminada la hora bloqueada {hora_bloqueada.fecha}, {hora_bloqueada.inicio_tiempo}-{hora_bloqueada.termino_tiempo}"),
            url=url_for("cit_horas_bloqueadas.detail", hora_bloqueada_id=hora_bloqueada.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("cit_horas_bloqueadas.detail", hora_bloqueada_id=hora_bloqueada_id))


@cit_horas_bloqueadas.route("/cit_horas_bloqueadas/recuperar/<int:hora_bloqueada_id>")
@login_required
@permission_required(MODULO, Permiso.MODIFICAR)
def recover(hora_bloqueada_id):
    """Recuperar Hora Bloqueada"""
    hora_bloqueada = CitHoraBloqueada.query.get_or_404(hora_bloqueada_id)
    if hora_bloqueada.estatus == "B":
        hora_bloqueada.recover()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Recuperada la fecha {hora_bloqueada.fecha}, {hora_bloqueada.inicio_tiempo}-{hora_bloqueada.termino_tiempo}"),
            url=url_for("cit_horas_bloqueadas.detail", hora_bloqueada_id=hora_bloqueada.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("cit_horas_bloqueadas.detail", hora_bloqueada_id=hora_bloqueada_id))


@cit_horas_bloqueadas.route("/cit_horas_bloqueadas/oficinas", methods=["POST"])
@permission_required(MODULO, Permiso.MODIFICAR)
def oficinas():
    """Entrega un JSON con las oficinas encontradas"""
    # Consultar
    consulta = Oficina.query
    consulta = consulta.filter_by(estatus="A")
    if "searchString" in request.form:
        palabra_buscada = safe_string(request.form["searchString"]).upper()
        consulta = consulta.filter(or_(Oficina.clave.contains(palabra_buscada), Oficina.descripcion_corta.contains(palabra_buscada)))
    consulta = consulta.order_by(Oficina.clave).limit(10).all()
    # Elaborar datos el Select2
    results = []
    for registro in consulta:
        results.append(
            {
                "id": registro.id,
                "text": str(f"{registro.clave} — {registro.descripcion_corta}"),
            }
        )

    return {"results": results, "pagination": {"more": False}}
