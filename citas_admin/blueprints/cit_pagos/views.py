"""
Cit Pagos, vistas
"""
import json
from flask import Blueprint, flash, redirect, render_template, request, url_for, Response
from flask_login import current_user, login_required

from lib.datatables import get_datatable_parameters, output_datatable_json
from lib.safe_string import safe_string, safe_message
from lib.wpp import create_chain_xml, create_pay_link

from citas_admin.blueprints.bitacoras.models import Bitacora
from citas_admin.blueprints.cit_clientes.models import CitCliente
from citas_admin.blueprints.cit_pagos.models import CitPago
from citas_admin.blueprints.cit_pagos.forms import CitPagoForm
from citas_admin.blueprints.modulos.models import Modulo
from citas_admin.blueprints.permisos.models import Permiso
from citas_admin.blueprints.usuarios.decorators import permission_required

MODULO = "CIT PAGOS"

cit_pagos = Blueprint("cit_pagos", __name__, template_folder="templates")


@cit_pagos.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""


@cit_pagos.route("/cit_pagos/datatable_json", methods=["GET", "POST"])
def datatable_json():
    """DataTable JSON para listado de pagos"""
    # Tomar parámetros de Datatables
    draw, start, rows_per_page = get_datatable_parameters()
    # Consultar
    consulta = CitPago.query
    if "estatus" in request.form:
        consulta = consulta.filter_by(estatus=request.form["estatus"])
    else:
        consulta = consulta.filter_by(estatus="A")
    if "cit_cliente_id" in request.form:
        consulta = consulta.filter_by(cit_cliente_id=request.form["cit_cliente_id"])
    registros = consulta.order_by(CitPago.id.desc()).offset(start).limit(rows_per_page).all()
    total = consulta.count()
    # Elaborar datos para DataTable
    data = []
    for resultado in registros:
        data.append(
            {
                "detalle": {
                    "id": resultado.id,
                    "url": url_for("cit_pagos.detail", cit_pago_id=resultado.id),
                },
                "cit_cliente": {
                    "nombre": resultado.cit_cliente.nombre,
                    "url": url_for("cit_clientes.detail", cit_cliente_id=resultado.cit_cliente.id) if current_user.can_view("CIT CLIENTES") else "",
                },
                "descripcion": resultado.descripcion,
                "total": resultado.total,
            }
        )
    # Entregar JSON
    return output_datatable_json(draw, total, data)


@cit_pagos.route("/cit_pagos")
def list_active():
    """Listado de pagos activos"""
    return render_template(
        "cit_pagos/list.jinja2",
        filtros=json.dumps({"estatus": "A"}),
        titulo="Pagos",
        estatus="A",
    )


@cit_pagos.route("/cit_pagos/inactivos")
@permission_required(MODULO, Permiso.MODIFICAR)
def list_inactive():
    """Listado de pagos inactivos"""
    return render_template(
        "cit_pagos/list.jinja2",
        filtros=json.dumps({"estatus": "B"}),
        titulo="Pagos inactivos",
        estatus="B",
    )


@cit_pagos.route("/cit_pagos/<int:cit_pago_id>")
def detail(cit_pago_id):
    """Detalle de un pago"""
    cit_pago = CitPago.query.get_or_404(cit_pago_id)
    return render_template(
        "cit_pagos/detail.jinja2",
        cit_pago=cit_pago,
    )


@cit_pagos.route("/cit_pagos/cadena/<int:cit_pago_id>")
def chain(cit_pago_id):
    """Cadena XML de un pago"""
    cit_pago = CitPago.query.get_or_404(cit_pago_id)
    xml = create_chain_xml(amount=cit_pago.total)
    return Response(xml, mimetype="text/xml")


@cit_pagos.route("/cit_pagos/link_pay/<int:cit_pago_id>")
def link_pay(cit_pago_id):
    """Cadena XML de un pago"""
    cit_pago = CitPago.query.get_or_404(cit_pago_id)

    try:
        url_pay = create_pay_link(
            client_id=cit_pago.cit_cliente.id,
            email=cit_pago.cit_cliente.email,
            service_detail=cit_pago.descripcion,
            amount=cit_pago.total,
        )
    except Exception as err:
        url_pay=f"ERROR! {err}"

    return render_template(
        "cit_pagos/link_pay.jinja2",
        cit_pago=cit_pago,
        url_pay=url_pay,
    )


@cit_pagos.route("/cit_pagos/nuevo/<int:cit_cliente_id>", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.CREAR)
def new(cit_cliente_id):
    """Nuevo Pago"""
    cit_cliente = CitCliente.query.get_or_404(cit_cliente_id)
    form = CitPagoForm()
    if form.validate_on_submit():
        cit_pago = CitPago(
            cit_cliente=cit_cliente,
            descripcion=safe_string(form.descripcion.data),
            total=form.total.data,
        )
        cit_pago.save()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Nuevo Pago {cit_pago.descripcion} ${cit_pago.total}"),
            url=url_for("cit_pagos.detail", cit_pago_id=cit_pago.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
        return redirect(bitacora.url)
    form.cit_cliente_nombre.data = cit_cliente.nombre  # Read only
    return render_template("cit_pagos/new.jinja2", form=form, cit_cliente=cit_cliente)


@cit_pagos.route("/cit_pagos/edicion/<int:cit_pago_id>", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.MODIFICAR)
def edit(cit_pago_id):
    """Editar pago"""
    cit_pago = CitPago.query.get_or_404(cit_pago_id)
    form = CitPagoForm()
    if form.validate_on_submit():
        cit_pago.descripcion = safe_string(form.descripcion.data)
        cit_pago.total = form.total.data
        cit_pago.save()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Editado pago {cit_pago.descripcion} ${cit_pago.total}"),
            url=url_for("cit_pagos.detail", cit_pago_id=cit_pago.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
        return redirect(bitacora.url)
    form.cit_cliente_nombre.data = cit_pago.cit_cliente.nombre  # Read only
    form.descripcion.data = cit_pago.descripcion
    form.total.data = cit_pago.total
    return render_template("cit_pagos/edit.jinja2", form=form, cit_pago=cit_pago)


@cit_pagos.route("/cit_pagos/eliminar/<int:cit_pago_id>")
@permission_required(MODULO, Permiso.MODIFICAR)
def delete(cit_pago_id):
    """Eliminar pago"""
    cit_pago = CitPago.query.get_or_404(cit_pago_id)
    if cit_pago.estatus == "A":
        cit_pago.delete()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Eliminado pago {cit_pago.descripcion} ${cit_pago.total}"),
            url=url_for("cit_pagos.detail", cit_pago_id=cit_pago.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("cit_pagos.detail", cit_pago_id=cit_pago.id))


@cit_pagos.route("/cit_pagos/recuperar/<int:cit_pago_id>")
@permission_required(MODULO, Permiso.MODIFICAR)
def recover(cit_pago_id):
    """Recuperar pago"""
    cit_pago = CitPago.query.get_or_404(cit_pago_id)
    if cit_pago.estatus == "B":
        cit_pago.recover()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Recuperado pago {cit_pago.descripcion} ${cit_pago.total}"),
            url=url_for("cit_pagos.detail", cit_pago_id=cit_pago.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("cit_pagos.detail", cit_pago_id=cit_pago.id))
