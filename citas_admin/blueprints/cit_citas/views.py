"""
Cit Citas, vistas
"""
from datetime import datetime, timedelta
import json
from flask import Blueprint, flash, redirect, render_template, request, url_for, abort
from flask_login import current_user, login_required

from lib.datatables import get_datatable_parameters, output_datatable_json
from lib.safe_string import safe_message, safe_string, safe_email, safe_text

from citas_admin.blueprints.bitacoras.models import Bitacora
from citas_admin.blueprints.modulos.models import Modulo
from citas_admin.blueprints.cit_citas.models import CitCita
from citas_admin.blueprints.permisos.models import Permiso
from citas_admin.blueprints.cit_clientes.models import CitCliente
from citas_admin.blueprints.usuarios.decorators import permission_required
from citas_admin.blueprints.distritos.models import Distrito
from citas_admin.blueprints.oficinas.models import Oficina

from citas_admin.blueprints.cit_citas.forms import CitCitaSearchForm, CitCitaSearchAdminForm

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
    if "cit_cliente" in request.form:
        consulta = consulta.join(CitCliente)
        consulta = consulta.filter(CitCliente.nombres.contains(request.form["cit_cliente"]))
    if "cit_cliente_email" in request.form:
        consulta = consulta.join(CitCliente)
        consulta = consulta.filter(CitCliente.email.contains(request.form["cit_cliente_email"]))
    if "cit_servicio_id" in request.form:
        consulta = consulta.filter_by(cit_servicio_id=request.form["cit_servicio_id"])
    if "oficina_id" in request.form:
        consulta = consulta.filter_by(oficina_id=request.form["oficina_id"])
    else:
        if "distrito_id" in request.form:
            consulta = consulta.join(Oficina)
            consulta = consulta.filter_by(distrito_id=request.form["distrito_id"])
    if "fecha" in request.form and request.form["fecha"] != "":
        fecha = datetime.strptime(request.form["fecha"], "%Y-%m-%d")
        inicio_dt = datetime(year=fecha.year, month=fecha.month, day=fecha.day, hour=0, minute=0, second=0)
        termino_dt = datetime(year=fecha.year, month=fecha.month, day=fecha.day, hour=23, minute=59, second=59)
        consulta = consulta.filter(CitCita.inicio >= inicio_dt).filter(CitCita.inicio <= termino_dt)
    # Si es admin, ordenar por id, si es juzgado ordenar por fecha
    if current_user.can_admin(MODULO):
        registros = consulta.order_by(CitCita.id.desc()).offset(start).limit(rows_per_page).all()
    else:
        # No mostrar a los juzgados la citas canceladas
        consulta = consulta.filter(CitCita.estado != "CANCELO")
        if rows_per_page == -1:
            registros = consulta.order_by(CitCita.inicio).all()
        else:
            registros = consulta.order_by(CitCita.inicio).offset(start).limit(rows_per_page).all()
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
                    "descripcion": cita.cit_servicio.descripcion,
                },
                "oficina": {
                    "clave": cita.oficina.clave,
                    "url": url_for("oficinas.detail", oficina_id=cita.oficina.id) if current_user.can_view("OFICINAS") else "",
                    "descripcion": cita.oficina.descripcion,
                },
                "creado": cita.creado.strftime("%Y-%m-%d %H:%M"),
                "fecha": cita.inicio.strftime("%Y-%m-%d %H:%M"),
                "inicio": cita.inicio.strftime("%H:%M"),
                "termino": cita.termino.strftime("%H:%M"),
                "estado": cita.estado,
                "notas": cita.notas,
            }
        )
    # Entregar JSON
    return output_datatable_json(draw, total, data)


@cit_citas.route("/cit_citas", methods=["POST", "GET"])
def list_active():
    """Listado de Citas activas"""
    fecha = None
    fecha_str = ""
    fecha_anterior_str = ""
    fecha_siguiente_str = ""
    # La fecha puede venir como argumento
    fecha_str = request.args.get("fecha", "")
    # Si no es administrador y no viene la fecha, se impone la fecha de hoy
    if fecha_str == "" and not current_user.can_admin(MODULO):
        fecha = datetime.now()
        fecha_str = fecha.strftime("%Y-%m-%d")
    # Al tener la fecha, se calcula la fecha anterior y siguiente
    if fecha_str != "":
        fecha = datetime.strptime(fecha_str, "%Y-%m-%d")
        fecha_anterior_str = (fecha - timedelta(days=1)).strftime("%Y-%m-%d")
        fecha_siguiente_str = (fecha + timedelta(days=1)).strftime("%Y-%m-%d")
    # Si es administrador, puede ver las citas de todas las oficinas
    if current_user.can_admin(MODULO):
        return render_template(
            "cit_citas/list_admin.jinja2",
            filtros=json.dumps({"estatus": "A", "fecha": fecha_str}),
            titulo="Todas las Citas" if fecha is None else f"Todas las citas del {fecha_str}",
            estatus="A",
            fecha_actual=fecha_str,
            fecha_anterior=fecha_anterior_str,
            fecha_siguiente=fecha_siguiente_str,
        )
    # NO es administrador, entonces se filtra por su propia oficina
    return render_template(
        "cit_citas/list.jinja2",
        filtros=json.dumps({"estatus": "A", "oficina_id": current_user.oficina_id, "fecha": fecha_str}),
        titulo=f"Citas del {current_user.oficina.descripcion_corta}",
        estatus="A",
        fecha_actual=fecha_str,
        fecha_anterior=fecha_anterior_str,
        fecha_siguiente=fecha_siguiente_str,
    )


@cit_citas.route("/cit_citas/inactivos")
@permission_required(MODULO, Permiso.MODIFICAR)
def list_inactive():
    """Listado de Citas inactivas"""
    fecha = None
    fecha_str = ""
    fecha_anterior_str = ""
    fecha_siguiente_str = ""
    # La fecha puede venir como argumento
    fecha_str = request.args.get("fecha", "")
    # Si no es administrador y no viene la fecha, se impone la fecha de hoy
    if fecha_str == "" and not current_user.can_admin(MODULO):
        fecha = datetime.now()
        fecha_str = fecha.strftime("%Y-%m-%d")
    # Al tener la fecha, se calcula la fecha anterior y siguiente
    if fecha_str != "":
        fecha = datetime.strptime(fecha_str, "%Y-%m-%d")
        fecha_anterior_str = (fecha - timedelta(days=1)).strftime("%Y-%m-%d")
        fecha_siguiente_str = (fecha + timedelta(days=1)).strftime("%Y-%m-%d")
    # Si es administrador, puede ver las citas de todas las oficinas
    if current_user.can_admin(MODULO):
        return render_template(
            "cit_citas/list_admin.jinja2",
            filtros=json.dumps({"estatus": "B", "fecha": fecha_str}),
            titulo="Todas las Citas eliminadas" if fecha is None else f"Todas las citas del {fecha_str}",
            estatus="B",
            fecha_anterior=fecha_anterior_str,
            fecha_siguiente=fecha_siguiente_str,
        )
    # NO es administrador, entonces se filtra por su propia oficina
    return render_template(
        "cit_citas/list.jinja2",
        filtros=json.dumps({"estatus": "B", "oficina_id": current_user.oficina_id, "fecha": fecha_str}),
        titulo=f"Citas eliminadas del {current_user.oficina.descripcion_corta}",
        estatus="B",
        fecha_actual=fecha_str,
        fecha_anterior=fecha_anterior_str,
        fecha_siguiente=fecha_siguiente_str,
    )


@cit_citas.route("/cit_citas/<int:cit_cita_id>")
def detail(cit_cita_id):
    """Detalle de una Cita"""
    cit_cita = CitCita.query.get_or_404(cit_cita_id)
    if cit_cita.inicio <= datetime.now():
        if cit_cita.estado == "PENDIENTE":
            marcar_asistencia = True
        else:
            marcar_asistencia = False
    else:
        marcar_asistencia = False
    # Si es administrador, ve todas las citas
    if current_user.can_admin(MODULO):
        return render_template("cit_citas/detail.jinja2", cit_cita=cit_cita, marcar_asistencia=marcar_asistencia)
    # Si no es administrador, solo puede ver los detalles de una cita de su propia oficina
    if cit_cita.oficina == current_user.oficina:
        return render_template("cit_citas/detail.jinja2", cit_cita=cit_cita, marcar_asistencia=marcar_asistencia)
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
def assistance(cit_cita_id, qr=False):
    """Marcar Asistencia a una Cita"""
    cit_cita = CitCita.query.get_or_404(cit_cita_id)
    # Si no es administrador, no puede marcar Asistencia a una cita de otra oficina
    if not current_user.can_admin(MODULO) and cit_cita.oficina != current_user.oficina:
        abort(403)
    if cit_cita.estado != "PENDIENTE":
        flash("No puede marcar la asistencia de una cita que no tenga estado de PENDIENTE.", "warning")
        return redirect(url_for("cit_citas.detail", cit_cita_id=cit_cita.id))
    # No se puede marcar la asistencia de una cita a futuro
    if cit_cita.inicio > datetime.now():
        flash("No puede marcar la asistencia de una cita que aún no ha pasado.", "warning")
        return redirect(url_for("cit_citas.detail", cit_cita_id=cit_cita.id))

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
    if qr is False:
        return redirect(url_for("cit_citas.detail", cit_cita_id=cit_cita.id))


@cit_citas.route("/cit_citas/pendiente/<int:cit_cita_id>")
@permission_required(MODULO, Permiso.MODIFICAR)
def pending(cit_cita_id):
    """Marcar la Cita como Pendiente"""
    cit_cita = CitCita.query.get_or_404(cit_cita_id)
    # Si no es administrador, no puede desmarcar una asistencia de una cita de otra oficina
    if not current_user.can_admin(MODULO) and cit_cita.oficina != current_user.oficina:
        abort(403)

    # No se puede marcar la des-asistencia de una cita que no este en estado de asistio
    if cit_cita.estado != "ASISTIO":
        flash("No puede desmarcar al asistencia de una cita que no tenga el estado previo de ASISTIO.", "warning")
        return redirect(url_for("cit_citas.detail", cit_cita_id=cit_cita.id))

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


@cit_citas.route("/cit_citas/buscar", methods=["GET", "POST"])
def search():
    """Buscar cit_citas"""
    if current_user.can_admin(MODULO):
        form_search = CitCitaSearchAdminForm()
    else:
        form_search = CitCitaSearchForm()

    if form_search.validate_on_submit():
        busqueda = {"estatus": "A"}
        titulos = []

        if form_search.cliente.data:
            cliente = safe_string(form_search.cliente.data)
            if cliente != "":
                busqueda["cit_cliente"] = cliente
                titulos.append("cit_cliente " + cliente)
        if form_search.email.data:
            email = safe_text(form_search.email.data, to_uppercase=False)
            if email != "":
                busqueda["cit_cliente_email"] = email
                titulos.append("email " + email)
        if form_search.fecha.data:
            fecha = form_search.fecha.data
            if fecha != "":
                busqueda["fecha"] = fecha.strftime("%Y-%m-%d")
                titulos.append("fecha " + fecha.strftime("%Y-%m-%d"))
        if form_search.oficina.data:
            oficina_id = form_search.oficina.data
            if oficina_id != "":
                busqueda["oficina_id"] = oficina_id
                oficina = Oficina.query.get_or_404(oficina_id)
                titulos.append("oficina " + oficina.clave)
        else:
            if form_search.distrito.data:
                distrito = form_search.distrito.data
                if distrito != "":
                    busqueda["distrito_id"] = distrito.id
                    titulos.append("distrito " + distrito.nombre_corto)

        return render_template(
            "cit_citas/list_search.jinja2",
            filtros=json.dumps(busqueda),
            titulo="Citas con " + ", ".join(titulos),
            estatus="A",
        )

    return render_template("cit_citas/search.jinja2", form=form_search)


@cit_citas.route("/cit_citas/asistencia/<string:cit_cita_id_encode>")
def assistance_qr(cit_cita_id_encode):
    """Marcado de asistencia a una cita direccionando vía código QR"""
    # Se descodifica el hash para saber que cita_id se trata
    cit_cita_id = CitCita.decode_id(cit_cita_id_encode)
    if cit_cita_id is None or cit_cita_id == "":
        flash("!ERROR: La cita que busca no se encuentra", "danger")
        return render_template("cit_citas/assistance.jinja2", cit_cita=0, asistencia=False)
    # Identificamos la cita correspondiente
    cit_cita = CitCita.query.get_or_404(cit_cita_id)
    if cit_cita.estado == "ASISTIO":
        return render_template("cit_citas/assistance.jinja2", cit_cita=cit_cita, asistencia=True)
    # rango de aceptación para dar asistencia a una cita
    if datetime.now() - timedelta(hours=24) <= cit_cita.inicio <= datetime.now() + timedelta(hours=8):
        if cit_cita.estado == "PENDIENTE":
            assistance(cit_cita.id, True)
            return render_template("cit_citas/assistance.jinja2", cit_cita=cit_cita, asistencia=True)
    else:
        flash("El rango aceptable para dar una asistencia ha sido superado.", "warning")

    return render_template("cit_citas/assistance.jinja2", cit_cita=cit_cita, asistencia=False)
