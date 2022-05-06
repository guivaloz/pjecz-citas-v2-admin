"""
Cit Clientes, vistas
"""
import json

from flask import Blueprint, request, render_template, url_for
from flask_login import login_required

from lib.datatables import get_datatable_parameters, output_datatable_json
from lib.safe_string import safe_string

from citas_admin.blueprints.cit_clientes.models import CitCliente
from citas_admin.blueprints.cit_clientes.forms import CitClienteSearchForm
from citas_admin.blueprints.permisos.models import Permiso
from citas_admin.blueprints.usuarios.decorators import permission_required

MODULO = "CIT CLIENTES"
RENOVACION_CONTRASENA_DIAS = 360

cit_clientes = Blueprint("cit_clientes", __name__, template_folder="templates")


@cit_clientes.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""


@cit_clientes.route("/cit_clientes/datatable_json", methods=["GET", "POST"])
def datatable_json():
    """DataTable JSON para listado de clientes"""
    # Tomar parámetros de Datatables
    draw, start, rows_per_page = get_datatable_parameters()
    # Consultar
    consulta = CitCliente.query
    if "estatus" in request.form:
        consulta = consulta.filter_by(estatus=request.form["estatus"])
    else:
        consulta = consulta.filter_by(estatus="A")
    if "nombres" in request.form:
        consulta = consulta.filter(CitCliente.nombres.contains(safe_string(request.form["nombres"])))
    if "apellido_paterno" in request.form:
        consulta = consulta.filter(CitCliente.apellido_paterno.contains(safe_string(request.form["apellido_paterno"])))
    if "apellido_materno" in request.form:
        consulta = consulta.filter(CitCliente.apellido_materno.contains(safe_string(request.form["apellido_materno"])))
    if "curp" in request.form:
        consulta = consulta.filter(CitCliente.curp.contains(safe_string(request.form["curp"])))
    if "email" in request.form:
        consulta = consulta.filter(CitCliente.email.contains(request.form["email"]))
    registros = consulta.order_by(CitCliente.id.desc()).offset(start).limit(rows_per_page).all()
    total = consulta.count()
    # Elaborar datos para DataTable
    data = []
    for cliente in registros:
        data.append(
            {
                "detalle": {
                    "id": cliente.id,
                    "url": url_for("cit_clientes.detail", cliente_id=cliente.id),
                },
                "nombre": cliente.nombre,
                "email": cliente.email,
            }
        )
    # Entregar JSON
    return output_datatable_json(draw, total, data)


@cit_clientes.route("/cit_clientes")
@login_required
@permission_required(MODULO, Permiso.VER)
def list_active():
    """Listado de Clientes activos"""
    return render_template(
        "cit_clientes/list.jinja2",
        filtros=json.dumps({"estatus": "A"}),
        titulo="Clientes",
        estatus="A",
    )


@cit_clientes.route("/cit_clientes/inactivos")
@login_required
@permission_required(MODULO, Permiso.MODIFICAR)
def list_inactive():
    """Listado de Clientes inactivos"""
    return render_template(
        "cit_clientes/list.jinja2",
        filtros=json.dumps({"estatus": "B"}),
        titulo="Clientes inactivos",
        estatus="B",
    )


@cit_clientes.route("/cit_clientes/<int:cliente_id>")
@login_required
@permission_required(MODULO, Permiso.VER)
def detail(cliente_id):
    """Detalle de un Cliente"""
    cliente = CitCliente.query.get_or_404(cliente_id)
    return render_template("cit_clientes/detail.jinja2", cliente=cliente)


@cit_clientes.route("/cit_clientes/buscar", methods=["GET", "POST"])
def search():
    """Buscar un Cliente"""
    form_search = CitClienteSearchForm()
    if form_search.validate_on_submit():
        busqueda = {"estatus": "A"}
        titulos = []
        # Nombres
        if form_search.nombres.data:
            busqueda["nombres"] = form_search.nombres.data
            titulos.append("nombre " + busqueda["nombres"])
        if form_search.apellido_paterno.data:
            busqueda["apellido_paterno"] = form_search.apellido_paterno.data
            titulos.append("apellido " + busqueda["apellido_paterno"])
        if form_search.apellido_materno.data:
            busqueda["apellido_materno"] = form_search.apellido_materno.data
            titulos.append("apellido " + busqueda["apellido_materno"])
        # CURP
        if form_search.curp.data:
            busqueda["curp"] = safe_string(form_search.curp.data)
            titulos.append("CURP: " + busqueda["curp"])
        # email
        if form_search.email.data:
            busqueda["email"] = form_search.email.data
            titulos.append("e-mail " + busqueda["email"])
        # Mostrar resultados
        return render_template(
            "cit_clientes/list.jinja2",
            filtros=json.dumps(busqueda),
            titulo="Clientes con " + ", ".join(titulos),
        )
    return render_template("cit_clientes/search.jinja2", form=form_search)
