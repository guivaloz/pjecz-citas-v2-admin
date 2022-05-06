"""
Autoridades, vistas
"""
import json

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from lib.datatables import get_datatable_parameters, output_datatable_json
from lib.safe_string import safe_clave, safe_string, safe_message

from citas_admin.blueprints.autoridades.models import Autoridad
from citas_admin.blueprints.autoridades.forms import AutoridadEditForm, AutoridadNewForm, AutoridadSearchForm
from citas_admin.blueprints.bitacoras.models import Bitacora
from citas_admin.blueprints.materias.models import Materia
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
    if "estatus" in request.form:
        consulta = consulta.filter_by(estatus=request.form["estatus"])
    else:
        consulta = consulta.filter_by(estatus="A")
    if "distrito_id" in request.form:
        consulta = consulta.filter_by(distrito_id=request.form["distrito_id"])
    if "materia_id" in request.form:
        consulta = consulta.filter_by(materia_id=request.form["materia_id"])
    if "clave" in request.form:
        consulta = consulta.filter(Autoridad.clave.contains(safe_string(request.form["clave"])))
    if "descripcion" in request.form:
        consulta = consulta.filter(Autoridad.descripcion.contains(safe_string(request.form["descripcion"], to_uppercase=False)))
    if "organo_jurisdiccional" in request.form:
        consulta = consulta.filter(Autoridad.organo_jurisdiccional == safe_string(request.form["organo_jurisdiccional"]))
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
                "organo_jurisdiccional": resultado.organo_jurisdiccional,
                "distrito": {
                    "nombre_corto": resultado.distrito.nombre_corto,
                    "url": url_for("distritos.detail", distrito_id=resultado.distrito_id) if current_user.can_view("DISTRITOS") else "",
                },
                "materia": {
                    "nombre": resultado.materia.nombre,
                    "url": url_for("materias.detail", materia_id=resultado.materia_id) if current_user.can_view("MATERIAS") else "",
                },
            }
        )
    # Entregar JSON
    return output_datatable_json(draw, total, data)


@autoridades.route("/autoridades")
def list_active():
    """Listado de Autoridades activos"""
    return render_template(
        "autoridades/list.jinja2",
        filtros=json.dumps({"estatus": "A"}),
        titulo="Autoridades",
        estatus="A",
    )


@autoridades.route("/autoridades/inactivos")
@permission_required(MODULO, Permiso.MODIFICAR)
def list_inactive():
    """Listado de Autoridades inactivos"""
    return render_template(
        "autoridades/list.jinja2",
        filtros=json.dumps({"estatus": "B"}),
        titulo="Autoridades inactivos",
        estatus="B",
    )


@autoridades.route("/autoridades/buscar", methods=["GET", "POST"])
def search():
    """Buscar Autoridad"""
    form_search = AutoridadSearchForm()
    if form_search.validate_on_submit():
        busqueda = {"estatus": "A"}
        titulos = []
        if form_search.descripcion.data:
            descripcion = safe_string(form_search.descripcion.data, to_uppercase=False)
            if descripcion != "":
                busqueda["descripcion"] = descripcion
                titulos.append("descripción " + descripcion)
        if form_search.clave.data:
            clave = safe_string(form_search.clave.data)
            if clave != "":
                busqueda["clave"] = clave
                titulos.append("clave " + clave)
        if form_search.organo_jurisdiccional.data:
            organo_jurisdiccional = safe_string(form_search.organo_jurisdiccional.data)
            if organo_jurisdiccional != "":
                busqueda["organo_jurisdiccional"] = organo_jurisdiccional
                titulos.append("órgano jurisdiccional " + organo_jurisdiccional)
        return render_template(
            "autoridades/list.jinja2",
            filtros=json.dumps(busqueda),
            titulo="Autoridad con " + ", ".join(titulos),
            estatus="A",
        )
    return render_template("autoridades/search.jinja2", form=form_search)


@autoridades.route("/autoridades/<int:autoridad_id>")
def detail(autoridad_id):
    """Detalle de un Autoridad"""
    autoridad = Autoridad.query.get_or_404(autoridad_id)
    return render_template("autoridades/detail.jinja2", autoridad=autoridad)


@autoridades.route("/autoridades/nuevo", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.CREAR)
def new():
    """Nueva Autoridad"""
    form = AutoridadNewForm()
    if form.validate_on_submit():
        # Validar que la clave no se repita
        clave = safe_string(form.clave.data)
        if Autoridad.query.filter_by(clave=clave).first():
            flash("La clave ya está en uso. Debe de ser única.", "warning")
        else:
            autoridad = Autoridad(
                distrito=form.distrito.data,
                descripcion=safe_string(form.descripcion.data),
                descripcion_corta=safe_string(form.descripcion_corta.data),
                clave=clave,
                es_jurisdiccional=form.es_jurisdiccional.data,
                es_notaria=form.es_notaria.data,
                organo_jurisdiccional=form.organo_jurisdiccional.data,
                materia=form.materia.data,
            )
            autoridad.save()
            bitacora = Bitacora(
                modulo=Modulo.query.filter_by(nombre=MODULO).first(),
                usuario=current_user,
                descripcion=safe_message(f"Nueva autoridad {autoridad.clave}"),
                url=url_for("autoridades.detail", autoridad_id=autoridad.id),
            )
            bitacora.save()
            flash(bitacora.descripcion, "success")
            return redirect(bitacora.url)
    form.materia.data = Materia.query.get(1)  # Materia NO DEFINIDO
    return render_template("autoridades/new.jinja2", form=form)


@autoridades.route("/autoridades/edicion/<int:autoridad_id>", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.MODIFICAR)
def edit(autoridad_id):
    """Editar Autoridad"""
    autoridad = Autoridad.query.get_or_404(autoridad_id)
    form = AutoridadEditForm()
    if form.validate_on_submit():
        es_valido = True
        # Si cambia la clave verificar que no este en uso
        clave = safe_clave(form.clave.data)
        if autoridad.clave != clave:
            oficina_existente = Autoridad.query.filter_by(clave=clave).first()
            if oficina_existente and oficina_existente.id != autoridad.id:
                es_valido = False
                flash("La clave ya está en uso. Debe de ser única.", "warning")
        # Si es valido actualizar
        if es_valido:
            autoridad.distrito = form.distrito.data
            autoridad.descripcion = safe_string(form.descripcion.data)
            autoridad.descripcion_corta = safe_string(form.descripcion_corta.data)
            autoridad.clave = clave
            autoridad.es_jurisdiccional = form.es_jurisdiccional.data
            autoridad.es_notaria = form.es_notaria.data
            autoridad.organo_jurisdiccional = form.organo_jurisdiccional.data
            autoridad.materia = form.materia.data
            autoridad.save()
            bitacora = Bitacora(
                modulo=Modulo.query.filter_by(nombre=MODULO).first(),
                usuario=current_user,
                descripcion=safe_message(f"Editada autoridad {autoridad.clave}"),
                url=url_for("autoridades.detail", autoridad_id=autoridad.id),
            )
            bitacora.save()
            flash(bitacora.descripcion, "success")
            return redirect(bitacora.url)
    form.distrito.data = autoridad.distrito
    form.descripcion.data = autoridad.descripcion
    form.descripcion_corta.data = autoridad.descripcion_corta
    form.clave.data = autoridad.clave
    form.es_jurisdiccional.data = autoridad.es_jurisdiccional
    form.es_notaria.data = autoridad.es_notaria
    form.organo_jurisdiccional.data = autoridad.organo_jurisdiccional
    form.materia.data = autoridad.materia
    return render_template("autoridades/edit.jinja2", form=form, autoridad=autoridad)


@autoridades.route("/autoridades/eliminar/<int:autoridad_id>")
@permission_required(MODULO, Permiso.MODIFICAR)
def delete(autoridad_id):
    """Eliminar Autoridad"""
    autoridad = Autoridad.query.get_or_404(autoridad_id)
    if autoridad.estatus == "A":
        autoridad.delete()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Eliminada autoridad {autoridad.clave}"),
            url=url_for("autoridades.detail", autoridad_id=autoridad.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
        return redirect(bitacora.url)
    return redirect(url_for("autoridades.detail", autoridad_id=autoridad.id))


@autoridades.route("/autoridades/recuperar/<int:autoridad_id>")
@permission_required(MODULO, Permiso.MODIFICAR)
def recover(autoridad_id):
    """Recuperar Autoridad"""
    autoridad = Autoridad.query.get_or_404(autoridad_id)
    if autoridad.estatus == "B":
        autoridad.recover()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Recuperada autoridad {autoridad.clave}"),
            url=url_for("autoridades.detail", autoridad_id=autoridad.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
        return redirect(bitacora.url)
    return redirect(url_for("autoridades.detail", autoridad_id=autoridad.id))
