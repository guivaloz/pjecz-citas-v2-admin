"""
Encuestas, vistas
"""
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required


from citas_admin.blueprints.bitacoras.models import Bitacora
from citas_admin.blueprints.modulos.models import Modulo
from citas_admin.blueprints.permisos.models import Permiso
from citas_admin.blueprints.usuarios.decorators import permission_required

MODULO = "ENC ENCUESTAS"

enc_encuestas = Blueprint("enc_encuestas", __name__, template_folder="templates")


@enc_encuestas.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""


@enc_encuestas.route("/enc_encuestas")
def list_active():
    """Listado de Modulo activos"""
    return render_template(
        "enc_encuestas/list.jinja2",
        titulo="Encuestas",
    )
