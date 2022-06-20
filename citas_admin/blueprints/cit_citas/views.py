"""
Cit Citas, vistas
"""
from datetime import datetime
import json
from flask import Blueprint, flash, redirect, render_template, request, url_for, abort
from flask_login import current_user, login_required

from lib.datatables import get_datatable_parameters, output_datatable_json
from lib.safe_string import safe_message

from citas_admin.blueprints.bitacoras.models import Bitacora
from citas_admin.blueprints.modulos.models import Modulo
from citas_admin.blueprints.cit_citas.models import CitCita
from citas_admin.blueprints.permisos.models import Permiso
from citas_admin.blueprints.usuarios.decorators import permission_required

MODULO = "CIT CITAS"

cit_citas = Blueprint("cit_citas", __name__, template_folder="templates")


@cit_citas.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""


@cit_citas.route("/cit_citas/datatable_json", methods=["GET", "POST"])
def datatable_json():
    """DataTable JSON para listado de citas"""
    # Tomar parámetros de Datatables
    draw, start, rows_per_page = get_datatable_parameters()
    # Consultar
    consulta = CitCita.query
    if "estatus" in request.form:
        consulta = consulta.filter_by(estatus=request.form["estatus"])
    else:
        consulta = consulta.filter_by(estatus="A")
    if "cit_cliente_id" in request.form:
        consulta = consulta.filter_by(cit_cliente_id=request.form["cit_cliente_id"])
    if "cit_servicio_id" in request.form:
        consulta = consulta.filter_by(cit_servicio_id=request.form["cit_servicio_id"])
    if "oficina_id" in request.form:
        consulta = consulta.filter_by(oficina_id=request.form["oficina_id"])
    if "fecha" in request.form and request.form["fecha"] != "":
        fecha = datetime.strptime(request.form["fecha"], "%Y-%m-%d")
        inicio_dt = datetime(year=fecha.year, month=fecha.month, day=fecha.day, hour=0, minute=0, second=0)
        termino_dt = datetime(year=fecha.year, month=fecha.month, day=fecha.day, hour=23, minute=59, second=59)
        consulta = consulta.filter(CitCita.inicio >= inicio_dt).filter(CitCita.inicio <= termino_dt)
    registros = consulta.order_by(CitCita.id.desc()).offset(start).limit(rows_per_page).all()
    total = consulta.count()
    # Elaborar datos para DataTable
    data = []
    for cita in registros:
        data.append(
            {
                "detalle": {
                    "id": cita.id,
                    "url": url_for("cit_citas.detail", cit_cita_id=cita.id),
                },
                "cit_cliente": {
                    "nombre": cita.cit_cliente.nombre,
                    "url": url_for("cit_clientes.detail", cit_cliente_id=cita.cit_cliente.id) if current_user.can_view("CIT CLIENTES") else "",
                },
                "cit_servicio": {
                    "clave": cita.cit_servicio.clave,
                    "url": url_for("cit_servicios.detail", cit_servicio_id=cita.cit_servicio.id) if current_user.can_view("CIT SERVICIOS") else "",
                },
                "oficina": {
                    "clave": cita.oficina.clave,
                    "url": url_for("oficinas.detail", oficina_id=cita.oficina.id) if current_user.can_view("OFICINAS") else "",
                },
                "fecha": cita.inicio.strftime("%Y-%m-%d 00:00:00"),
                "inicio": cita.inicio.strftime("%H:%M"),
                "termino": cita.termino.strftime("%H:%M"),
                "estado": cita.estado,
            }
        )
    # Entregar JSON
    return output_datatable_json(draw, total, data)


@cit_citas.route("/cit_citas", methods=["POST", "GET"])
def list_active():
    """Listado de Citas activas"""
    # La fecha puede venir como argumento
    fecha = request.args.get("fecha", None)
    # Si es administrador, puede ver las citas de todas las oficinas
    if current_user.can_admin(MODULO):
        return render_template(
            "cit_citas/list_admin.jinja2",
            filtros=json.dumps({"estatus": "A", "fecha": fecha}),
            titulo="Todas las Citas" if fecha is None else f"Todas las citas del {fecha}",
            estatus="A",
        )
    # No es administrador, entonces la fecha por defecto es hoy
    if fecha is None:
        fecha = datetime.now().strftime("%Y-%m-%d")
    # Y siempre se filtra por su propia oficina
    return render_template(
        "cit_citas/list.jinja2",
        filtros=json.dumps({"estatus": "A", "fecha": fecha, "oficina_id": current_user.oficina_id}),
        titulo=f"Citas del {fecha} de {current_user.oficina.descripcion_corta}",
        estatus="A",
    )


@cit_citas.route("/cit_citas/inactivos")
@permission_required(MODULO, Permiso.MODIFICAR)
def list_inactive():
    """Listado de Citas inactivas"""
    # La fecha puede venir como argumento
    fecha = request.args.get("fecha", None)
    # Si es administrador, puede ver las citas de todas las oficinas
    if current_user.can_admin(MODULO):
        return render_template(
            "cit_citas/list_admin.jinja2",
            filtros=json.dumps({"estatus": "A", "fecha": fecha}),
            titulo="Todas las Citas eliminadas" if fecha is None else f"Todas las citas del {fecha}",
            estatus="B",
        )
    # No es administrador, entonces la fecha por defecto es hoy
    if fecha is None:
        fecha = datetime.now().strftime("%Y-%m-%d")
    # Y siempre se filtra por su propia oficina
    return render_template(
        "cit_citas/list.jinja2",
        filtros=json.dumps({"estatus": "A", "fecha": fecha, "oficina_id": current_user.oficina_id}),
        titulo=f"Citas eliminadas del {fecha} de {current_user.oficina.descripcion_corta}",
        estatus="B",
    )


@cit_citas.route("/cit_citas/<int:cit_cita_id>")
def detail(cit_cita_id):
    """Detalle de una Cita"""
    cit_cita = CitCita.query.get_or_404(cit_cita_id)
    # Si es administrador, ve todas las citas
    if current_user.can_admin(MODULO):
        return render_template("cit_citas/detail.jinja2", cit_cita=cit_cita)
    # Si no es administrador, solo puede ver los detalles de una cita de su propia oficina
    if cit_cita.oficina == current_user.oficina:
        return render_template("cit_citas/detail.jinja2", cit_cita=cit_cita)
    # Si no es administrador, no puede ver los detalles de una cita de otra oficina, lo reenviamos al listado
    abort(403)


@cit_citas.route("/cit_citas/eliminar/<int:cit_cita_id>")
@permission_required(MODULO, Permiso.MODIFICAR)
def delete(cit_cita_id):
    """Eliminar Cita"""
    cit_cita = CitCita.query.get_or_404(cit_cita_id)
    # Si no es administrador, no puede eliminar un cita de otra oficina
    if not current_user.can_admin(MODULO) and cit_cita.oficina != current_user.oficina:
        abort(403)

    if cit_cita.estatus == "A":
        cit_cita.delete()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Eliminado Cita {cit_cita.id}"),
            url=url_for("cit_citas.detail", cit_cita_id=cit_cita.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("cit_citas.detail", cit_cita_id=cit_cita.id))


@cit_citas.route("/cit_citas/recuperar/<int:cit_cita_id>")
@permission_required(MODULO, Permiso.MODIFICAR)
def recover(cit_cita_id):
    """Recuperar Cita"""
    cit_cita = CitCita.query.get_or_404(cit_cita_id)
    # Si no es administrador, no puede eliminar un cita de otra oficina
    if not current_user.can_admin(MODULO) and cit_cita.oficina != current_user.oficina:
        abort(403)

    if cit_cita.estatus == "B":
        cit_cita.recover()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Recuperado Cita {cit_cita.id}"),
            url=url_for("cit_citas.detail", cit_cita_id=cit_cita.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("cit_citas.detail", cit_cita_id=cit_cita.id))


@cit_citas.route("/cit_citas/aistencia/<int:cit_cita_id>")
@permission_required(MODULO, Permiso.MODIFICAR)
def assistance(cit_cita_id):
    """Marcar Asistencia a una Cita"""
    cit_cita = CitCita.query.get_or_404(cit_cita_id)
    # Si no es administrador, no puede eliminar un cita de otra oficina
    if not current_user.can_admin(MODULO) and cit_cita.oficina != current_user.oficina:
        abort(403)

    if cit_cita.estatus == "A":
        cit_cita.estado = "ASISTIO"
        cit_cita.asistencia = True
        cit_cita.save()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Agregadó Asistencia a la Cita {cit_cita.id}"),
            url=url_for("cit_citas.detail", cit_cita_id=cit_cita.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("cit_citas.detail", cit_cita_id=cit_cita.id))


@cit_citas.route("/cit_citas/pendiente/<int:cit_cita_id>")
@permission_required(MODULO, Permiso.MODIFICAR)
def pending(cit_cita_id):
    """Marcar la Cita como Pendiente"""
    cit_cita = CitCita.query.get_or_404(cit_cita_id)
    # Si no es administrador, no puede eliminar un cita de otra oficina
    if not current_user.can_admin(MODULO) and cit_cita.oficina != current_user.oficina:
        abort(403)

    if cit_cita.estatus == "A":
        cit_cita.estado = "PENDIENTE"
        cit_cita.asistencia = False
        cit_cita.save()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Cambiado estado de la Cita {cit_cita.id} a Pendiente"),
            url=url_for("cit_citas.detail", cit_cita_id=cit_cita.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("cit_citas.detail", cit_cita_id=cit_cita.id))
