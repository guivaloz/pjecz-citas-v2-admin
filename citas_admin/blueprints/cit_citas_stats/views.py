"""
Cit Citas Stats, vistas
"""

from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from lib.safe_string import safe_message

from citas_admin.blueprints.bitacoras.models import Bitacora
from citas_admin.blueprints.modulos.models import Modulo
from citas_admin.blueprints.permisos.models import Permiso
from citas_admin.blueprints.usuarios.decorators import permission_required

from .stats_citas_totales import obtener_stats_json_citas_totales, actualizar_stats_citas_totales
from .stats_estados import obtener_stats_json_estados, actualizar_stats_estados
from .models import CitCitaStats

MODULO = "CIT CITAS STATS"

cit_citas_stats = Blueprint("cit_citas_stats", __name__, template_folder="templates")


@cit_citas_stats.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""


@cit_citas_stats.route("/cit_citas_stats")
def detail():
    """Estadísticas del módulo citas"""

    return render_template("cit_citas_stats/detail.jinja2")


@cit_citas_stats.route("/cit_citas_stats/stats/<string:categoria>", methods=["GET"])
def stats(categoria):
    """Muestra la estadística indicada"""

    if categoria == CitCitaStats.CAT_CITAS_ESTADO:
        return render_template("cit_citas_stats/citas_estado.jinja2")

    return redirect("/cit_citas_stats")


@cit_citas_stats.route("/cit_citas_stats/data/<string:categoria>/<string:subcategoria>", methods=["POST", "GET"])
def stats_json(categoria, subcategoria):
    """Entrega los datos para gráficas"""

    # Entregar JSON
    if categoria == CitCitaStats.CAT_CITAS_TOTALES:
        return obtener_stats_json_citas_totales(subcategoria)
    elif categoria == CitCitaStats.CAT_CITAS_ESTADO:
        return obtener_stats_json_estados(subcategoria)

    return None


@cit_citas_stats.route("/cit_citas_stats/actualizar/<string:categoria>", methods=["GET"])
@permission_required(MODULO, Permiso.MODIFICAR)
def actualizar_stats(categoria):

    if categoria == CitCitaStats.CAT_CITAS_TOTALES:
        actualizar_stats_citas_totales()
        flash(f"Actualización individual de los datos estadísticos de citas, categoría: {categoria}", "success")
        Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Actualización individual de los datos estadísticos de citas, categoría: {categoria}"),
            url=url_for("cit_citas_stats.detail"),
        ).save()
        return redirect("/cit_citas_stats")
    elif categoria == CitCitaStats.CAT_CITAS_ESTADO:
        actualizar_stats_estados()
        flash(f"Actualización individual de los datos estadísticos de citas, categoría: {categoria}", "success")
        Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Actualización individual de los datos estadísticos de citas, categoría: {categoria}"),
            url=url_for("cit_citas_stats.detail"),
        ).save()
        return redirect(url_for("cit_citas_stats.stats", categoria=categoria))

    flash(f"No se pudo actalizar la estadística de esa categoria: {categoria}", "warning")
    return redirect("/cit_citas_stats")
