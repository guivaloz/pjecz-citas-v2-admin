"""
Cit Clientes Registros, vistas
"""
import json
import os

from dotenv import load_dotenv
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from lib.datatables import get_datatable_parameters, output_datatable_json
from lib.safe_string import safe_string, safe_message

from citas_admin.blueprints.bitacoras.models import Bitacora
from citas_admin.blueprints.modulos.models import Modulo
from citas_admin.blueprints.permisos.models import Permiso
from citas_admin.blueprints.usuarios.decorators import permission_required
from citas_admin.blueprints.cit_clientes_registros.models import CitClienteRegistro

MODULO = "CIT CLIENTES REGISTROS"

cit_clientes_registros = Blueprint("cit_clientes_registros", __name__, template_folder="templates")


@cit_clientes_registros.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""


@cit_clientes_registros.route("/cit_clientes_registros/datatable_json", methods=["GET", "POST"])
def datatable_json():
    """DataTable JSON para listado de Clientes Registros"""
    # Tomar parámetros de Datatables
    draw, start, rows_per_page = get_datatable_parameters()
    # Consultar
    consulta = CitClienteRegistro.query
    if "estatus" in request.form:
        consulta = consulta.filter_by(estatus=request.form["estatus"])
    else:
        consulta = consulta.filter_by(estatus="A")
    if "email" in request.form:
        consulta = consulta.filter(CitClienteRegistro.email.contains(request.form["email"]))
    if "nombres" in request.form:
        consulta = consulta.filter(CitClienteRegistro.nombres.contains(safe_string(request.form["nombres"])))
    if "apellido_primero" in request.form:
        consulta = consulta.filter(CitClienteRegistro.apellido_primero.contains(safe_string(request.form["apellido_primero"])))
    if "ya_registrado" in request.form:
        consulta = consulta.filter_by(ya_registrado=request.form["ya_registrado"])

    registros = consulta.order_by(CitClienteRegistro.id.desc()).offset(start).limit(rows_per_page).all()
    total = consulta.count()
    # Elaborar datos para DataTable
    data = []
    for resultado in registros:
        data.append(
            {
                "detalle": {
                    "id": resultado.id,
                    "url": url_for("cit_clientes_registros.detail", cit_cliente_registro_id=resultado.id),
                },
                "nombres": resultado.nombres,
                "apellido_primero": resultado.apellido_primero,
                "apellido_segundo": resultado.apellido_segundo,
                "email": resultado.email,
                "expiracion": resultado.expiracion,
                "ya_registrado": resultado.ya_registrado,
            }
        )
    # Entregar JSON
    return output_datatable_json(draw, total, data)


@cit_clientes_registros.route("/cit_clientes_registros")
def list_active():
    """Listado de Clientes Registros activos"""
    return render_template(
        "cit_clientes_registros/list.jinja2",
        filtros=json.dumps({"estatus": "A"}),
        titulo="Clientes Registros",
        estatus="A",
    )


@cit_clientes_registros.route("/cit_clientes_registros/inactivos")
@permission_required(MODULO, Permiso.MODIFICAR)
def list_inactive():
    """Listado de Clientes Registros inactivos"""
    return render_template(
        "cit_clientes_registros/list.jinja2",
        filtros=json.dumps({"estatus": "B"}),
        titulo="Clientes Registros inactivos",
        estatus="B",
    )


@cit_clientes_registros.route("/cit_clientes_registros/<int:cit_cliente_registro_id>")
def detail(cit_cliente_registro_id):
    """Detalle de un Cliente Registro"""
    cit_cliente_registro = CitClienteRegistro.query.get_or_404(cit_cliente_registro_id)
    load_dotenv()  # Take environment variables from .env
    NEW_ACCOUNT_CONFIRM_URL = os.getenv("NEW_ACCOUNT_CONFIRM_URL", "")
    url_confirmacion = f"{NEW_ACCOUNT_CONFIRM_URL}?hashid={cit_cliente_registro.encode_id()}&cadena_validar={cit_cliente_registro.cadena_validar}"
    return render_template("cit_clientes_registros/detail.jinja2", cit_cliente_registro=cit_cliente_registro, url_confirmacion=url_confirmacion)


@cit_clientes_registros.route("/cit_clientes_registros/eliminar/<int:cit_cliente_registro_id>")
@permission_required(MODULO, Permiso.MODIFICAR)
def delete(cit_cliente_registro_id):
    """Eliminar Registro de Cliente"""
    cit_cliente_registro = CitClienteRegistro.query.get_or_404(cit_cliente_registro_id)
    if cit_cliente_registro.estatus == "A":
        cit_cliente_registro.delete()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Eliminado Registro {cit_cliente_registro.email}"),
            url=url_for("cit_clientes_registros.detail", cit_cliente_registro_id=cit_cliente_registro.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("cit_clientes_registros.detail", cit_cliente_registro_id=cit_cliente_registro.id))


@cit_clientes_registros.route("/cit_clientes_registros/recuperar/<int:cit_cliente_registro_id>")
@permission_required(MODULO, Permiso.MODIFICAR)
def recover(cit_cliente_registro_id):
    """Recuperar Registro de Cliente"""
    cit_cliente_registro = CitClienteRegistro.query.get_or_404(cit_cliente_registro_id)
    if cit_cliente_registro.estatus == "B":
        cit_cliente_registro.recover()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Recuperado Registro {cit_cliente_registro.email}"),
            url=url_for("cit_clientes_registros.detail", cit_cliente_registro_id=cit_cliente_registro.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("cit_clientes_registros.detail", cit_cliente_registro_id=cit_cliente_registro.id))
