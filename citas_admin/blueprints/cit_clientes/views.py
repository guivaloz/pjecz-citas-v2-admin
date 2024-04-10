"""
Cit Clientes, vistas
"""

import json
import os
from datetime import datetime, timedelta

from flask import Blueprint, render_template, request, url_for, flash, redirect
from flask_login import login_required, current_user
from sqlalchemy import or_

from config.settings import get_settings
from lib.datatables import get_datatable_parameters, output_datatable_json
from lib.exceptions import MyFilenameError, MyNotAllowedExtensionError, MyUnknownExtensionError
from lib.safe_string import safe_string, safe_text, safe_message, safe_email, safe_curp, safe_telefono
from lib.storage import GoogleCloudStorage

from citas_admin.blueprints.cit_clientes.forms import CitClienteEditForm, CitClienteNewForm
from citas_admin.blueprints.cit_clientes.models import CitCliente
from citas_admin.blueprints.cit_clientes_recuperaciones.models import CitClienteRecuperacion
from citas_admin.blueprints.bitacoras.models import Bitacora
from citas_admin.blueprints.modulos.models import Modulo
from citas_admin.blueprints.permisos.models import Permiso
from citas_admin.blueprints.usuarios.decorators import permission_required
from citas_admin.extensions import pwd_context

FILE_NAME = "cit_clientes_reporte.json"
MODULO = "CIT CLIENTES"
RECOVER_ACCOUNT_CONFIRM_URL = os.getenv("RECOVER_ACCOUNT_CONFIRM_URL", "")

cit_clientes = Blueprint("cit_clientes", __name__, template_folder="templates")


@cit_clientes.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""


@cit_clientes.route("/cit_clientes/datatable_json", methods=["GET", "POST"])
def datatable_json():
    """DataTable JSON para listado de Clientes"""
    # Tomar parámetros de Datatables
    draw, start, rows_per_page = get_datatable_parameters()
    # Consultar
    consulta = CitCliente.query
    if "estatus" in request.form:
        consulta = consulta.filter_by(estatus=request.form["estatus"])
    else:
        consulta = consulta.filter_by(estatus="A")
    if "email" in request.form:
        consulta = consulta.filter(CitCliente.email.contains(safe_text(request.form["email"], to_uppercase=False)))
    if "nombres" in request.form:
        consulta = consulta.filter(CitCliente.nombres.contains(safe_string(request.form["nombres"])))
    if "apellido_primero" in request.form:
        consulta = consulta.filter(CitCliente.apellido_primero.contains(safe_string(request.form["apellido_primero"])))
    if "curp" in request.form:
        consulta = consulta.filter(CitCliente.curp.contains(safe_string(request.form["curp"])))
    if "telefono" in request.form:
        consulta = consulta.filter(CitCliente.telefono.contains(safe_telefono(request.form["telefono"])))
    if "nombre_completo" in request.form:
        palabras = safe_string(request.form["nombre_completo"]).split(" ")
        for palabra in palabras:
            consulta = consulta.filter(
                or_(
                    CitCliente.nombres.contains(palabra),
                    CitCliente.apellido_primero.contains(palabra),
                    CitCliente.apellido_segundo.contains(palabra),
                )
            )
    registros = consulta.order_by(CitCliente.modificado.desc()).offset(start).limit(rows_per_page).all()
    total = consulta.count()
    # Elaborar datos para DataTable
    data = []
    for resultado in registros:
        data.append(
            {
                "detalle": {
                    "email": resultado.email,
                    "url": url_for("cit_clientes.detail", cit_cliente_id=resultado.id),
                },
                "nombre": resultado.nombre,
                "curp": resultado.curp,
                "telefono": resultado.telefono_formato,
            }
        )
    # Entregar JSON
    return output_datatable_json(draw, total, data)


@cit_clientes.route("/cit_clientes")
def list_active():
    """Listado de Clientes activos"""
    return render_template(
        "cit_clientes/list.jinja2",
        filtros=json.dumps({"estatus": "A"}),
        titulo="Clientes",
        estatus="A",
    )


@cit_clientes.route("/cit_clientes/inactivos")
@permission_required(MODULO, Permiso.MODIFICAR)
def list_inactive():
    """Listado de Clientes inactivos"""
    return render_template(
        "cit_clientes/list.jinja2",
        filtros=json.dumps({"estatus": "B"}),
        titulo="Clientes inactivos",
        estatus="B",
    )


@cit_clientes.route("/cit_clientes/<int:cit_cliente_id>")
def detail(cit_cliente_id):
    """Detalle de un Cliente"""
    cit_cliente = CitCliente.query.get_or_404(cit_cliente_id)

    # Si el cliente ha solicitado recuperar su contrasena, definir url_recuperacion
    url_recuperacion = None
    recuperacion = CitClienteRecuperacion.query
    recuperacion = recuperacion.filter_by(estatus="A").filter_by(cit_cliente_id=cit_cliente_id)
    recuperacion = recuperacion.filter_by(ya_recuperado=False)
    recuperacion = recuperacion.first()
    if recuperacion and RECOVER_ACCOUNT_CONFIRM_URL != "":
        url_recuperacion = (
            f"{RECOVER_ACCOUNT_CONFIRM_URL}?hashid={recuperacion.encode_id()}&cadena_validar={recuperacion.cadena_validar}"
        )

    # Entregar
    return render_template(
        "cit_clientes/detail.jinja2",
        cit_cliente=cit_cliente,
        recuperacion=recuperacion,
        url_recuperacion=url_recuperacion,
    )


@cit_clientes.route("/cit_clientes/enviar_recuperacion_contrasena/<int:cit_cliente_recuperacion_id>")
@permission_required(MODULO, Permiso.MODIFICAR)
def send_email_recover_password(cit_cliente_recuperacion_id):
    """Envía el correo de recuperación de contraseña"""
    cliente_recuperacion = CitClienteRecuperacion.query.get_or_404(cit_cliente_recuperacion_id)

    # Salir si hay una tarea en el fondo
    if current_user.get_task_in_progress("cit_clientes_recuperaciones.tasks.enviar"):
        flash("Debe esperar porque hay una tarea en el fondo sin terminar.", "warning")
    else:
        # Lanzar tarea en el fondo
        current_user.launch_task(
            nombre="cit_clientes_recuperaciones.tasks.enviar",
            descripcion=f"Enviar correo de recuperación de contraseña al cliente {cliente_recuperacion.cit_cliente_id}",
            cit_cliente_recuperacion_id=cliente_recuperacion.id,
        )
        flash("Se está reenviando un correo de recuperación de contraseña al cliente... ", "info")

    # Redirigir al detalle
    return redirect(url_for("cit_clientes.detail", cit_cliente_id=cliente_recuperacion.cit_cliente_id))


@cit_clientes.route("/cit_clientes/edicion/<int:cit_cliente_id>", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.MODIFICAR)
def edit(cit_cliente_id):
    """Editar Cliente"""
    cliente = CitCliente.query.get_or_404(cit_cliente_id)
    form = CitClienteEditForm()
    if form.validate_on_submit():

        # Validar que el CURP no se repita
        curp = safe_curp(form.curp.data)
        if curp == "" or curp is None:
            flash("El formato de la CURP no es válido.", "warning")
            return render_template("cit_clientes/edit.jinja2", form=form, cit_cliente=cliente)
        curp_repetido = CitCliente.query.filter_by(curp=curp).filter(CitCliente.id != cit_cliente_id).first()
        if curp_repetido:
            flash(f'Esta CURP ya se encuentra en uso. La utiliza el cliente: "{curp_repetido.nombre}"', "danger")
            return render_template("cit_clientes/edit.jinja2", form=form, cit_cliente=cliente)

        # Validar que el e-mail no se repita
        email = safe_email(form.email.data)
        if email == "":
            flash("El formato del EMAIL no es válido.", "warning")
            return render_template("cit_clientes/edit.jinja2", form=form, cit_cliente=cliente)
        email_repetido = CitCliente.query.filter_by(email=email).filter(CitCliente.id != cit_cliente_id).first()
        if email_repetido:
            flash(f'Este EMAIL ya se encuentra en uso. La utiliza el cliente: "{email_repetido.nombre}"', "danger")
            return render_template("cit_clientes/edit.jinja2", form=form, cit_cliente=cliente)

        # Validar limite de citas
        limite_citas = form.limite_citas.data
        if limite_citas is None or limite_citas > 500 or limite_citas < 0:
            flash("El límite de citas esta fuera de rango.", "warning")
            return render_template("cit_clientes/edit.jinja2", form=form, cit_cliente=cliente)

        # Actualizar
        cliente.nombres = safe_string(form.nombres.data)
        cliente.apellido_primero = safe_string(form.apellido_primero.data)
        cliente.apellido_segundo = safe_string(form.apellido_segundo.data)
        cliente.curp = curp
        cliente.email = email
        cliente.telefono = safe_telefono(form.telefono.data)
        cliente.limite_citas_pendientes = form.limite_citas.data
        cliente.enviar_boletin = form.recibir_boletin.data
        cliente.save()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Editado Cliente {cliente.nombre}"),
            url=url_for("cit_clientes.detail", cit_cliente_id=cliente.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
        return redirect(bitacora.url)

    # Entregar
    form.nombres.data = cliente.nombres
    form.apellido_primero.data = cliente.apellido_primero
    form.apellido_segundo.data = cliente.apellido_segundo
    form.curp.data = cliente.curp
    form.email.data = cliente.email
    form.telefono.data = cliente.telefono
    form.limite_citas.data = cliente.limite_citas_pendientes
    form.recibir_boletin.data = cliente.enviar_boletin
    return render_template("cit_clientes/edit.jinja2", form=form, cit_cliente=cliente)


def _read_file_report():
    """Rutina para abrir y leer el archivo de reportes"""
    # Preparar Google Storage
    storage = GoogleCloudStorage("/")
    contenido_json = ""
    # Subir el archivo a la nube (Google Storage)
    try:
        contenido_json = storage.download_as_string("json/" + FILE_NAME)
    except (MyFilenameError, MyNotAllowedExtensionError, MyUnknownExtensionError):
        flash("No se ha configurado el almacenamiento en la nube.", "warning")
        return None
    except Exception:
        flash("Error al leer el archivo.", "warning")
        return None
    # Abrimos el archivo de reporte JSON
    return json.loads(contenido_json)


@cit_clientes.route("/cit_clientes/avisos")
def report_list():
    """Lectura y presentación de los reportes creados para Clientes"""
    data = _read_file_report()
    if data is None:
        flash(f"AVISO: {FILE_NAME} no es un archivo.", "danger")
        return render_template(
            "cit_clientes/report_list.jinja2",
            fecha_creacion="",
        )
    return render_template(
        "cit_clientes/report_list.jinja2",
        fecha_creacion=data["fecha_creacion"],
        reporte=data["reportes"],
    )


@cit_clientes.route("/cit_clientes/aviso/<int:reporte_id>", methods=["GET", "POST"])
def report_detail(reporte_id):
    """Lectura a detalle del reporte"""
    data = _read_file_report()
    # Construir tabla de resultados
    resultados = []
    renglon = {}
    for resultado in data["reportes"][reporte_id]["resultados"]:
        renglon = {}
        renglon["valor"] = ""
        for llave, valor in resultado.items():
            if llave == "id":
                renglon["id"] = valor
            else:
                renglon["valor"] += "<strong>" + str(llave) + ":</strong> " + str(valor) + "<br/>"
        resultados.append(renglon)
    return render_template(
        "cit_clientes/report_detail.jinja2",
        fecha_creacion=data["fecha_creacion"],
        reporte=data["reportes"][reporte_id],
        resultados=resultados,
    )


@cit_clientes.route("/cit_clientes/actualizar_reporte/")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def refresh_report():
    """Actualiza el reporte de avisos de clientes"""
    # Salir si hay una tarea en el fondo
    if current_user.get_task_in_progress("cit_clientes.tasks.refresh_report"):
        flash("Debe esperar porque hay una tarea en el fondo sin terminar.", "warning")
    else:
        # Lanzar tarea en el fondo
        current_user.launch_task(
            nombre="cit_clientes.tasks.refresh_report",
            descripcion="Actualiza el reporte de errores de cit_clientes",
        )
        flash("Se está actualizando el reporte de errores de clientes...", "info")
    # Mostrar reporte de errores del cliente
    return redirect(url_for("cit_clientes.list_active"))


@cit_clientes.route("/cit_clientes/nuevo", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.CREAR)
def new():
    """Nuevo Cliente"""
    form = CitClienteNewForm()
    if form.validate_on_submit():
        # Validar que el CURP no se repita
        curp = safe_curp(form.curp.data)
        if curp == "" or curp is None:
            mensaje = "El formato de la <strong>CURP</strong> no es válido."
            return render_template("cit_clientes/new.jinja2", form=form, mensaje=mensaje)
        curp_repetido = CitCliente.query.filter_by(curp=curp).first()
        if curp_repetido:
            mensaje = f"Esta <strong>CURP</strong> ya se encuentra en uso.<br/>\
                Lo utiliza el Cliente:<br/>\
                <strong>Nombre:</strong> {curp_repetido.nombre} <br/>\
                <strong>CURP:</strong> <span class='text-danger'><strong>{curp_repetido.curp}</strong></span> <br/>\
                <strong>Email:</strong> {curp_repetido.email}"
            return render_template("cit_clientes/new.jinja2", form=form, mensaje=mensaje, cit_cliente=curp_repetido)

        # Validar que el e-mail no se repita
        email = safe_email(form.email.data)
        if email == "":
            mensaje = "El formato del <strong>EMAIL</strong> no es válido."
            return render_template("cit_clientes/new.jinja2", form=form, mensaje=mensaje)
        email_repetido = CitCliente.query.filter_by(email=email).first()
        if email_repetido:
            mensaje = f"Este <strong>EMAIL</strong> ya se encuentra en uso.<br/>\
                Lo utiliza el Cliente:<br/>\
                <strong>Nombre:</strong> {email_repetido.nombre} <br/>\
                <strong>CURP:</strong> {email_repetido.curp} <br/>\
                <strong>Email:</strong> <span class='text-danger'><strong>{email_repetido.email}</strong></span>"
            return render_template("cit_clientes/new.jinja2", form=form, mensaje=mensaje, cit_cliente=email_repetido)

        # Definir la fecha de renovación
        renovacion_fecha = datetime.now() + timedelta(days=360)

        cliente = CitCliente(
            nombres=safe_string(form.nombres.data),
            apellido_primero=safe_string(form.apellido_primero.data),
            apellido_segundo=safe_string(form.apellido_segundo.data),
            curp=safe_string(form.curp.data),
            email=email,
            telefono=safe_telefono(form.telefono.data),
            contrasena_md5="",
            contrasena_sha256=pwd_context.hash(form.contrasena.data),
            renovacion=renovacion_fecha.date(),
            limite_citas_pendientes=LIMITE_CITAS_PENDIENTES,
        )
        cliente.save()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Nuevo cliente {cliente.email}: {cliente.nombre}"),
            url=url_for("cit_clientes.detail", cit_cliente_id=cliente.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
        return redirect(bitacora.url)
    # Entregar
    return render_template("cit_clientes/new.jinja2", form=form)
