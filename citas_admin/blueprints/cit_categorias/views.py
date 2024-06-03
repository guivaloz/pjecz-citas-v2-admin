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
        consulta = consulta.filter_by(estatus=request.form["estatus"])
    else:
        consulta = consulta.filter_by(estatus="A")
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


@cit_categorias.route('/cit_categorias/<int:cit_categoria_id>')
def detail(cit_categoria_id):
    """ Detalle de un Cit Categoria """
    cit_categoria = CitCategoria.query.get_or_404(cit_categoria_id)
    return render_template('cit_categorias/detail.jinja2', cit_categoria=cit_categoria)

