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

from citas_admin.blueprints.encuestas.models import EncuestaSistema

MODULO = "ENCUESTAS"

encuestas = Blueprint("encuestas", __name__, template_folder="templates")


@encuestas.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""


@encuestas.route("/encuesta/sistema/datatable_json", methods=["GET", "POST"])
def datatable_json_sistema():
    """DataTable JSON para listado de respuestas de la encuesta de sistema"""
    # Tomar parámetros de Datatables
    draw, start, rows_per_page = get_datatable_parameters()
    # Consultar
    consulta = EncuestaSistema.query
    if "estatus" in request.form:
        consulta = consulta.filter_by(estatus=request.form["estatus"])
    else:
        consulta = consulta.filter_by(estatus="A")
    # Hace el query de listado
    registros = consulta.order_by(EncuestaSistema.id.desc()).offset(start).limit(rows_per_page).all()
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
    encuestados = EncuestaSistema.query.filter_by(estatus="A").count()
    votos = EncuestaSistema.query.filter_by(estatus="A").filter_by(estado="CONTESTADO")
    votos_total = votos.count()
    val_05 = votos.filter_by(respuesta_01=5).count()
    val_04 = votos.filter_by(respuesta_01=4).count()
    val_03 = votos.filter_by(respuesta_01=3).count()
    val_02 = votos.filter_by(respuesta_01=2).count()
    val_01 = votos.filter_by(respuesta_01=1).count()
    # Calcular el nivel de satisfacción
    formula_result = (val_01 * 1) + (val_02 * 2) + (val_03 * 3) + (val_04 * 4) + (val_05 * 5) / votos_total 
    detalle = {
        "periodo": "2022/09/01 - 2022/09/30",
        "encuestados": encuestados,
        "total_votos": f'{votos_total}, participación del {round((votos_total*100)/encuestados)}%',
        "resultado": "BIEN",
        "indice_satisfaccion": round(formula_result, 2),
        "resp_01_valor_05": val_05,
        "resp_01_valor_04": val_04,
        "resp_01_valor_03": val_03,
        "resp_01_valor_02": val_02,
        "resp_01_valor_01": val_01,
    }
    return render_template(
        "encuestas/detail_sistema.jinja2",
        filtros=json.dumps({"estatus": "A"}),
        titulo="Encuesta del Sistema",
        detalle=detalle,
    )
