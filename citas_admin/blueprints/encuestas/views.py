"""
Encuestas, vistas
"""
import json

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from citas_admin.blueprints.bitacoras.models import Bitacora
from citas_admin.blueprints.modulos.models import Modulo
from citas_admin.blueprints.permisos.models import Permiso
from citas_admin.blueprints.usuarios.decorators import permission_required

from citas_admin.blueprints.encuestas.models import EncuestaSistema

MODULO = "ENCUESTAS"

encuestas = Blueprint("encuestas", __name__, template_folder="templates")


@encuestas.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""


@encuestas.route("/encuestas")
def list_active():
    """Listado de Modulo activos"""
    return render_template(
        "encuestas/list.jinja2",
        filtros=json.dumps({"estatus": "A"}),
        titulo="Encuestas",
    )


@encuestas.route("/encuesta/sistema")
def detail_sistema():
    """Listado de Modulo activos"""
    return render_template(
        "encuestas/detail_sistema.jinja2",
        filtros=json.dumps({"estatus": "A"}),
        titulo="Encuesta del Sistema",
    )