"""
Encuestas, vistas
"""
from calendar import month
import json
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from sqlalchemy.sql import func
from lib.database import SessionLocal

from lib.datatables import get_datatable_parameters, output_datatable_json

from citas_admin.blueprints.bitacoras.models import Bitacora
from citas_admin.blueprints.modulos.models import Modulo
from citas_admin.blueprints.permisos.models import Permiso
from citas_admin.blueprints.usuarios.decorators import permission_required

from citas_admin.blueprints.enc_sistemas.models import EncSistema

MODULO = "ENC SISTEMAS"

enc_sistemas = Blueprint("enc_sistemas", __name__, template_folder="templates")


@enc_sistemas.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""


@enc_sistemas.route("/encuestas/sistemas/datatable_json", methods=["GET", "POST"])
def datatable_json():
    """DataTable JSON para listado de respuestas de la encuesta de sistema"""
    # Tomar parámetros de Datatables
    draw, start, rows_per_page = get_datatable_parameters()
    # Consultar
    consulta = EncSistema.query
    if "estatus" in request.form:
        consulta = consulta.filter_by(estatus=request.form["estatus"])
    else:
        consulta = consulta.filter_by(estatus="A")
    if "desde" in request.form:
        consulta = consulta.filter(EncSistema.modificado >= request.form["desde"])
    if "hasta" in request.form:
        consulta = consulta.filter(EncSistema.modificado <= request.form["hasta"])
    if "respuesta_01" in request.form:
        consulta = consulta.filter_by(respuesta_01=request.form["respuesta_01"])
    if "estado" in request.form:
        consulta = consulta.filter_by(estado=request.form["estado"])
    # Hace el query de listado
    registros = consulta.order_by(EncSistema.id.desc()).offset(start).limit(rows_per_page).all()
    total = consulta.count()
    # Elaborar datos para DataTable
    data = []
    for registro in registros:
        data.append(
            {
                "id": {
                    "id": registro.id,
                    "url": url_for("enc_sistemas.detail", respuesta_id=registro.id),
                },
                "creado": registro.creado.strftime("%Y-%m-%d %H:%M"),
                "respuesta_01": registro.respuesta_01,
                "respuesta_02": registro.respuesta_02,
                "respuesta_03": registro.respuesta_03,
                "estado": registro.estado,
            }
        )
    # Entregar JSON
    return output_datatable_json(draw, total, data)


@enc_sistemas.route("/encuestas/sistemas")
def list_active():
    """Listado de respuestas dela encuesta del sistema"""
    fecha_actual = datetime.now()
    reportes = {
        "desde_siete_dias": (fecha_actual - timedelta(days=7)).strftime("%Y-%m-%d"),
        "desde_un_mes": (fecha_actual - relativedelta(months=1)).strftime("%Y-%m-%d"),
        "desde_tres_meses": (fecha_actual - relativedelta(months=3)).strftime("%Y-%m-%d"),
        "desde_seis_meses": (fecha_actual - relativedelta(months=6)).strftime("%Y-%m-%d"),
    }
    return render_template(
        "enc_sistemas/list.jinja2",
        filtros=json.dumps({"estatus": "A"}),
        titulo="Encuesta del Sistema",
        reportes=reportes,
    )


@enc_sistemas.route("/encuestas/sistemas/<int:respuesta_id>", methods=["GET", "POST"])
def detail(respuesta_id):
    """Detalle de una respuesta"""
    detalle = EncSistema.query.get_or_404(respuesta_id)
    return render_template(
        "enc_sistemas/detail.jinja2",
        filtros=json.dumps({"estatus": "A"}),
        titulo="Encuesta del Sistema",
        detalle=detalle,
    )


@enc_sistemas.route("/encuestas/sistemas/reporte?desde=<desde>")
def report(desde):
    """Reporte de la encuesta en un período de tiempo dado"""
    # Validar parámetros de entrada
    desde_date = None
    try:
        desde_date = datetime.strptime(desde, "%Y-%m-%d")
    except ValueError:
        flash("Error en el formato de la fecha de entrada", "danger")
        return redirect(url_for("enc_sistemas.list_active"))
    # Query de consulta de cantidad de encuestados
    db = SessionLocal()
    enc_sistemas_cantidades = (
        db.query(
            EncSistema.estado.label("estado"),
            func.count("*").label("cantidad"),
        )
        .filter(EncSistema.modificado >= desde_date)
        .group_by(EncSistema.estado)
    )

    encuestados_cantidad = 0
    encuestados_contestados = 0
    encuestados_cancelados = 0
    encuestados_pendientes = 0

    for estado, cantidad in enc_sistemas_cantidades:
        if estado == "CONTESTADO":
            encuestados_contestados = cantidad
        elif estado == "CANCELADO":
            encuestados_cancelados = cantidad
        elif estado == "PENDIENTE":
            encuestados_pendientes = cantidad
    encuestados_cantidad = encuestados_contestados + encuestados_cancelados + encuestados_pendientes

    # Cuenta de votos de la respuesta 01 ---
    votos_total = encuestados_contestados

    enc_sistemas_cantidades = (
        db.query(
            EncSistema.respuesta_01,
            func.count("*").label("cantidad"),
        )
        .filter(EncSistema.estado == "CONTESTADO")
        .filter(EncSistema.modificado >= desde_date)
        .group_by(EncSistema.respuesta_01)
    )

    val_01, val_02, val_03, val_04, val_05 = (0, 0, 0, 0, 0)

    for opcion, cantidad in enc_sistemas_cantidades.all():
        if opcion == 1:
            val_01 = cantidad
        elif opcion == 2:
            val_02 = cantidad
        elif opcion == 3:
            val_03 = cantidad
        elif opcion == 4:
            val_04 = cantidad
        elif opcion == 5:
            val_05 = cantidad

    # En caso de no tener valores o sea 0
    encuestados_cantidad = 1 if encuestados_cantidad == 0 else encuestados_cantidad
    votos_total = 1 if votos_total == 0 else votos_total

    if votos_total <= 1:
        formula_result = 0
    else:
        formula_result = ((val_01 * 1) + (val_02 * 2) + (val_03 * 3) + (val_04 * 4) + (val_05 * 5)) / votos_total
    detalle = {
        "periodo": f"{desde_date.strftime('%Y/%m/%d')} - {datetime.now().strftime('%Y/%m/%d')}",  # "2022/09/01 - 2022/09/30",
        "encuestados": encuestados_cantidad,
        "contestados": encuestados_contestados,
        "cancelados": encuestados_cancelados,
        "pendientes": encuestados_pendientes,
        "contestados_porcentaje": round((encuestados_contestados * 100) / encuestados_cantidad, 2),
        "cancelados_porcentaje": round((encuestados_cancelados * 100) / encuestados_cantidad, 2),
        "pendientes_porcentaje": round((encuestados_pendientes * 100) / encuestados_cantidad, 2),
        "total_votos": votos_total,
        "total_votos_porcentaje": round((votos_total * 100) / encuestados_cantidad),
        "votos_bien_porcentaje": round(((val_05 + val_04) * 100) / votos_total),
        "votos_normal_porcentaje": round((val_03 * 100) / votos_total),
        "votos_mal_porcentaje": round(((val_02 + val_01) * 100) / votos_total),
        "indice_satisfaccion": round(formula_result, 2),
        "resp_01_valor_05": val_05,
        "resp_01_valor_04": val_04,
        "resp_01_valor_03": val_03,
        "resp_01_valor_02": val_02,
        "resp_01_valor_01": val_01,
    }
    return render_template(
        "enc_sistemas/report.jinja2",
        filtros=json.dumps({"estatus": "A"}),
        titulo="Reporte de la Encuesta del Sistema",
        detalle=detalle,
    )
