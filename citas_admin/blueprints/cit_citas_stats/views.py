"""
Cit Citas Stats, vistas
"""
import json
from datetime import datetime, timedelta
from flask import Blueprint, flash, redirect, render_template, request, url_for, abort
from flask_login import current_user, login_required

from lib.safe_string import safe_message

from citas_admin.blueprints.bitacoras.models import Bitacora
from citas_admin.blueprints.modulos.models import Modulo
from citas_admin.blueprints.cit_citas.models import CitCita
from citas_admin.blueprints.permisos.models import Permiso
from citas_admin.blueprints.usuarios.decorators import permission_required

from .stats import obtener_stats_json, actualizar_stats

MODULO = "CIT CITAS STATS"

cit_citas_stats = Blueprint("cit_citas_stats", __name__, template_folder="templates")


@cit_citas_stats.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""


@cit_citas_stats.route("/cit_citas_stats")
@permission_required(MODULO, Permiso.VER)
def detail():
    """Estadísticas del módulo citas"""

    return render_template(
        "cit_citas_stats/detail.jinja2",
        titulo="Estadísticas de Citas",
    )


@cit_citas_stats.route("/cit_citas_stats/data/<string:rango>", methods=["POST", "GET"])
@permission_required(MODULO, Permiso.VER)
def stats_json(rango):
    """Entrega los datos para gráficas"""

    # Entregar JSON
    return obtener_stats_json(rango)


@cit_citas_stats.route("/cit_citas_stats/actualizar", methods=["GET"])
@permission_required(MODULO, Permiso.MODIFICAR)
def actualizar_estadisticas():
    """Actualiza las estadísticas"""

    actualizar_stats()

    flash("Actualización de los datos estadísticos de citas", "success")
    return redirect("/cit_citas_stats")
