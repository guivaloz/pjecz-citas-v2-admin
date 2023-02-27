"""
Pagos Pagos, vistas
"""
import json
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import or_
from datetime import datetime

from config.settings import PAGO_VERIFY_URL
from lib.datatables import get_datatable_parameters, output_datatable_json
from lib.safe_string import safe_message, safe_string

from citas_admin.blueprints.bitacoras.models import Bitacora
from citas_admin.blueprints.modulos.models import Modulo
from citas_admin.blueprints.permisos.models import Permiso
from citas_admin.blueprints.usuarios.decorators import permission_required
from citas_admin.blueprints.pag_pagos.models import PagPago
from citas_admin.blueprints.cit_clientes.models import CitCliente
from citas_admin.blueprints.pag_tramites_servicios.models import PagTramiteServicio

MODULO = "PAG PAGOS"

pag_pagos = Blueprint("pag_pagos", __name__, template_folder="templates")


@pag_pagos.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""


@pag_pagos.route("/pag_pagos/datatable_json", methods=["GET", "POST"])
def datatable_json():
    """DataTable JSON para listado de pagos"""
    # Tomar parámetros de Datatables
    draw, start, rows_per_page = get_datatable_parameters()
    # Consultar
    consulta = PagPago.query
    if "estatus" in request.form:
        consulta = consulta.filter_by(estatus=request.form["estatus"])
    else:
        consulta = consulta.filter_by(estatus="A")
    if "id" in request.form:
        consulta = consulta.filter_by(id=request.form["id"])
    if "fecha" in request.form:
        fecha = datetime.strptime(request.form["fecha"], "%Y-%m-%d")
        inicio_dt = datetime(year=fecha.year, month=fecha.month, day=fecha.day, hour=0, minute=0, second=0)
        termino_dt = datetime(year=fecha.year, month=fecha.month, day=fecha.day, hour=23, minute=59, second=59)
        consulta = consulta.filter(PagPago.creado >= inicio_dt).filter(PagPago.creado <= termino_dt)
    if "pag_tramite_servicio_id" in request.form:
        consulta = consulta.filter_by(pag_tramite_servicio_id=request.form["pag_tramite_servicio_id"])
    if "estado" in request.form:
        consulta = consulta.filter_by(estado=request.form["estado"])
    if "nombre_completo" in request.form:
        palabras = safe_string(request.form["nombre_completo"]).split(" ")
        consulta = consulta.join(CitCliente)
        for palabra in palabras:
            consulta = consulta.filter(or_(CitCliente.nombres.contains(palabra), CitCliente.apellido_primero.contains(palabra), CitCliente.apellido_segundo.contains(palabra)))
    registros = consulta.order_by(PagPago.id.desc()).offset(start).limit(rows_per_page).all()
    total = consulta.count()
    # Elaborar datos para DataTable
    data = []
    for resultado in registros:
        data.append(
            {
                "detalle": {
                    "id": resultado.id,
                    "url": url_for("pag_pagos.detail", pag_pago_id=resultado.id),
                },
                "fecha": resultado.creado,
                "cit_cliente": {
                    "nombre": f"{resultado.cit_cliente.nombre}",
                    "url": url_for("cit_clientes.detail", cit_cliente_id=resultado.cit_cliente.id) if current_user.can_view("CIT CLIENTES") else "",
                },
                "cantidad": resultado.cantidad,
                "pag_tramite_servicio": {
                    "clave": resultado.pag_tramite_servicio.clave,
                    "descripcion": resultado.pag_tramite_servicio.descripcion,
                    "url": url_for("pag_tramites_servicios.detail", pag_tramite_servicio_id=resultado.pag_tramite_servicio.id) if current_user.can_view("PAG TRAMITES SERVICIOS") else "",
                },
                "autoridad": {
                    "clave": resultado.autoridad.clave,
                    "url": url_for("autoridades.detail", autoridad_id=resultado.autoridad.id) if current_user.can_view("AUTORIDADES") else "",
                },
                "estado": resultado.estado,
                "folio": resultado.folio,
                "total": resultado.total,
            }
        )
    # Entregar JSON
    return output_datatable_json(draw, total, data)


@pag_pagos.route("/pag_pagos")
def list_active():
    """Listado de pagos activos"""
    return render_template(
        "pag_pagos/list.jinja2",
        filtros=json.dumps({"estatus": "A"}),
        titulo="Pagos",
        estatus="A",
        estados=PagPago.ESTADOS,
        tramites_y_servicios=PagTramiteServicio.query.filter_by(estatus="A").all(),
    )


@pag_pagos.route("/pag_pagos/inactivos")
@permission_required(MODULO, Permiso.MODIFICAR)
def list_inactive():
    """Listado de pagos inactivos"""
    return render_template(
        "pag_pagos/list.jinja2",
        filtros=json.dumps({"estatus": "B"}),
        titulo="Pagos inactivos",
        estatus="B",
        estados=PagPago.ESTADOS,
        tramites_y_servicios=PagTramiteServicio.query.filter_by(estatus="A").all(),
    )


@pag_pagos.route("/pag_pagos/<int:pag_pago_id>")
def detail(pag_pago_id):
    """Detalle de un pago"""
    pag_pago = PagPago.query.get_or_404(pag_pago_id)
    pag_pago_verify_url = "" if PAGO_VERIFY_URL == "" else PAGO_VERIFY_URL + "/" + pag_pago.encode_id()
    return render_template(
        "pag_pagos/detail.jinja2",
        pag_pago=pag_pago,
        pag_pago_verify_url=pag_pago_verify_url,
    )


@pag_pagos.route("/pag_pagos/eliminar/<int:pag_pago_id>")
@permission_required(MODULO, Permiso.MODIFICAR)
def delete(pag_pago_id):
    """Eliminar pago"""
    pag_pago = PagPago.query.get_or_404(pag_pago_id)
    if pag_pago.estatus == "A":
        pag_pago.delete()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Eliminado pago {pag_pago.id}"),
            url=url_for("pag_pagos.detail", pag_pago_id=pag_pago.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("pag_pagos.detail", pag_pago_id=pag_pago.id))


@pag_pagos.route("/pag_pagos/recuperar/<int:pag_pago_id>")
@permission_required(MODULO, Permiso.MODIFICAR)
def recover(pag_pago_id):
    """Recuperar pago"""
    pag_pago = PagPago.query.get_or_404(pag_pago_id)
    if pag_pago.estatus == "B":
        pag_pago.recover()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Recuperado pago {pag_pago.id}"),
            url=url_for("pag_pagos.detail", pag_pago_id=pag_pago.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("pag_pagos.detail", pag_pago_id=pag_pago.id))


@pag_pagos.route("/pag_pagos/entregar/<int:pag_pago_id>")
@permission_required(MODULO, Permiso.MODIFICAR)
def deliver(pag_pago_id):
    """Cambiar el estado a ENTREGADO"""
    pag_pago = PagPago.query.get_or_404(pag_pago_id)
    if pag_pago.estatus == "A" and pag_pago.estado == "PAGADO":
        pag_pago.estado = "ENTREGADO"
        pag_pago.save()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Entregado el pago {pag_pago.id}"),
            url=url_for("pag_pagos.detail", pag_pago_id=pag_pago.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("pag_pagos.detail", pag_pago_id=pag_pago.id))


@pag_pagos.route("/pag_pagos/pagar/<int:pag_pago_id>")
@permission_required(MODULO, Permiso.MODIFICAR)
def paid(pag_pago_id):
    """Cambiar el estado a PAGADO"""
    pag_pago = PagPago.query.get_or_404(pag_pago_id)
    if pag_pago.estatus == "A" and pag_pago.estado == "ENTREGADO":
        pag_pago.estado = "PAGADO"
        pag_pago.save()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Pagado el pago {pag_pago.id}"),
            url=url_for("pag_pagos.detail", pag_pago_id=pag_pago.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("pag_pagos.detail", pag_pago_id=pag_pago.id))
