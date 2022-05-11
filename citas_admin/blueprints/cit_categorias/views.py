"""
Cit Categorias, vistas
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
from citas_admin.blueprints.cit_categorias.models import CitCategoria
from citas_admin.blueprints.cit_categorias.forms import CitCategoriaForm

MODULO = "CIT CATEGORIAS"

cit_categorias = Blueprint("cit_categorias", __name__, template_folder="templates")


@cit_categorias.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""


@cit_categorias.route("/cit_categorias/datatable_json", methods=["GET", "POST"])
def datatable_json():
    """DataTable JSON para listado de Categorias"""
    # Tomar parámetros de Datatables
    draw, start, rows_per_page = get_datatable_parameters()
    # Consultar
    consulta = CitCategoria.query
    if "estatus" in request.form:
        consulta = consulta.filter_by(estatus=request.form["estatus"])
    else:
        consulta = consulta.filter_by(estatus="A")
    registros = consulta.order_by(CitCategoria.id).offset(start).limit(rows_per_page).all()
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
    """Listado de Categorias activas"""
    return render_template(
        "cit_categorias/list.jinja2",
        filtros=json.dumps({"estatus": "A"}),
        titulo="Categorias",
        estatus="A",
    )


@cit_categorias.route("/cit_categorias/inactivos")
@permission_required(MODULO, Permiso.MODIFICAR)
def list_inactive():
    """Listado de Categorias inactivas"""
    return render_template(
        "cit_categorias/list.jinja2",
        filtros=json.dumps({"estatus": "B"}),
        titulo="Categorias inactivas",
        estatus="B",
    )


@cit_categorias.route("/cit_categorias/<int:cit_categoria_id>")
def detail(cit_categoria_id):
    """Detalle de una Categoria"""
    cit_categoria = CitCategoria.query.get_or_404(cit_categoria_id)
    return render_template("cit_categorias/detail.jinja2", cit_categoria=cit_categoria)


@cit_categorias.route("/cit_categorias/nuevo", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.CREAR)
def new():
    """Nuevo Categoria"""
    form = CitCategoriaForm()
    if form.validate_on_submit():
        # Validar que el nombre no se repita
        nombre = safe_string(form.nombre.data)
        if CitCategoria.query.filter_by(nombre=nombre).first():
            flash("La nombre ya está en uso. Debe de ser único.", "warning")
        else:
            cit_categoria = CitCategoria(nombre=nombre)
            cit_categoria.save()
            bitacora = Bitacora(
                modulo=Modulo.query.filter_by(nombre=MODULO).first(),
                usuario=current_user,
                descripcion=safe_message(f"Nuevo Categoria {cit_categoria.nombre}"),
                url=url_for("cit_categorias.detail", cit_categoria_id=cit_categoria.id),
            )
            bitacora.save()
            flash(bitacora.descripcion, "success")
            return redirect(bitacora.url)
    return render_template("cit_categorias/new.jinja2", form=form)


@cit_categorias.route("/cit_categorias/edicion/<int:cit_categoria_id>", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.MODIFICAR)
def edit(cit_categoria_id):
    """Editar Categoria"""
    cit_categoria = CitCategoria.query.get_or_404(cit_categoria_id)
    form = CitCategoriaForm()
    if form.validate_on_submit():
        es_valido = True
        # Si cambia el nombre verificar que no este en uso
        nombre = safe_string(form.nombre.data)
        if cit_categoria.nombre != nombre:
            cit_categoria_existente = CitCategoria.query.filter_by(nombre=nombre).first()
            if cit_categoria_existente and cit_categoria_existente.id != cit_categoria.id:
                es_valido = False
                flash("El nombre ya está en uso. Debe de ser único.", "warning")
        # Si es valido actualizar
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
@permission_required(MODULO, Permiso.MODIFICAR)
def delete(cit_categoria_id):
    """Eliminar Categoria"""
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
@permission_required(MODULO, Permiso.MODIFICAR)
def recover(cit_categoria_id):
    """Recuperar Categoria"""
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
