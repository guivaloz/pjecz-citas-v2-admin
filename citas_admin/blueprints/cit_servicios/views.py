"""
Cit Servicios, vistas
"""

import json
from datetime import time
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from lib.datatables import get_datatable_parameters, output_datatable_json
from lib.safe_string import safe_clave, safe_string, safe_message

from citas_admin.blueprints.bitacoras.models import Bitacora
from citas_admin.blueprints.cit_categorias.models import CitCategoria
from citas_admin.blueprints.cit_servicios.models import CitServicio
from citas_admin.blueprints.cit_servicios.forms import CitServicioForm
from citas_admin.blueprints.modulos.models import Modulo
from citas_admin.blueprints.permisos.models import Permiso
from citas_admin.blueprints.usuarios.decorators import permission_required

MODULO = "CIT SERVICIOS"

cit_servicios = Blueprint("cit_servicios", __name__, template_folder="templates")


@cit_servicios.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""


@cit_servicios.route("/cit_servicios/datatable_json", methods=["GET", "POST"])
def datatable_json():
    """DataTable JSON para listado de Servicios"""
    # Tomar parámetros de Datatables
    draw, start, rows_per_page = get_datatable_parameters()
    # Consultar
    consulta = CitServicio.query
    if "estatus" in request.form:
        consulta = consulta.filter_by(estatus=request.form["estatus"])
    else:
        consulta = consulta.filter_by(estatus="A")
    if "cit_categoria_id" in request.form:
        consulta = consulta.filter_by(cit_categoria_id=request.form["cit_categoria_id"])
    registros = consulta.order_by(CitServicio.clave).offset(start).limit(rows_per_page).all()
    total = consulta.count()
    # Elaborar datos para DataTable
    data = []
    for resultado in registros:
        data.append(
            {
                "detalle": {
                    "clave": resultado.clave,
                    "url": url_for("cit_servicios.detail", cit_servicio_id=resultado.id),
                },
                "descripcion": resultado.descripcion,
                "duracion": resultado.duracion.strftime("%H:%M"),
                "documentos_limite": resultado.documentos_limite,
                "cit_categoria": {
                    "nombre": resultado.cit_categoria.nombre,
                    "url": url_for("cit_categorias.detail", cit_categoria_id=resultado.cit_categoria.id),
                },
                "desde": "-" if resultado.desde is None else resultado.desde.strftime("%H:%M"),
                "hasta": "-" if resultado.hasta is None else resultado.hasta.strftime("%H:%M"),
                "dias_habilitados": (
                    "-"
                    if resultado.dias_habilitados == ""
                    else _conversion_dias_habilitados_numero_letra_abreviada(resultado.dias_habilitados)
                ),
            }
        )
    # Entregar JSON
    return output_datatable_json(draw, total, data)


@cit_servicios.route("/cit_servicios")
def list_active():
    """Listado de Servicios activos"""
    return render_template(
        "cit_servicios/list.jinja2",
        filtros=json.dumps({"estatus": "A"}),
        titulo="Servicios",
        estatus="A",
    )


@cit_servicios.route("/cit_servicios/inactivos")
@permission_required(MODULO, Permiso.MODIFICAR)
def list_inactive():
    """Listado de Servicios inactivos"""
    return render_template(
        "cit_servicios/list.jinja2",
        filtros=json.dumps({"estatus": "B"}),
        titulo="Servicios inactivos",
        estatus="B",
    )


@cit_servicios.route("/cit_servicios/<int:cit_servicio_id>")
def detail(cit_servicio_id):
    """Detalle de un Servicio"""
    cit_servicio = CitServicio.query.get_or_404(cit_servicio_id)
    # Cuando no hay horario en el servicio
    horario = ""
    if cit_servicio.desde is None and cit_servicio.hasta is None:
        horario = "No se especifica horario, se utilizará el de su oficina."
    else:
        if cit_servicio.desde is None:
            horario = f"Hora de apertura de la oficina hasta {cit_servicio.hasta.strftime('%H:%M')}"
        elif cit_servicio.hasta is None:
            horario = f"{cit_servicio.desde.strftime('%H:%M')} hasta hora de cierre de la oficina"
        else:
            horario = f"{cit_servicio.desde.strftime('%H:%M')} hasta {cit_servicio.hasta.strftime('%H:%M')}"
    # Dias habilitados
    dias_habilitados = _conversion_dias_habilitados_numero_letra(cit_servicio.dias_habilitados)
    if dias_habilitados == "LUNES, MARTES, MIERCOLES, JUEVES, VIERNES, ":
        dias_habilitados = "LUNES A VIERNES"
    # Entregar
    return render_template(
        "cit_servicios/detail.jinja2",
        cit_servicio=cit_servicio,
        horario=horario,
        dias_habilitados=dias_habilitados,
    )


@cit_servicios.route("/cit_servicios/nuevo/<int:cit_categoria_id>", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.CREAR)
def new(cit_categoria_id):
    """Nuevo Servicio"""
    cit_categoria = CitCategoria.query.get_or_404(cit_categoria_id)
    form = CitServicioForm()
    if form.validate_on_submit():
        es_valido = True
        # Validar que la clave no se repita
        clave = safe_clave(form.clave.data)
        if CitServicio.query.filter_by(clave=clave).first():
            es_valido = False
            flash("La clave ya está en uso. Debe de ser única.", "warning")
        # Validar horario
        if not _validar_horario(form.desde.data, form.hasta.data):
            flash("El horario no es válido", "warning")
            es_valido = False
        # Si no de define el limite de documentos, se deja en cero
        if form.documentos_limite.data:
            documentos_limite = form.documentos_limite.data
        else:
            documentos_limite = 0
        # Si es válido, guardar
        if es_valido:
            cit_servicio = CitServicio(
                cit_categoria=cit_categoria,
                clave=clave,
                descripcion=safe_string(form.descripcion.data, max_len=64),
                duracion=form.duracion.data,
                documentos_limite=documentos_limite,
                desde=form.desde.data,
                hasta=form.hasta.data,
                dias_habilitados=_conversion_dias_habilitados_letra_numero(form.dias_habilitados.data),
            )
            cit_servicio.save()
            bitacora = Bitacora(
                modulo=Modulo.query.filter_by(nombre=MODULO).first(),
                usuario=current_user,
                descripcion=safe_message(f"Nuevo Servicio {cit_servicio.descripcion}"),
                url=url_for("cit_servicios.detail", cit_servicio_id=cit_servicio.id),
            )
            bitacora.save()
            flash(bitacora.descripcion, "success")
            return redirect(bitacora.url)
    # Llenar el campo con el nombre de la categoria
    form.cit_categoria_nombre.data = cit_categoria.nombre
    # Entregar
    return render_template(
        "cit_servicios/new.jinja2",
        form=form,
        cit_categoria=cit_categoria,
    )


@cit_servicios.route("/cit_servicios/edicion/<int:cit_servicio_id>", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.MODIFICAR)
def edit(cit_servicio_id):
    """Editar Servicio"""
    cit_servicio = CitServicio.query.get_or_404(cit_servicio_id)
    form = CitServicioForm()
    if form.validate_on_submit():
        es_valido = True
        # Si cambia la clave verificar que no este en uso
        clave = safe_clave(form.clave.data)
        if cit_servicio.clave != clave:
            cit_servicio_existente = CitServicio.query.filter_by(clave=clave).first()
            if cit_servicio_existente and cit_servicio_existente.id != cit_servicio.id:
                es_valido = False
                flash("La clave ya está en uso. Debe de ser única.", "warning")
        # Validar horario
        if not _validar_horario(form.desde.data, form.hasta.data):
            flash("El horario no es válido", "warning")
            es_valido = False
        # Si no de define el limite de documentos, se deja en cero
        if form.documentos_limite.data:
            documentos_limite = form.documentos_limite.data
        else:
            documentos_limite = 0
        # Si es valido actualizar
        if es_valido:
            cit_servicio.clave = clave
            cit_servicio.descripcion = safe_string(form.descripcion.data, max_len=64)
            cit_servicio.duracion = form.duracion.data
            cit_servicio.documentos_limite = documentos_limite
            cit_servicio.desde = form.desde.data
            cit_servicio.hasta = form.hasta.data
            dias_habilitados = _conversion_dias_habilitados_letra_numero(form.dias_habilitados.data)
            if dias_habilitados == "01234":
                dias_habilitados = ""
            cit_servicio.dias_habilitados = dias_habilitados
            cit_servicio.save()
            bitacora = Bitacora(
                modulo=Modulo.query.filter_by(nombre=MODULO).first(),
                usuario=current_user,
                descripcion=safe_message(f"Editado Servicio: {cit_servicio.descripcion}"),
                url=url_for("cit_servicios.detail", cit_servicio_id=cit_servicio.id),
            )
            bitacora.save()
            flash(bitacora.descripcion, "success")
            return redirect(bitacora.url)
    # Llenar los campos del formulario
    form.cit_categoria_nombre.data = cit_servicio.cit_categoria.nombre
    form.clave.data = cit_servicio.clave
    form.descripcion.data = cit_servicio.descripcion
    form.duracion.data = cit_servicio.duracion
    form.documentos_limite.data = cit_servicio.documentos_limite
    form.desde.data = cit_servicio.desde
    form.hasta.data = cit_servicio.hasta
    form.dias_habilitados.data = _conversion_dias_habilitados_numero_letra(cit_servicio.dias_habilitados)
    # Entregar
    return render_template(
        "cit_servicios/edit.jinja2",
        form=form,
        cit_servicio=cit_servicio,
    )


def _validar_horario(inicio, termino):
    """Validad que el horario no se empalme"""
    if inicio is None and termino is None:
        return True
    if inicio is None:
        inicio = time.fromisoformat("08:30:00")
    if termino is None:
        termino = time.fromisoformat("16:30:00")
    if inicio > termino:
        return False
    return True


def _conversion_dias_habilitados_letra_numero(texto: str):
    """Regresa la conversión de días en letra a número"""
    if texto == "" or texto is None:
        return ""
    # Elaborar resultado de la conversión
    resultado = ""
    if "LUNES" in texto:
        resultado = "0"
    if "MARTES" in texto:
        resultado += "1"
    if "MIERCOLES" in texto:
        resultado += "2"
    if "JUEVES" in texto:
        resultado += "3"
    if "VIERNES" in texto:
        resultado += "4"
    # Entregar
    return resultado


def _conversion_dias_habilitados_numero_letra(texto: str):
    """Regresa la conversión de días de número a letra"""
    if texto == "" or texto is None:
        return "LUNES, MARTES, MIERCOLES, JUEVES, VIERNES, "
    # Elaborar resultado de la conversión
    resultado = ""
    if "0" in texto:
        resultado = "LUNES, "
    if "1" in texto:
        resultado += "MARTES, "
    if "2" in texto:
        resultado += "MIERCOLES, "
    if "3" in texto:
        resultado += "JUEVES, "
    if "4" in texto:
        resultado += "VIERNES, "
    # Entregar
    return resultado


def _conversion_dias_habilitados_numero_letra_abreviada(texto: str):
    """Regresa la conversión de días de número a letra abreviadas"""
    # Elaborar resultado de la conversión
    resultado = ""
    if "0" in texto:
        resultado = "Lun, "
    if "1" in texto:
        resultado += "Mar, "
    if "2" in texto:
        resultado += "Mie, "
    if "3" in texto:
        resultado += "Jue, "
    if "4" in texto:
        resultado += "Vie, "
    # Entregar
    return resultado[:-2]


@cit_servicios.route("/cit_servicios/eliminar/<int:cit_servicio_id>")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def delete(cit_servicio_id):
    """Eliminar Servicio"""
    cit_servicio = CitServicio.query.get_or_404(cit_servicio_id)
    if cit_servicio.estatus == "A":
        cit_servicio.delete()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Eliminado Servi {cit_servicio.descripcion}"),
            url=url_for("cit_servicios.detail", cit_servicio_id=cit_servicio.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("cit_servicios.detail", cit_servicio_id=cit_servicio.id))


@cit_servicios.route("/cit_servicios/recuperar/<int:cit_servicio_id>")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def recover(cit_servicio_id):
    """Recuperar Servicio"""
    cit_servicio = CitServicio.query.get_or_404(cit_servicio_id)
    if cit_servicio.estatus == "B":
        cit_servicio.recover()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Recuperado Servicio {cit_servicio.descripcion}"),
            url=url_for("cit_servicios.detail", cit_servicio_id=cit_servicio.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("cit_servicios.detail", cit_servicio_id=cit_servicio.id))
