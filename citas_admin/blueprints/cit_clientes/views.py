"""
Cit Clientes, vistas
"""
import json
import os
from pathlib import Path
from flask import Blueprint, render_template, request, url_for, flash, redirect
from flask_login import login_required, current_user

from lib.datatables import get_datatable_parameters, output_datatable_json
from lib.safe_string import safe_string, safe_text, safe_message, safe_email, safe_curp, safe_tel

from dotenv import load_dotenv

from citas_admin.blueprints.permisos.models import Permiso
from citas_admin.blueprints.bitacoras.models import Bitacora
from citas_admin.blueprints.modulos.models import Modulo
from citas_admin.blueprints.usuarios.decorators import permission_required
from citas_admin.blueprints.cit_clientes.models import CitCliente
from citas_admin.blueprints.cit_clientes_recuperaciones.models import CitClienteRecuperacion

from citas_admin.blueprints.cit_clientes.forms import ClienteEditForm

FILE_NAME = "citas_admin/blueprints/cit_clientes/data/reporte.json"
MODULO = "CIT CLIENTES"

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
        reporte_nuevo=_leer_estado_reporte(),
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
        reporte_nuevo=_leer_estado_reporte(),
    )


@cit_clientes.route("/cit_clientes/<int:cit_cliente_id>")
def detail(cit_cliente_id):
    """Detalle de un Cliente"""
    cit_cliente = CitCliente.query.get_or_404(cit_cliente_id)
    # Revisar si el cliente está en estado de recuperación
    recuperacion = CitClienteRecuperacion.query
    recuperacion = recuperacion.filter_by(estatus="A").filter_by(cit_cliente_id=cit_cliente_id)
    recuperacion = recuperacion.filter_by(ya_recuperado=False)
    recuperacion = recuperacion.first()

    url = None
    if recuperacion:
        load_dotenv()  # Take environment variables from .env
        RECOVER_ACCOUNT_CONFIRM_URL = os.getenv("RECOVER_ACCOUNT_CONFIRM_URL", "https://citas.justiciadigital.gob.mx/recover_account_confirm")
        url = f"{RECOVER_ACCOUNT_CONFIRM_URL}?hashid={recuperacion.encode_id()}&cadena_validar={recuperacion.cadena_validar}"

    return render_template(
        "cit_clientes/detail.jinja2",
        cit_cliente=cit_cliente,
        recuperacion=recuperacion,
        url_recuperacion=url,
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
    # Mostrar detalle del cliente
    return redirect(url_for("cit_clientes.detail", cit_cliente_id=cliente_recuperacion.cit_cliente_id))


@cit_clientes.route("/cit_clientes/edicion/<int:cit_cliente_id>", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.MODIFICAR)
def edit(cit_cliente_id):
    """Editar Cliente"""
    cliente = CitCliente.query.get_or_404(cit_cliente_id)
    form = ClienteEditForm()
    if form.validate_on_submit():
        # --- Validaciones ---
        # Validar CURP repetido
        curp = safe_curp(form.curp.data)
        if curp == "" or curp is None:
            flash("El formato de la CURP no es válido.", "warning")
            return render_template("cit_clientes/edit.jinja2", form=form, cit_cliente=cliente)
        curp_repetido = CitCliente.query.filter_by(curp=curp).filter(CitCliente.id != cit_cliente_id).first()
        if curp_repetido:
            flash(f'Esta CURP ya se encuentra en uso. La utiliza el cliente: "{curp_repetido.nombre}"', "danger")
            return render_template("cit_clientes/edit.jinja2", form=form, cit_cliente=cliente)
        # Validar email repetido
        email = safe_email(form.email.data)
        if email == "":
            flash("El formato del EMAIL no es válido.", "warning")
            return render_template("cit_clientes/edit.jinja2", form=form, cit_cliente=cliente)
        email_repetido = CitCliente.query.filter_by(email=email).filter(CitCliente.id != cit_cliente_id).first()
        if email_repetido:
            flash(f'Este EMAIL ya se encuentra en uso. La utiliza el cliente: "{email_repetido.nombre}"', "danger")
            return render_template("cit_clientes/edit.jinja2", form=form, cit_cliente=cliente)
        # Validar teléfono repetido
        telefono = safe_tel(form.telefono.data)
        if telefono == "" or telefono is None or len(telefono) < 10:
            flash("El formato del TELEFONO no es válido.", "warning")
            return render_template("cit_clientes/edit.jinja2", form=form, cit_cliente=cliente)
        telefono_repetido = CitCliente.query.filter_by(telefono=telefono).filter(CitCliente.id != cit_cliente_id).first()
        if telefono_repetido:
            flash(f'Este TELEFONO ya se encuentra en uso. La utiliza el cliente: "{telefono_repetido.nombre}"', "danger")
            return render_template("cit_clientes/edit.jinja2", form=form, cit_cliente=cliente)
        # --- Fin Validaciones ---
        cliente.nombres = safe_string(form.nombres.data)
        cliente.apellido_primero = safe_string(form.apellido_primero.data)
        cliente.apellido_segundo = safe_string(form.apellido_segundo.data)
        cliente.curp = curp
        cliente.email = email
        cliente.telefono = telefono
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
    form.nombres.data = cliente.nombres
    form.apellido_primero.data = cliente.apellido_primero
    form.apellido_segundo.data = cliente.apellido_segundo
    form.curp.data = cliente.curp
    form.email.data = cliente.email
    form.telefono.data = cliente.telefono
    return render_template("cit_clientes/edit.jinja2", form=form, cit_cliente=cliente)


def _read_file_report():
    """Rutina para abrir y leer el archivo de reportes"""
    # Revisa si existe el archivo de reporte
    ruta = Path(FILE_NAME)
    if not ruta.exists():
        flash(f"AVISO: La ruta '{ruta}' no se encontró.", "danger")
        return render_template("cit_clientes/reports.jinja2")
    if not ruta.is_file():
        flash(f"AVISO: {ruta.name} no es un archivo.", "danger")
        return render_template("cit_clientes/reports.jinja2")
    # Abrimos el archivo de reporte JSON
    archivo = open(FILE_NAME, "r")
    data = json.load(archivo)
    archivo.close()

    return data


def _leer_estado_reporte():
    """Lee el estado del reporte"""
    data = _read_file_report()
    return data["consultado"]


def _escribir_estado_reporte():
    """Escribe el estado del reporte"""
    data = _read_file_report()
    data["consultado"] = True
    with open(FILE_NAME, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


@cit_clientes.route("/cit_clientes/avisos")
def report_list():
    """Lectura y presentación de los reportes creados para Clientes"""
    data = _read_file_report()

    if data["consultado"] == False:
        _escribir_estado_reporte()

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
                renglon["valor"] += '<strong>' + str(llave) + ':</strong> ' + str(valor) + '<br/>'
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
        # current_user.launch_task(
        #     nombre="cit_clientes.tasks.refresh_report",
        #     descripcion=f"Actualiza el reporte de errores de cit_clientes"
        # )
        flash("Se está actualizando el reporte de errores de clientes...", "info")
    # Mostrar reporte de errores del cliente
    return redirect(url_for("cit_clientes.reports"))
