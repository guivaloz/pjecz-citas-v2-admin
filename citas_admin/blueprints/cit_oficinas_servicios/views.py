"""
Cit Oficinas-Servicios, vistas
"""

import json

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from citas_admin.blueprints.bitacoras.models import Bitacora
from citas_admin.blueprints.cit_oficinas_servicios.forms import (
    CitOficinaServicioWithCitServicioForm,
    CitOficinaServicioWithOficinaForm,
)
from citas_admin.blueprints.cit_oficinas_servicios.models import CitOficinaServicio
from citas_admin.blueprints.cit_servicios.models import CitServicio
from citas_admin.blueprints.modulos.models import Modulo
from citas_admin.blueprints.oficinas.models import Oficina
from citas_admin.blueprints.permisos.models import Permiso
from citas_admin.blueprints.usuarios.decorators import permission_required
from lib.datatables import get_datatable_parameters, output_datatable_json
from lib.safe_string import safe_clave, safe_message, safe_string

MODULO = "CIT OFICINAS SERVICIOS"

cit_oficinas_servicios = Blueprint("cit_oficinas_servicios", __name__, template_folder="templates")


@cit_oficinas_servicios.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""


@cit_oficinas_servicios.route("/cit_oficinas_servicios/datatable_json", methods=["GET", "POST"])
def datatable_json():
    """DataTable JSON para listado de Cit Oficinas-Servicios"""
    # Tomar parámetros de Datatables
    draw, start, rows_per_page = get_datatable_parameters()
    # Consultar
    consulta = CitOficinaServicio.query
    # Primero filtrar por columnas propias
    if "estatus" in request.form:
        consulta = consulta.filter(CitOficinaServicio.estatus == request.form["estatus"])
    else:
        consulta = consulta.filter(CitOficinaServicio.estatus == "A")
    # Filtrar por los ids que ya tenemos en esta tabla
    if "cit_servicio_id" in request.form:
        consulta = consulta.filter(CitOficinaServicio.cit_servicio_id == request.form["cit_servicio_id"])
    if "oficina_id" in request.form:
        consulta = consulta.filter(CitOficinaServicio.oficina_id == request.form["oficina_id"])
    # Filtrar por clave o descripción corta de la oficina
    oficina_clave = ""
    if "oficina_clave" in request.form:
        oficina_clave = safe_clave(request.form["oficina_clave"])
    oficina_descripcion_corta = ""
    if "oficina_descripcion_corta" in request.form:
        oficina_descripcion_corta = safe_string(request.form["oficina_descripcion_corta"], save_enie=True)
    if oficina_clave != "" or oficina_descripcion_corta != "":
        consulta = consulta.join(Oficina)
        if oficina_clave != "":
            consulta = consulta.filter(Oficina.clave.contains(oficina_clave))
        if oficina_descripcion_corta != "":
            consulta = consulta.filter(Oficina.descripcion_corta.contains(oficina_descripcion_corta))
    # Filtrar por clave o descripción del servicio
    cit_servicio_clave = ""
    if "cit_servicio_clave" in request.form:
        cit_servicio_clave = safe_clave(request.form["cit_servicio_clave"])
    cit_servicio_descripcion = ""
    if "cit_servicio_descripcion" in request.form:
        cit_servicio_descripcion = safe_string(request.form["cit_servicio_descripcion"], save_enie=True)
    if cit_servicio_clave != "" or cit_servicio_descripcion != "":
        consulta = consulta.join(CitServicio)
        if cit_servicio_clave != "":
            consulta = consulta.filter(CitServicio.clave.contains(cit_servicio_clave))
        if cit_servicio_descripcion != "":
            consulta = consulta.filter(CitServicio.descripcion.contains(cit_servicio_descripcion))
    # Ordenar y paginar
    registros = consulta.order_by(CitOficinaServicio.id).offset(start).limit(rows_per_page).all()
    total = consulta.count()
    # Elaborar datos para DataTable
    data = []
    for resultado in registros:
        data.append(
            {
                "detalle": {
                    "id": resultado.id,
                    "url": url_for("cit_oficinas_servicios.detail", cit_oficina_servicio_id=resultado.id),
                },
                "oficina": {
                    "clave": resultado.oficina.clave,
                    "url": (
                        url_for("oficinas.detail", oficina_id=resultado.oficina_id) if current_user.can_view("OFICINAS") else ""
                    ),
                },
                "oficina_descripcion_corta": resultado.oficina.descripcion_corta,
                "oficina_es_jurisdiccional": resultado.oficina.es_jurisdiccional,
                "oficina_puede_agendar_citas": resultado.oficina.puede_agendar_citas,
                "cit_servicio": {
                    "clave": resultado.cit_servicio.clave,
                    "url": (
                        url_for("cit_servicios.detail", cit_servicio_id=resultado.cit_servicio_id)
                        if current_user.can_view("CIT SERVICIOS")
                        else ""
                    ),
                },
                "cit_servicio_descripcion": resultado.cit_servicio.descripcion,
            }
        )
    # Entregar JSON
    return output_datatable_json(draw, total, data)


@cit_oficinas_servicios.route("/cit_oficinas_servicios")
def list_active():
    """Listado de Cit Oficinas-Servicios activos"""
    return render_template(
        "cit_oficinas_servicios/list.jinja2",
        filtros=json.dumps({"estatus": "A"}),
        titulo="Oficinas-Servicios",
        estatus="A",
    )


@cit_oficinas_servicios.route("/cit_oficinas_servicios/inactivos")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def list_inactive():
    """Listado de Cit Oficinas-Servicios inactivos"""
    return render_template(
        "cit_oficinas_servicios/list.jinja2",
        filtros=json.dumps({"estatus": "B"}),
        titulo="Oficinas-Servicios inactivos",
        estatus="B",
    )


@cit_oficinas_servicios.route("/cit_oficinas_servicios/<int:cit_oficina_servicio_id>")
def detail(cit_oficina_servicio_id):
    """Detalle de un Cit Oficina-Servicio"""
    cit_oficina_servicio = CitOficinaServicio.query.get_or_404(cit_oficina_servicio_id)
    return render_template("cit_oficinas_servicios/detail.jinja2", cit_oficina_servicio=cit_oficina_servicio)


@cit_oficinas_servicios.route("/cit_oficinas_servicios/nuevo_con_cit_servicio/<int:cit_servicio_id>", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.CREAR)
def new_with_cit_servicio(cit_servicio_id):
    """Nuevo Cit Oficina-Servicio con CitServicio"""
    cit_servicio = CitServicio.query.get_or_404(cit_servicio_id)
    form = CitOficinaServicioWithCitServicioForm()
    if form.validate_on_submit():
        oficina = Oficina.query.get_or_404(form.oficina.data)
        descripcion = safe_string(f"servicio {cit_servicio.clave} en oficina {oficina.clave}", save_enie=True)
        puede_existir = (
            CitOficinaServicio.query.filter(CitOficinaServicio.cit_servicio_id == cit_servicio_id)
            .filter(CitOficinaServicio.oficina_id == oficina.id)
            .first()
        )
        if puede_existir and puede_existir.estatus == "A":
            flash(f"Ya existe la combinación de {descripcion}", "warning")
            return redirect(url_for("cit_oficinas_servicios.detail", cit_oficina_servicio_id=puede_existir.id))
        if puede_existir:
            puede_existir.recover()
            bitacora = Bitacora(
                modulo=Modulo.query.filter_by(nombre=MODULO).first(),
                usuario=current_user,
                descripcion=safe_message(f"Recuperada Cit Oficina-Servicio con {descripcion}"),
                url=url_for("cit_oficinas_servicios.detail", cit_oficina_servicio_id=puede_existir.id),
            )
            bitacora.save()
            flash(bitacora.descripcion, "success")
            return redirect(url_for("cit_oficinas_servicios.detail", cit_oficina_servicio_id=puede_existir.id))
        cit_oficina_servicio = CitOficinaServicio(
            cit_servicio_id=cit_servicio.id,
            oficina_id=oficina.id,
            descripcion=descripcion,
        )
        cit_oficina_servicio.save()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Nuevo Cit Oficina-Servicio {descripcion}"),
            url=url_for("cit_oficinas_servicios.detail", cit_oficina_servicio_id=cit_oficina_servicio.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
        return redirect(url_for("cit_oficinas_servicios.detail", cit_oficina_servicio_id=cit_oficina_servicio.id))
    form.cit_servicio.data = f"{cit_servicio.clave} - {cit_servicio.descripcion}"  # Read only string field
    return render_template(
        "cit_oficinas_servicios/new_with_cit_servicio.jinja2",
        cit_servicio=cit_servicio,
        form=form,
        titulo=f"Agregar {cit_servicio.clave} a una oficina",
    )


@cit_oficinas_servicios.route("/cit_oficinas_servicios/nuevo_with_oficina/<int:oficina_id>", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.CREAR)
def new_with_oficina(oficina_id):
    """Nuevo Cit Oficina-Servicio con Oficina"""
    oficina = Oficina.query.get_or_404(oficina_id)
    form = CitOficinaServicioWithOficinaForm()
    if form.validate_on_submit():
        cit_servicio = CitServicio.query.get_or_404(form.cit_servicio.data)
        descripcion = safe_string(f"servicio {cit_servicio.clave} en oficina {oficina.clave}", save_enie=True)
        puede_existir = (
            CitOficinaServicio.query.filter(CitOficinaServicio.cit_servicio_id == cit_servicio.id)
            .filter(CitOficinaServicio.oficina_id == oficina_id)
            .first()
        )
        if puede_existir and puede_existir.estatus == "A":
            flash(f"Ya existe la combinación de {descripcion}", "warning")
            return redirect(url_for("cit_oficinas_servicios.detail", cit_oficina_servicio_id=puede_existir.id))
        if puede_existir:
            puede_existir.recover()
            bitacora = Bitacora(
                modulo=Modulo.query.filter_by(nombre=MODULO).first(),
                usuario=current_user,
                descripcion=safe_message(f"Recuperada Cit Oficina-Servicio con {descripcion}"),
                url=url_for("cit_oficinas_servicios.detail", cit_oficina_servicio_id=puede_existir.id),
            )
            bitacora.save()
            flash(bitacora.descripcion, "success")
            return redirect(url_for("cit_oficinas_servicios.detail", cit_oficina_servicio_id=puede_existir.id))
        cit_oficina_servicio = CitOficinaServicio(
            cit_servicio_id=cit_servicio.id,
            oficina_id=oficina.id,
            descripcion=descripcion,
        )
        cit_oficina_servicio.save()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Nuevo Cit Oficina-Servicio {descripcion}"),
            url=url_for("cit_oficinas_servicios.detail", cit_oficina_servicio_id=cit_oficina_servicio.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
        return redirect(url_for("cit_oficinas_servicios.detail", cit_oficina_servicio_id=cit_oficina_servicio.id))
    form.oficina.data = f"{oficina.clave} - {oficina.descripcion_corta}"  # Read only string field
    return render_template(
        "cit_oficinas_servicios/new_with_oficina.jinja2",
        form=form,
        oficina=oficina,
        titulo=f"Agregar una oficina a {oficina.clave}",
    )


@cit_oficinas_servicios.route("/cit_oficinas_servicios/eliminar/<int:cit_oficina_servicio_id>")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def delete(cit_oficina_servicio_id):
    """Eliminar Cit Oficina-Servicio"""
    cit_oficina_servicio = CitOficinaServicio.query.get_or_404(cit_oficina_servicio_id)
    if cit_oficina_servicio.estatus == "A":
        cit_oficina_servicio.delete()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Eliminado Cit Oficina-Servicio {cit_oficina_servicio.descripcion}"),
            url=url_for("cit_oficinas_servicios.detail", cit_oficina_servicio_id=cit_oficina_servicio.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("cit_oficinas_servicios.detail", cit_oficina_servicio_id=cit_oficina_servicio.id))


@cit_oficinas_servicios.route("/cit_oficinas_servicios/recuperar/<int:cit_oficina_servicio_id>")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def recover(cit_oficina_servicio_id):
    """Recuperar Cit Oficina-Servicio"""
    cit_oficina_servicio = CitOficinaServicio.query.get_or_404(cit_oficina_servicio_id)
    if cit_oficina_servicio.estatus == "B":
        cit_oficina_servicio.recover()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Recuperado Cit Oficina-Servicio {cit_oficina_servicio.descripcion}"),
            url=url_for("cit_oficinas_servicios.detail", cit_oficina_servicio_id=cit_oficina_servicio.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("cit_oficinas_servicios.detail", cit_oficina_servicio_id=cit_oficina_servicio.id))
