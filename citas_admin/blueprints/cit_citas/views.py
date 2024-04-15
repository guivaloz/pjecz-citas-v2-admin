"""
Cit Citas, vistas
"""

from datetime import datetime, timedelta
import json

from flask import Blueprint, flash, redirect, render_template, request, url_for, abort
from flask_login import current_user, login_required
from pytz import timezone
from sqlalchemy import or_

from lib.datatables import get_datatable_parameters, output_datatable_json
from lib.safe_string import safe_message, safe_string, safe_text
from lib.pwgen import generar_codigo_asistencia

from citas_admin.blueprints.bitacoras.models import Bitacora
from citas_admin.blueprints.cit_citas.models import CitCita
from citas_admin.blueprints.cit_clientes.models import CitCliente
from citas_admin.blueprints.cit_horas_bloqueadas.models import CitHoraBloqueada
from citas_admin.blueprints.cit_oficinas_servicios.models import CitOficinaServicio
from citas_admin.blueprints.cit_servicios.models import CitServicio
from citas_admin.blueprints.modulos.models import Modulo
from citas_admin.blueprints.oficinas.models import Oficina
from citas_admin.blueprints.permisos.models import Permiso
from citas_admin.blueprints.usuarios.decorators import permission_required
from citas_admin.blueprints.usuarios_oficinas.models import UsuarioOficina

from citas_admin.blueprints.cit_citas.forms import CitCitaSearchForm, CitCitaSearchAdminForm, CitCitaAssistance, CitCitaNew

HUSO_HORARIO = "America/Mexico_City"
LIMITE_CITAS = 5
LIMITE_EXTRA_PERSONAS = 2
MODULO = "CIT CITAS"
MINUTOS_MARGEN = 5

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
    if "id" in request.form:
        consulta = consulta.filter_by(id=request.form["id"])
    if "cit_cliente_id" in request.form:
        consulta = consulta.filter_by(cit_cliente_id=request.form["cit_cliente_id"])
    if "cit_cliente" in request.form:
        consulta = consulta.join(CitCliente)
        consulta = consulta.filter(CitCliente.nombres.contains(request.form["cit_cliente"]))
    if "cit_cliente_email" in request.form:
        consulta = consulta.join(CitCliente)
        consulta = consulta.filter(CitCliente.email.contains(request.form["cit_cliente_email"]))
    if "oficina_id" in request.form:
        consulta = consulta.filter_by(oficina_id=request.form["oficina_id"])
    if "nombre_completo" in request.form:
        palabras = safe_string(request.form["nombre_completo"]).split(" ")
        consulta = consulta.join(CitCliente)
        for palabra in palabras:
            consulta = consulta.filter(
                or_(
                    CitCliente.nombres.contains(palabra),
                    CitCliente.apellido_primero.contains(palabra),
                    CitCliente.apellido_segundo.contains(palabra),
                )
            )
    if "cit_servicio_id" in request.form:
        consulta = consulta.filter_by(cit_servicio_id=request.form["cit_servicio_id"])
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
                    "url": (
                        url_for("cit_clientes.detail", cit_cliente_id=cita.cit_cliente.id)
                        if current_user.can_view("CIT CLIENTES")
                        else ""
                    ),
                },
                "cit_servicio": {
                    "clave": cita.cit_servicio.clave,
                    "url": (
                        url_for("cit_servicios.detail", cit_servicio_id=cita.cit_servicio.id)
                        if current_user.can_view("CIT SERVICIOS")
                        else ""
                    ),
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

    # Si es administrador, entregar las citas de todas las oficinas
    if current_user.can_admin(MODULO):
        oficinas = Oficina.query.filter_by(estatus="A").filter_by(puede_agendar_citas=True).order_by(Oficina.clave).all()

        return render_template(
            "cit_citas/list_admin.jinja2",
            filtros=json.dumps({"estatus": "A", "fecha": fecha_str}),
            titulo="Todas las Citas" if fecha is None else f"Todas las citas del {fecha_str}",
            estatus="A",
            fecha_actual=fecha_str,
            fecha_anterior=fecha_anterior_str,
            fecha_siguiente=fecha_siguiente_str,
            oficinas=oficinas,
        )

    # Verificamos si tiene asignadas varias oficinas
    oficinas_usr = (
        UsuarioOficina.query.join(Oficina)
        .filter(UsuarioOficina.usuario_id == current_user.id)
        .filter_by(estatus="A")
        .order_by(Oficina.descripcion_corta)
        .all()
    )

    # NO es administrador, entregar las citas de su propia oficina
    return render_template(
        "cit_citas/list.jinja2",
        filtros=json.dumps({"estatus": "A", "oficina_id": current_user.oficina_id, "fecha": fecha_str}),
        titulo=f"Citas del {current_user.oficina.descripcion_corta}",
        estatus="A",
        fecha_actual=fecha_str,
        fecha_anterior=fecha_anterior_str,
        fecha_siguiente=fecha_siguiente_str,
        oficinas=oficinas_usr,
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

    # Si es administrador, entregar las citas de todas las oficinas
    if current_user.can_admin(MODULO):
        return render_template(
            "cit_citas/list_admin.jinja2",
            filtros=json.dumps({"estatus": "B", "fecha": fecha_str}),
            titulo="Todas las Citas eliminadas" if fecha is None else f"Todas las citas del {fecha_str}",
            estatus="B",
            fecha_anterior=fecha_anterior_str,
            fecha_siguiente=fecha_siguiente_str,
        )

    # NO es administrador, entregar las citas de su propia oficina
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

    # Consultar
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

    # Si tiene acceso a varias oficinas
    oficinas = (
        UsuarioOficina.query.filter_by(usuario=current_user).filter_by(oficina=cit_cita.oficina).filter_by(estatus="A").first()
    )
    if oficinas is not None:
        return render_template("cit_citas/detail.jinja2", cit_cita=cit_cita, marcar_asistencia=marcar_asistencia)

    # No puede ver la cita
    abort(403)


@cit_citas.route("/cit_citas/eliminar/<int:cit_cita_id>")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def delete(cit_cita_id):
    """Eliminar Cita"""

    # Consultar
    cit_cita = CitCita.query.get_or_404(cit_cita_id)

    # Si no es administrador, no puede eliminar un cita de otra oficina
    if not current_user.can_admin(MODULO) and cit_cita.oficina != current_user.oficina:
        abort(403)

    # Si tiene estatus "A", eliminar
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
@permission_required(MODULO, Permiso.ADMINISTRAR)
def recover(cit_cita_id):
    """Recuperar Cita"""

    # Consultar
    cit_cita = CitCita.query.get_or_404(cit_cita_id)

    # Si no es administrador, no puede eliminar un cita de otra oficina
    if not current_user.can_admin(MODULO) and cit_cita.oficina != current_user.oficina:
        abort(403)

    # Si tiene estatus "B", recuperar
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


@cit_citas.route("/cit_citas/asistencia/<int:cit_cita_id>", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.MODIFICAR)
def assistance(cit_cita_id, qr=False):
    """Marcar Asistencia a una Cita"""

    # Consultar
    cit_cita = CitCita.query.get_or_404(cit_cita_id)

    # Si viene el formulario
    form = CitCitaAssistance()
    if form.validate_on_submit():

        # Validar el estatus
        if cit_cita.estatus != "A":
            flash("No puede marcar la asistencia de una cita BORRADA.", "warning")
            return redirect(url_for("cit_citas.assistance", cit_cita_id=cit_cita.id))

        # Validar el estado
        if cit_cita.estado != "PENDIENTE":
            flash("No puede marcar la asistencia de una cita que no tenga estado de PENDIENTE.", "warning")
            return redirect(url_for("cit_citas.assistance", cit_cita_id=cit_cita.id))

        # No se puede marcar la asistencia de una cita en el futuro
        if cit_cita.inicio > datetime.now():
            flash("No puede marcar la asistencia de una cita que aún no ha pasado.", "warning")
            return redirect(url_for("cit_citas.assistance", cit_cita_id=cit_cita.id))

        # Validar el código de verificación
        if cit_cita.codigo_asistencia != form.codigo.data:
            flash("El código de verificación es incorrecto", "danger")
            return redirect(url_for("cit_citas.assistance", cit_cita_id=cit_cita.id))

        # Actualizar la cita
        cit_cita.estado = "ASISTIO"
        cit_cita.asistencia = True
        cit_cita.save()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Asistencia correcta en la Cita {cit_cita.id}"),
            url=url_for("cit_citas.detail", cit_cita_id=cit_cita.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")

        # Lanzar tarea en el fondo
        current_user.launch_task(
            nombre="cit_citas.tasks.enviar_asistio",
            descripcion="Enviar mensaje para informar que asistió a la cita",
            cit_cita_id=cit_cita.id,
        )
        flash("Se va a enviar un mensaje para informar que asistió a la cita", "info")

        # TODO: Porque si no se usa el QR, redireccionar
        if qr is False:
            return redirect(url_for("cit_citas.detail", cit_cita_id=cit_cita.id))

    # Entregar formulario
    form.cita_id.data = cit_cita_id
    form.cliente.data = cit_cita.cit_cliente.nombre
    return render_template("cit_citas/assistance.jinja2", form=form, cit_cita_id=cit_cita.id)


@cit_citas.route("/cit_citas/pendiente/<int:cit_cita_id>")
@permission_required(MODULO, Permiso.MODIFICAR)
def pending(cit_cita_id):
    """Marcar la Cita como Pendiente"""

    # Consultar
    cit_cita = CitCita.query.get_or_404(cit_cita_id)

    # Si no es administrador, no puede desmarcar una asistencia de una cita de otra oficina
    if not current_user.can_admin(MODULO) and cit_cita.oficina != current_user.oficina:
        abort(403)

    # No se puede marcar la des-asistencia de una cita que no este en estado de asistio
    if cit_cita.estado != "ASISTIO":
        flash("No puede desmarcar al asistencia de una cita que no tenga el estado previo de ASISTIO.", "warning")
        return redirect(url_for("cit_citas.detail", cit_cita_id=cit_cita.id))

    # Si el estatus es "A"
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

    # Entregar
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
        if "fecha" in request.form and form_search.fecha.data:
            fecha = form_search.fecha.data
            if fecha != "":
                busqueda["fecha"] = fecha.strftime("%Y-%m-%d")
                titulos.append("fecha " + fecha.strftime("%Y-%m-%d"))
        if "oficina" in request.form and form_search.oficina.data:
            oficina_id = form_search.oficina.data
            if oficina_id != "":
                busqueda["oficina_id"] = oficina_id
                oficina = Oficina.query.get_or_404(oficina_id)
                titulos.append("oficina " + oficina.clave)
        else:
            if "distrito" in request.form and form_search.distrito.data:
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
        return render_template("cit_citas/assistance_qr.jinja2", cit_cita=0, asistencia=False)

    # Identificamos la cita correspondiente
    cit_cita = CitCita.query.get_or_404(cit_cita_id)
    if cit_cita.estado == "ASISTIO":
        return render_template("cit_citas/assistance_qr.jinja2", cit_cita=cit_cita, asistencia=True)

    # Rango de aceptación para dar asistencia a una cita
    if datetime.now() - timedelta(hours=24) <= cit_cita.inicio <= datetime.now() + timedelta(hours=8):
        if cit_cita.estado == "PENDIENTE":
            assistance(cit_cita.id, True)
            return render_template("cit_citas/assistance_qr.jinja2", cit_cita=cit_cita, asistencia=True)
    else:
        flash("El rango de horario aceptable para dar asistencia ha sido superado.", "warning")

    # Entregar
    return render_template("cit_citas/assistance_qr.jinja2", cit_cita=cit_cita, asistencia=False)


@cit_citas.route("/cit_citas/nueva/<int:cit_cliente_id>", methods=["GET", "POST"])
def new(cit_cliente_id):
    """Nueva Cita"""

    # Consultar cliente
    cliente = CitCliente.query.get_or_404(cit_cliente_id)
    if cliente is None:
        flash(f"Error: el ID del cliente {cit_cliente_id} no existe.", "danger")

    # Listado de Oficinas donde puede agendar citas
    oficinas = UsuarioOficina.query.filter_by(usuario_id=current_user.id).filter_by(estatus="A").all()
    form = CitCitaNew()
    if form.validate_on_submit():

        # Validar datos
        if "oficina_id" not in request.form:
            flash("Error: Faltó indicar la oficina", "danger")
            return render_template("cit_citas/new.jinja2", cit_cliente=cliente, oficinas=oficinas, form=form)
        oficina = Oficina.query.get_or_404(request.form["oficina_id"])
        if oficina is None:
            flash(f"Error: el ID de la Oficina {request.form['oficina_id']} no existe.", "danger")
            return render_template("cit_citas/new.jinja2", cit_cliente=cliente, oficinas=oficinas, form=form)
        oficina_user = (
            UsuarioOficina.query.filter_by(usuario_id=current_user.id).filter_by(oficina=oficina).filter_by(estatus="A").first()
        )
        if oficina_user is None:
            flash(f"Error: Usted no tiene acceso a agendar citas en esta oficina {oficina.clave}.", "warning")
            return render_template("cit_citas/new.jinja2", cit_cliente=cliente, oficinas=oficinas, form=form)
        if "servicio_id" not in request.form:
            flash("Error: Faltó indicar el servicio", "danger")
            return render_template("cit_citas/new.jinja2", cit_cliente=cliente, oficinas=oficinas, form=form)
        servicio = CitServicio.query.get_or_404(request.form["servicio_id"])
        if servicio is None:
            flash(f"Error: el ID del Servicio {request.form['servicio_id']} no existe.", "danger")
            return render_template("cit_citas/new.jinja2", cit_cliente=cliente, oficinas=oficinas, form=form)
        oficina_servicio = (
            CitOficinaServicio.query.filter_by(oficina=oficina).filter_by(cit_servicio=servicio).filter_by(estatus="A").first()
        )
        if oficina_servicio is None:
            flash(f"Error: Este servicio {servicio.clave} no se atiende en la oficina {oficina.clave}.", "warning")
            return render_template("cit_citas/new.jinja2", cit_cliente=cliente, oficinas=oficinas, form=form)
        if "horario" not in request.form:
            flash("Error: Faltó indicar el horario", "danger")
            return render_template("cit_citas/new.jinja2", cit_cliente=cliente, oficinas=oficinas, form=form)
        fecha = datetime.now()
        hora_minutos = datetime.strptime(request.form["horario"], "%H:%M")
        horario = datetime(
            year=fecha.year,
            month=fecha.month,
            day=fecha.day,
            hour=hora_minutos.hour,
            minute=hora_minutos.minute,
            second=0,
        )

        # Validar si se puede agendar la cita
        count_citas = (
            CitCita.query.filter_by(oficina=oficina)
            .filter_by(inicio=horario)
            .filter(CitCita.estado != "CANCELO")
            .filter_by(estatus="A")
            .count()
        )
        if count_citas >= LIMITE_CITAS:
            flash(f"Error: Ya se alcanzó el límite de citas para ese horario. Límite: {LIMITE_CITAS}", "warning")
            return render_template("cit_citas/new.jinja2", cit_cliente=cliente, oficinas=oficinas, form=form)

        # Hacer el insert en la tabla
        cit_cita = CitCita(
            cit_cliente_id=cliente.id,
            cit_servicio_id=servicio.id,
            oficina_id=oficina.id,
            inicio=horario,
            termino=horario + timedelta(minutes=servicio.duracion.minute),
            notas="",
            estado="PENDIENTE",
            asistencia=False,
            codigo_asistencia=generar_codigo_asistencia(),
        )
        cit_cita.save()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Cita Inmediata Creada {cit_cita.id}"),
            url=url_for("cit_citas.detail", cit_cita_id=cit_cita.id),
        )
        bitacora.save()

        # Mostrar resultado
        flash(
            f"Cita agendada con éxito: {cit_cita.id}<br>\
            <strong>Cliente</strong>: {cliente.nombre}<br>\
            <strong>Oficina</strong>: {oficina.clave} : {oficina.descripcion_corta}<br>\
            <strong>Servicio</strong>: {servicio.clave} : {servicio.descripcion}<br>\
            <strong>Horario</strong>: {horario}<br>\
            <h5>Código de Asistencia: <pre>{cit_cita.codigo_asistencia}</pre></h5>",
            "success",
        )
        return redirect(url_for("cit_citas.list_active"))

    # Google App Engine usa tiempo universal, sin esta correccion las fechas de la noche cambian al dia siguiente
    ahora_utc = datetime.now(timezone("UTC"))
    ahora_mx_coah = ahora_utc.astimezone(timezone(HUSO_HORARIO))

    # Entregar
    return render_template(
        "cit_citas/new.jinja2",
        cit_cliente=cliente,
        oficinas=oficinas,
        form=form,
        hora_actual=ahora_mx_coah.strftime("%H:%M"),
    )


@cit_citas.route("/cit_citas/servicios/<int:oficina_id>", methods=["GET", "POST"])
def servicios_json(oficina_id):
    """Entrega los servicios de una oficina"""

    servicios = CitServicio.query.join(CitOficinaServicio).filter(CitOficinaServicio.oficina_id == oficina_id).all()

    # Elaborar datos para el Select2
    results = []
    for servicio in servicios:
        results.append({"value": servicio.id, "text": servicio.clave + " : " + servicio.descripcion})

    return {"results": results}


@cit_citas.route("/cit_citas/horarios/<int:oficina_id>/<int:servicio_id>", methods=["GET", "POST"])
def horarios_json(oficina_id, servicio_id):
    """Entrega los horarios disponibles para agendar"""

    # Google App Engine usa tiempo universal, sin esta correccion las fechas de la noche cambian al dia siguiente
    ahora_utc = datetime.now(timezone("UTC"))
    ahora_mx_coah = ahora_utc.astimezone(timezone(HUSO_HORARIO))

    # Validar oficina
    oficina = Oficina.query.get_or_404(oficina_id)
    if oficina is None:
        return {"results": []}

    # Validar Servicio
    cit_servicio = CitServicio.query.get_or_404(servicio_id)
    if cit_servicio is None:
        return {"results": []}

    # Tomar tiempos de inicio y termino de la oficina
    apertura = oficina.apertura
    cierre = oficina.cierre

    # Si el servicio tiene un tiempo desde
    if cit_servicio.desde and apertura < cit_servicio.desde:
        apertura = cit_servicio.desde
    # Si el cit_servicio tiene un tiempo hasta
    if cit_servicio.hasta and cierre > cit_servicio.hasta:
        cierre = cit_servicio.hasta

    # Definimos la hora actual y damos este momento como el inicio
    fecha = ahora_mx_coah

    # Definir los tiempos de inicio, de final y el timedelta de la duración
    tiempo_inicial = datetime(
        year=fecha.year,
        month=fecha.month,
        day=fecha.day,
        hour=apertura.hour,
        minute=apertura.minute,
        second=0,
    )
    tiempo_final = datetime(
        year=fecha.year,
        month=fecha.month,
        day=fecha.day,
        hour=cierre.hour,
        minute=cierre.minute,
        second=0,
    )
    duracion = timedelta(
        hours=cit_servicio.duracion.hour,
        minutes=cit_servicio.duracion.minute,
    )

    # Consultar las horas bloqueadas y convertirlas a datetime para compararlas
    tiempos_bloqueados = []
    cit_horas_bloqueadas = CitHoraBloqueada.query.filter_by(oficina_id=oficina.id).filter_by(fecha=fecha).filter_by(estatus="A")
    for cit_hora_bloqueada in cit_horas_bloqueadas:
        tiempo_bloquedo_inicia = datetime(
            year=fecha.year,
            month=fecha.month,
            day=fecha.day,
            hour=cit_hora_bloqueada.inicio.hour,
            minute=cit_hora_bloqueada.inicio.minute,
            second=0,
        )
        tiempo_bloquedo_termina = datetime(
            year=fecha.year,
            month=fecha.month,
            day=fecha.day,
            hour=cit_hora_bloqueada.termino.hour,
            minute=cit_hora_bloqueada.termino.minute,
            second=0,
        ) - timedelta(minutes=1)
        tiempos_bloqueados.append((tiempo_bloquedo_inicia, tiempo_bloquedo_termina))

    # Acumular las citas agendadas en un diccionario de tiempos y cantidad de citas, para la oficina en la fecha
    # { 08:30: 2, 08:45: 1, 10:00: 2,... }
    citas_ya_agendadas = {}
    cit_citas_anonimas = CitCita.query.filter_by(oficina_id=oficina.id)
    inicio_dt = datetime(year=fecha.year, month=fecha.month, day=fecha.day, hour=0, minute=0, second=0)
    termino_dt = datetime(year=fecha.year, month=fecha.month, day=fecha.day, hour=23, minute=59, second=59)
    cit_citas_anonimas = cit_citas_anonimas.filter(CitCita.inicio >= inicio_dt).filter(CitCita.inicio <= termino_dt)

    # Filtro por tiempo de termino
    hasta_tiempo = datetime(
        year=fecha.year,
        month=fecha.month,
        day=fecha.day,
        hour=23,
        minute=59,
        second=59,
    )
    cit_citas_anonimas = cit_citas_anonimas.filter(CitCita.termino <= hasta_tiempo).filter(CitCita.estado != "CANCELO")
    cit_citas_anonimas = cit_citas_anonimas.filter_by(estatus="A").order_by(CitCita.id).all()
    for cit_cita in cit_citas_anonimas:
        if cit_cita.inicio not in citas_ya_agendadas:
            citas_ya_agendadas[cit_cita.inicio] = 1
        else:
            citas_ya_agendadas[cit_cita.inicio] += 1

    # Bucle por los intervalos
    horas_minutos_disponibles = []
    tiempo = tiempo_inicial

    # Bucle para quitar segmentos de tiempos
    while tiempo < tiempo_final:
        # Bandera
        es_hora_disponible = True
        citas_agendadas = 0
        disabled = False
        # Quitar las horas bloqueadas
        for tiempo_bloqueado in tiempos_bloqueados:
            if tiempo_bloqueado[0] <= tiempo <= tiempo_bloqueado[1]:
                es_hora_disponible = False
                break
        # Quitar las horas ocupadas
        if tiempo in citas_ya_agendadas:
            citas_agendadas = citas_ya_agendadas[tiempo]
            if citas_ya_agendadas[tiempo] >= oficina.limite_personas + LIMITE_EXTRA_PERSONAS:
                es_hora_disponible = False
                disabled = True
        # Acumular si es hora disponible
        if es_hora_disponible:
            if tiempo > fecha.replace(tzinfo=None) - timedelta(minutes=MINUTOS_MARGEN):
                horas_minutos_disponibles.append(
                    {
                        "value": tiempo.time().strftime("%H:%M"),
                        "text": f"{tiempo.time().strftime('%H:%M')} - {citas_agendadas} personas",
                        "disabled": disabled,
                    }
                )
        # Siguiente intervalo
        tiempo = tiempo + duracion

    # Entregar
    return {"results": horas_minutos_disponibles}
