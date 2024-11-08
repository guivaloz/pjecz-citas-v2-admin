"""
Cit Categorias, vistas
"""

import json

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from citas_admin.blueprints.bitacoras.models import Bitacora
from citas_admin.blueprints.cit_categorias.forms import CitCategoriaForm
from citas_admin.blueprints.cit_categorias.models import CitCategoria
from citas_admin.blueprints.modulos.models import Modulo
from citas_admin.blueprints.permisos.models import Permiso
from citas_admin.blueprints.usuarios.decorators import permission_required
from lib.datatables import get_datatable_parameters, output_datatable_json
from lib.safe_string import safe_message, safe_string

MODULO = "CIT CATEGORIAS"

cit_categorias = Blueprint("cit_categorias", __name__, template_folder="templates")


@cit_categorias.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""


@cit_categorias.route("/cit_categorias/datatable_json", methods=["GET", "POST"])
def datatable_json():
    """DataTable JSON para listado de Cit Categorias"""
    # Tomar parámetros de Datatables
    draw, start, rows_per_page = get_datatable_parameters()
    # Consultar
    consulta = CitCategoria.query
    # Primero filtrar por columnas propias
    if "estatus" in request.form:
        consulta = consulta.filter(CitCategoria.estatus == request.form["estatus"])
    else:
        consulta = consulta.filter(CitCategoria.estatus == "A")
    if "nombre" in request.form:
        nombre = safe_string(request.form["nombre"], save_enie=True)
        if nombre != "":
            consulta = consulta.filter(CitCategoria.nombre.contains(nombre))
    # Ordenar y paginar
    registros = consulta.order_by(CitCategoria.nombre).offset(start).limit(rows_per_page).all()
    total = consulta.count()
    # Elaborar datos para DataTable
    data = []
    for resultado in registros:
        data.append(
            {
                "detalle": {
                    "nombre": resultado.nombre,
                    "url": url_for("cit_categorias.detail", cit_categoria_id=resultado.id),
                },
            }
        )
    # Entregar JSON
    return output_datatable_json(draw, total, data)


@cit_categorias.route("/cit_categorias")
def list_active():
    """Listado de Cit Categorias activas"""
    return render_template(
        "cit_categorias/list.jinja2",
        filtros=json.dumps({"estatus": "A"}),
        titulo="Categorías",
        estatus="A",
    )


@cit_categorias.route("/cit_categorias/inactivos")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def list_inactive():
    """Listado de Cit Categorias inactivas"""
    return render_template(
        "cit_categorias/list.jinja2",
        filtros=json.dumps({"estatus": "B"}),
        titulo="Categorías inactivas",
        estatus="B",
    )


@cit_categorias.route("/cit_categorias/<int:cit_categoria_id>")
def detail(cit_categoria_id):
    """Detalle de un Cit Categoria"""
    cit_categoria = CitCategoria.query.get_or_404(cit_categoria_id)
    return render_template("cit_categorias/detail.jinja2", cit_categoria=cit_categoria)


@cit_categorias.route("/cit_categorias/nuevo", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.CREAR)
def new():
    """Nuevo Cit Categoria"""
    form = CitCategoriaForm()
    if form.validate_on_submit():
        es_valido = True
        # Validar nombre
        nombre = safe_string(form.nombre.data, save_enie=True, max_len=64)
        if nombre == "":
            es_valido = False
            flash("El nombre es incorrecto o está vacío", "warning")
        # Validar que el nombre sea único
        if CitCategoria.query.filter_by(nombre=nombre).first():
            es_valido = False
            flash("El nombre ya está en uso. Debe de ser único.", "warning")
        # Si es válido, guardar
        if es_valido:
            cit_categoria = CitCategoria(nombre=nombre)
            cit_categoria.save()
            bitacora = Bitacora(
                modulo=Modulo.query.filter_by(nombre=MODULO).first(),
                usuario=current_user,
                descripcion=safe_message(f"Nueva Categoria {cit_categoria.nombre}"),
                url=url_for("cit_categorias.detail", cit_categoria_id=cit_categoria.id),
            )
            bitacora.save()
            flash(bitacora.descripcion, "success")
            return redirect(bitacora.url)
    return render_template("cit_categorias/new.jinja2", form=form)


@cit_categorias.route("/cit_categorias/edicion/<int:cit_categoria_id>", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.MODIFICAR)
def edit(cit_categoria_id):
    """Editar Cit Categoria"""
    cit_categoria = CitCategoria.query.get_or_404(cit_categoria_id)
    form = CitCategoriaForm()
    if form.validate_on_submit():
        es_valido = True
        # Validar nombre
        nombre = safe_string(form.nombre.data, save_enie=True, max_len=64)
        if nombre == "":
            es_valido = False
            flash("El nombre es incorrecto o está vacío", "warning")
        # Si cambia el nombre verificar que no este en uso
        if cit_categoria.nombre != nombre:
            cit_categoria_existente = CitCategoria.query.filter_by(nombre=nombre).first()
            if cit_categoria_existente and cit_categoria_existente.id != cit_categoria.id:
                es_valido = False
                flash("El nombre ya está en uso. Debe de ser único.", "warning")
        # Si es válido, actualizar
        if es_valido:
            cit_categoria.nombre = nombre
            cit_categoria.save()
            bitacora = Bitacora(
                modulo=Modulo.query.filter_by(nombre=MODULO).first(),
                usuario=current_user,
                descripcion=safe_message(f"Editado Categoria {cit_categoria.nombre}"),
                url=url_for("cit_categorias.detail", cit_categoria_id=cit_categoria.id),
            )
            bitacora.save()
            flash(bitacora.descripcion, "success")
            return redirect(bitacora.url)
    form.nombre.data = cit_categoria.nombre
    return render_template("cit_categorias/edit.jinja2", form=form, cit_categoria=cit_categoria)


@cit_categorias.route("/cit_categorias/eliminar/<int:cit_categoria_id>")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def delete(cit_categoria_id):
    """Eliminar Cit Categoria"""
    cit_categoria = CitCategoria.query.get_or_404(cit_categoria_id)
    if cit_categoria.estatus == "A":
        cit_categoria.delete()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Eliminado Categoria {cit_categoria.nombre}"),
            url=url_for("cit_categorias.detail", cit_categoria_id=cit_categoria.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("cit_categorias.detail", cit_categoria_id=cit_categoria.id))


@cit_categorias.route("/cit_categorias/recuperar/<int:cit_categoria_id>")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def recover(cit_categoria_id):
    """Recuperar Cit Categoria"""
    cit_categoria = CitCategoria.query.get_or_404(cit_categoria_id)
    if cit_categoria.estatus == "B":
        cit_categoria.recover()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Recuperado Categoria {cit_categoria.nombre}"),
            url=url_for("cit_categorias.detail", cit_categoria_id=cit_categoria.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("cit_categorias.detail", cit_categoria_id=cit_categoria.id))
