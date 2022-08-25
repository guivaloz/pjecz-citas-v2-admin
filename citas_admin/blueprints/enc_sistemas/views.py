"""
Encuestas, vistas
"""
import json

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

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
                    "url": "#",  # url_for("cit_citas.detail", cit_cita_id=cita.id),
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
    """Detalle de la encuesta y listado de respuestas"""
    encuestados = EncSistema.query.filter_by(estatus="A").count()
    votos_contestados = EncSistema.query.filter_by(estatus="A").filter_by(estado="CONTESTADO").count()
    votos_cancelados = EncSistema.query.filter_by(estatus="A").filter_by(estado="CANCELADO").count()
    votos_pendientes = EncSistema.query.filter_by(estatus="A").filter_by(estado="PENDIENTE").count()

    votos = EncSistema.query.filter_by(estatus="A").filter_by(estado="CONTESTADO")
    votos_total = votos.count()
    val_05 = votos.filter_by(respuesta_01=5).count()
    val_04 = votos.filter_by(respuesta_01=4).count()
    val_03 = votos.filter_by(respuesta_01=3).count()
    val_02 = votos.filter_by(respuesta_01=2).count()
    val_01 = votos.filter_by(respuesta_01=1).count()
    # Calcular el nivel de satisfacción
    encuestados = 1 if encuestados == 0 else encuestados
    votos_total = 1 if votos_total == 0 else votos_total

    if votos_total <= 1:
        formula_result = 0
    else:
        formula_result = ((val_01 * 1) + (val_02 * 2) + (val_03 * 3) + (val_04 * 4) + (val_05 * 5)) / votos_total
    # Interpretar el resultado de la formula (Índice de satisfacción)
    if 0 <= formula_result < 1.25:
        resultado = "MALO"
    elif 1.25 <= formula_result < 3.75:
        resultado = "NORMAL"
    else:
        resultado = "BIEN"
    detalle = {
        "periodo": "2022/09/01 - 2022/09/30",
        "encuestados": encuestados,
        "contestados": votos_contestados,
        "cancelados": votos_cancelados,
        "pendientes": votos_pendientes,
        "contestados_porcentaje": round((votos_contestados * 100) / encuestados, 2),
        "cancelados_porcentaje": round((votos_cancelados * 100) / encuestados, 2),
        "pendientes_porcentaje": round((votos_pendientes * 100) / encuestados, 2),
        "total_votos": votos_total,
        "total_votos_porcentaje": round((votos_total*100)/encuestados),
        "votos_bien_porcentaje": round(((val_05+val_04)*100)/votos_total),
        "votos_normal_porcentaje": round((val_03*100)/votos_total),
        "votos_mal_porcentaje": round(((val_02+val_01)*100)/votos_total),
        "resultado": resultado,
        "indice_satisfaccion": round(formula_result, 2),
        "resp_01_valor_05": val_05,
        "resp_01_valor_04": val_04,
        "resp_01_valor_03": val_03,
        "resp_01_valor_02": val_02,
        "resp_01_valor_01": val_01,
    }
    return render_template(
        "enc_sistemas/list.jinja2",
        filtros=json.dumps({"estatus": "A"}),
        titulo="Encuesta del Sistema",
        detalle=detalle,
    )


@enc_sistemas.route("/encuestas/sistemas/<int:respuesta_id>", methods=["GET", "POST"])
def detail(respuesta_id):
    """Detalle de una respuesta"""
    return render_template(
        "enc_encuestas/detail.jinja2",
        filtros=json.dumps({"estatus": "A"}),
        titulo="Encuesta del Sistema",
        detalle=detalle,
    )
