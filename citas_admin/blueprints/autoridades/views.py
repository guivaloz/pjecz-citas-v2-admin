"""
Autoridades, vistas
"""

import json

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from lib.datatables import get_datatable_parameters, output_datatable_json
from lib.safe_string import safe_clave, safe_message, safe_string
from citas_admin.blueprints.autoridades.forms import AutoridadForm
from citas_admin.blueprints.autoridades.models import Autoridad
from citas_admin.blueprints.bitacoras.models import Bitacora
from citas_admin.blueprints.distritos.models import Distrito
from citas_admin.blueprints.modulos.models import Modulo
from citas_admin.blueprints.permisos.models import Permiso
from citas_admin.blueprints.usuarios.decorators import permission_required

MODULO = "AUTORIDADES"

autoridades = Blueprint("autoridades", __name__, template_folder="templates")


@autoridades.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""


@autoridades.route("/autoridades/datatable_json", methods=["GET", "POST"])
def datatable_json():
    """DataTable JSON para listado de Autoridades"""
    # Tomar parámetros de Datatables
    draw, start, rows_per_page = get_datatable_parameters()
    # Consultar
    consulta = Autoridad.query
    # Primero filtrar por columnas propias
    if "estatus" in request.form:
        consulta = consulta.filter_by(estatus=request.form["estatus"])
    else:
        consulta = consulta.filter_by(estatus="A")
    if "distrito_id" in request.form:
        consulta = consulta.filter_by(distrito_id=request.form["distrito_id"])
    if "clave" in request.form:
        try:
            clave = safe_clave(request.form["clave"])
            if clave != "":
                consulta = consulta.filter(Autoridad.clave.contains(clave))
        except ValueError:
            pass
    if "descripcion" in request.form:
        descripcion = safe_string(request.form["descripcion"], save_enie=True)
        if descripcion != "":
            consulta = consulta.filter(Autoridad.descripcion.contains(descripcion))
    # Luego filtrar por columnas de otras tablas
    if "distrito_nombre" in request.form:
        distrito_nombre = safe_string(request.form["distrito_nombre"], save_enie=True)
        if distrito_nombre != "":
            consulta = consulta.join(Distrito).filter(Distrito.nombre.contains(distrito_nombre))
    # Ordenar y paginar
    registros = consulta.order_by(Autoridad.clave).offset(start).limit(rows_per_page).all()
    total = consulta.count()
    # Elaborar datos para DataTable
    data = []
    for resultado in registros:
        data.append(
            {
                "detalle": {
                    "clave": resultado.clave,
                    "url": url_for("autoridades.detail", autoridad_id=resultado.id),
                },
                "descripcion_corta": resultado.descripcion_corta,
                "distrito": {
                    "nombre_corto": resultado.distrito.nombre_corto,
                    "url": (
                        url_for("distritos.detail", distrito_id=resultado.distrito_id)
                        if current_user.can_view("DISTRITOS")
                        else ""
                    ),
                },
            }
        )
    # Entregar JSON
    return output_datatable_json(draw, total, data)


@autoridades.route("/autoridades/select_json/<int:distrito_id>", methods=["GET", "POST"])
def select_json(distrito_id):
    """Select JSON para Autoridades"""
    # Consultar (como hay usuarios en autoridades dadas de baja, no se filtra por estatus)
    consulta = Autoridad.query.filter_by(distrito_id=distrito_id)
    # Si viene es_jurisdiccional como parametro en el URL como true o false
    if "es_jurisdiccional" in request.args:
        es_jurisdiccional = request.args["es_jurisdiccional"] == "true"
        consulta = consulta.filter_by(es_jurisdiccional=es_jurisdiccional)
    # Si viene es_notaria como parametro en el URL como true o false
    if "es_notaria" in request.args:
        es_notaria = request.args["es_notaria"] == "true"
        consulta = consulta.filter_by(es_notaria=es_notaria)
    # Si viene es_organo_especializado como parametro en el URL como true o false
    if "es_organo_especializado" in request.args:
        es_organo_especializado = request.args["es_organo_especializado"] == "true"
        consulta = consulta.filter_by(es_organo_especializado=es_organo_especializado)
    # Ordenar
    consulta = consulta.order_by(Autoridad.descripcion_corta)
    # Elaborar datos para Select
    data = []
    for resultado in consulta.all():
        data.append(
            {
                "id": resultado.id,
                "descripcion_corta": resultado.descripcion_corta,
            }
        )
    # Entregar JSON
    return json.dumps(data)


@autoridades.route("/autoridades")
def list_active():
    """Listado de Autoridades activas"""
    return render_template(
        "autoridades/list.jinja2",
        filtros=json.dumps({"estatus": "A"}),
        titulo="Autoridades",
        estatus="A",
    )


@autoridades.route("/autoridades/inactivos")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def list_inactive():
    """Listado de Autoridades inactivas"""
    return render_template(
        "autoridades/list.jinja2",
        filtros=json.dumps({"estatus": "B"}),
        titulo="Autoridades inactivas",
        estatus="B",
    )


@autoridades.route("/autoridades/<int:autoridad_id>")
def detail(autoridad_id):
    """Detalle de una Autoridad"""
    autoridad = Autoridad.query.get_or_404(autoridad_id)
    return render_template("autoridades/detail.jinja2", autoridad=autoridad)


@autoridades.route("/autoridades/nuevo", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.CREAR)
def new():
    """Nuevo Autoridad"""
    form = AutoridadForm()
    if form.validate_on_submit():
        # Validar que la clave no se repita
        clave = safe_clave(form.clave.data)
        if Autoridad.query.filter_by(clave=clave).first():
            flash("La clave ya está en uso. Debe de ser única.", "warning")
            return render_template("autoridades/new.jinja2", form=form)
        # Guardar
        distrito = Distrito.query.get_or_404(form.distrito.data)
        autoridad = Autoridad(
            distrito=distrito,
            clave=clave,
            descripcion=safe_string(form.descripcion.data, save_enie=True),
            descripcion_corta=safe_string(form.descripcion_corta.data, save_enie=True, max_len=64),
            es_jurisdiccional=form.es_jurisdiccional.data,
            es_notaria=form.es_notaria.data,
            es_organo_especializado=form.es_organo_especializado.data,
        )
        autoridad.save()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Nueva Autoridad {autoridad.clave}"),
            url=url_for("autoridades.detail", autoridad_id=autoridad.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
        return redirect(bitacora.url)
    return render_template("autoridades/new.jinja2", form=form)


@autoridades.route("/autoridades/edicion/<int:autoridad_id>", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.MODIFICAR)
def edit(autoridad_id):
    """Editar Autoridad"""
    autoridad = Autoridad.query.get_or_404(autoridad_id)
    form = AutoridadForm()
    if form.validate_on_submit():
        es_valido = True
        # Si cambia la clave verificar que no este en uso
        clave = safe_clave(form.clave.data)
        if autoridad.clave != clave:
            oficina_existente = Autoridad.query.filter_by(clave=clave).first()
            if oficina_existente and oficina_existente.id != autoridad_id:
                es_valido = False
                flash("La clave ya está en uso. Debe de ser única.", "warning")
        # Si es valido actualizar
        if es_valido:
            distrito = Distrito.query.get_or_404(form.distrito.data)
            autoridad.distrito = distrito
            autoridad.clave = clave
            autoridad.descripcion = safe_string(form.descripcion.data, save_enie=True)
            autoridad.descripcion_corta = safe_string(form.descripcion_corta.data, save_enie=True, max_len=64)
            autoridad.es_jurisdiccional = form.es_jurisdiccional.data
            autoridad.es_notaria = form.es_notaria.data
            autoridad.es_organo_especializado = form.es_organo_especializado.data
            autoridad.save()
            bitacora = Bitacora(
                modulo=Modulo.query.filter_by(nombre=MODULO).first(),
                usuario=current_user,
                descripcion=safe_message(f"Editada Autoridad {autoridad.clave}"),
                url=url_for("autoridades.detail", autoridad_id=autoridad.id),
            )
            bitacora.save()
            flash(bitacora.descripcion, "success")
            return redirect(bitacora.url)
    form.distrito.data = autoridad.distrito_id  # Usa id porque es un SelectField
    form.clave.data = autoridad.clave
    form.descripcion.data = autoridad.descripcion
    form.descripcion_corta.data = autoridad.descripcion_corta
    form.es_jurisdiccional.data = autoridad.es_jurisdiccional
    form.es_notaria.data = autoridad.es_notaria
    form.es_organo_especializado.data = autoridad.es_organo_especializado
    return render_template("autoridades/edit.jinja2", form=form, autoridad=autoridad)


@autoridades.route("/autoridades/eliminar/<int:autoridad_id>")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def delete(autoridad_id):
    """Eliminar Autoridad"""
    autoridad = Autoridad.query.get_or_404(autoridad_id)
    if autoridad.estatus == "A":
        autoridad.delete()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Eliminado Autoridad {autoridad.clave}"),
            url=url_for("autoridades.detail", autoridad_id=autoridad.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("autoridades.detail", autoridad_id=autoridad.id))


@autoridades.route("/autoridades/recuperar/<int:autoridad_id>")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def recover(autoridad_id):
    """Recuperar Autoridad"""
    autoridad = Autoridad.query.get_or_404(autoridad_id)
    if autoridad.estatus == "B":
        autoridad.recover()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Recuperado Autoridad {autoridad.clave}"),
            url=url_for("autoridades.detail", autoridad_id=autoridad.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("autoridades.detail", autoridad_id=autoridad.id))
