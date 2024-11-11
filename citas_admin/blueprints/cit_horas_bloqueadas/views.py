"""
Cit Horas Bloqueadas, vistas
"""

import json

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from citas_admin.blueprints.bitacoras.models import Bitacora
from citas_admin.blueprints.cit_horas_bloqueadas.forms import CitHoraBloqueadaAdminForm, CitHoraBloqueadaForm
from citas_admin.blueprints.cit_horas_bloqueadas.models import CitHoraBloqueada
from citas_admin.blueprints.modulos.models import Modulo
from citas_admin.blueprints.oficinas.models import Oficina
from citas_admin.blueprints.permisos.models import Permiso
from citas_admin.blueprints.usuarios.decorators import permission_required
from lib.datatables import get_datatable_parameters, output_datatable_json
from lib.safe_string import safe_clave, safe_message, safe_string

MODULO = "CIT HORAS BLOQUEADAS"

cit_horas_bloqueadas = Blueprint("cit_horas_bloqueadas", __name__, template_folder="templates")


@cit_horas_bloqueadas.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""


@cit_horas_bloqueadas.route("/cit_horas_bloqueadas/datatable_json", methods=["GET", "POST"])
def datatable_json():
    """DataTable JSON para listado de Cit Horas Bloqueadas"""
    # Tomar parámetros de Datatables
    draw, start, rows_per_page = get_datatable_parameters()
    # Consultar
    consulta = CitHoraBloqueada.query
    # Primero filtrar por columnas propias
    if "estatus" in request.form:
        consulta = consulta.filter(CitHoraBloqueada.estatus == request.form["estatus"])
    else:
        consulta = consulta.filter(CitHoraBloqueada.estatus == "A")
    if "oficina_id" in request.form:
        try:
            oficina_id = int(request.form["oficina_id"])
            consulta = consulta.filter(CitHoraBloqueada.oficina_id == oficina_id)
        except ValueError:
            pass
    elif "oficina_clave" in request.form:
        oficina_clave = safe_clave(request.form["oficina_clave"])
        if oficina_clave != "":
            consulta = consulta.join(Oficina).filter(Oficina.clave.contains(oficina_clave))
    if "descripcion" in request.form:
        descripcion = safe_string(request.form["descripcion"], save_enie=True)
        if descripcion != "":
            consulta = consulta.filter(CitHoraBloqueada.descripcion.contains(descripcion))
    # Ordenar y paginar
    registros = consulta.order_by(CitHoraBloqueada.id.desc()).offset(start).limit(rows_per_page).all()
    total = consulta.count()
    # Elaborar datos para DataTable
    data = []
    for resultado in registros:
        data.append(
            {
                "detalle": {
                    "fecha": resultado.fecha.strftime("%Y-%m-%d 00:00:00"),
                    "url": url_for("cit_horas_bloqueadas.detail", cit_hora_bloqueada_id=resultado.id),
                },
                "inicio": resultado.inicio.strftime("%H:%M"),
                "termino": resultado.termino.strftime("%H:%M"),
                "descripcion": resultado.descripcion,
            }
        )
    # Entregar JSON
    return output_datatable_json(draw, total, data)


@cit_horas_bloqueadas.route("/cit_horas_bloqueadas/admin_datatable_json", methods=["GET", "POST"])
def admin_datatable_json():
    """DataTable JSON para listado de Cit Horas Bloqueadas"""
    # Tomar parámetros de Datatables
    draw, start, rows_per_page = get_datatable_parameters()
    # Consultar
    consulta = CitHoraBloqueada.query
    # Primero filtrar por columnas propias
    if "estatus" in request.form:
        consulta = consulta.filter(CitHoraBloqueada.estatus == request.form["estatus"])
    else:
        consulta = consulta.filter(CitHoraBloqueada.estatus == "A")
    if "oficina_id" in request.form:
        try:
            oficina_id = int(request.form["oficina_id"])
            consulta = consulta.filter(CitHoraBloqueada.oficina_id == oficina_id)
        except ValueError:
            pass
    elif "oficina_clave" in request.form:
        oficina_clave = safe_clave(request.form["oficina_clave"])
        if oficina_clave != "":
            consulta = consulta.join(Oficina).filter(Oficina.clave.contains(oficina_clave))
    if "descripcion" in request.form:
        descripcion = safe_string(request.form["descripcion"], save_enie=True)
        if descripcion != "":
            consulta = consulta.filter(CitHoraBloqueada.descripcion.contains(descripcion))
    # Ordenar y paginar
    registros = consulta.order_by(CitHoraBloqueada.id.desc()).offset(start).limit(rows_per_page).all()
    total = consulta.count()
    # Elaborar datos para DataTable
    data = []
    for resultado in registros:
        data.append(
            {
                "detalle": {
                    "id": resultado.id,
                    "url": url_for("cit_horas_bloqueadas.detail", cit_hora_bloqueada_id=resultado.id),
                },
                "oficina": {
                    "clave": resultado.oficina.clave,
                    "descripcion": resultado.oficina.descripcion,
                    "url": url_for("oficinas.detail", oficina_id=resultado.oficina_id),
                },
                "fecha": resultado.fecha.strftime("%Y-%m-%d 00:00:00"),
                "inicio": resultado.inicio.strftime("%H:%M"),
                "termino": resultado.termino.strftime("%H:%M"),
                "descripcion": resultado.descripcion,
            }
        )
    # Entregar JSON
    return output_datatable_json(draw, total, data)


@cit_horas_bloqueadas.route("/cit_horas_bloqueadas")
def list_active():
    """Listado de Cit Horas Bloqueadas activas"""
    if current_user.can_admin(MODULO):
        return render_template(
            "cit_horas_bloqueadas/list_admin.jinja2",
            filtros=json.dumps({"estatus": "A"}),
            titulo="Todas las Horas Bloqueadas",
            estatus="A",
        )
    return render_template(
        "cit_horas_bloqueadas/list.jinja2",
        filtros=json.dumps({"estatus": "A"}),
        titulo="Todas las Horas Bloqueadas",
        estatus="A",
    )


@cit_horas_bloqueadas.route("/cit_horas_bloqueadas/inactivos")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def list_inactive():
    """Listado de Cit Horas Bloqueadas inactivas"""
    if current_user.can_admin(MODULO):
        return render_template(
            "cit_horas_bloqueadas/list_admin.jinja2",
            filtros=json.dumps({"estatus": "B"}),
            titulo="Horas Bloqueadas inactivas",
            estatus="B",
        )
    return render_template(
        "cit_horas_bloqueadas/list.jinja2",
        filtros=json.dumps({"estatus": "B"}),
        titulo="Horas Bloqueadas inactivas",
        estatus="B",
    )


@cit_horas_bloqueadas.route("/cit_horas_bloqueadas/<int:cit_hora_bloqueada_id>")
def detail(cit_hora_bloqueada_id):
    """Detalle de un Cit Hora Bloqueada"""
    cit_hora_bloqueada = CitHoraBloqueada.query.get_or_404(cit_hora_bloqueada_id)
    return render_template("cit_horas_bloqueadas/detail.jinja2", cit_hora_bloqueada=cit_hora_bloqueada)


@cit_horas_bloqueadas.route("/cit_horas_bloqueadas/nuevo", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.CREAR)
def new():
    """Nueva Hora Bloqueada"""
    # Si es administrador, puede elegir la oficina
    if current_user.can_admin(MODULO):
        form = CitHoraBloqueadaAdminForm()
        oficina_id = form.oficina.data
    else:
        form = CitHoraBloqueadaForm()
        oficina_id = current_user.oficina_id
    # Si se recibe el formulario
    if form.validate_on_submit():
        es_valido = True
        # Validar que el inicio sea igual o posterior a la apertura de la oficina
        inicio = form.inicio_tiempo.data
        if inicio < current_user.oficina.apertura:
            flash(
                f"El inicio debe ser igual o posterior a la apertura de la oficina {current_user.oficina.apertura}", "warning"
            )
            es_valido = False
        # Validar que el termino sea igual o anterior al cierre de la oficina
        termino = form.termino_tiempo.data
        if termino > current_user.oficina.cierre:
            flash(f"El termino debe ser igual o anterior al cierre de la oficina {current_user.oficina.cierre}", "warning")
            es_valido = False
        # Si el tiempo de inicio es mayor que el tiempo de termino, vamos a intercambiarlos
        if inicio > termino:
            inicio, termino = termino, inicio
        # Si es valido, insertar
        if es_valido:
            cit_hora_bloqueada = CitHoraBloqueada(
                oficina_id=oficina_id,
                fecha=form.fecha.data,
                inicio=inicio,
                termino=termino,
                descripcion=safe_string(form.descripcion.data, save_enie=True),
            )
            cit_hora_bloqueada.save()
            bitacora = Bitacora(
                modulo=Modulo.query.filter_by(nombre=MODULO).first(),
                usuario=current_user,
                descripcion=safe_message(
                    f"Nueva Hora Bloqueada {cit_hora_bloqueada.fecha} de {cit_hora_bloqueada.inicio} a {cit_hora_bloqueada.termino}"
                ),
                url=url_for("cit_horas_bloqueadas.detail", cit_hora_bloqueada_id=cit_hora_bloqueada.id),
            )
            bitacora.save()
            flash(bitacora.descripcion, "success")
            return redirect(bitacora.url)
    # Si es administrador, puede elegir la oficina
    if current_user.can_admin(MODULO):
        # Si viene oficina_id en el URL, se va a consultar
        oficina = None
        if "oficina_id" in request.args:
            try:
                oficina = Oficina.query.get(int(request.args.get("oficina_id")))
            except ValueError:
                pass
        else:
            oficina = Oficina.query.filter_by(clave="ND").first()  # De lo contrario, se va a tomar la oficina 'ND'
        return render_template("cit_horas_bloqueadas/new_admin.jinja2", form=form, oficina=oficina)
    # No es administrador
    form.oficina.data = current_user.oficina.clave + ": " + current_user.oficina.descripcion
    return render_template("cit_horas_bloqueadas/new.jinja2", form=form)


@cit_horas_bloqueadas.route("/cit_horas_bloqueadas/edicion/<int:cit_hora_bloqueada_id>", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.MODIFICAR)
def edit(cit_hora_bloqueada_id):
    """Editar Hora Bloqueada"""
    cit_hora_bloqueada = CitHoraBloqueada.query.get_or_404(cit_hora_bloqueada_id)
    # Si es administrador, puede elegir la oficina
    if current_user.can_admin(MODULO):
        form = CitHoraBloqueadaAdminForm()
    else:
        # No es administrador, si no es de su oficina, se patea con error fordibben
        if cit_hora_bloqueada.oficina_id != current_user.oficina_id:
            abort(403)
        form = CitHoraBloqueadaForm()
    # Si se recibe el formulario
    if form.validate_on_submit():
        # Si es administrador, puede elegir la oficina
        if current_user.can_admin(MODULO):
            oficina_id = form.oficina.data
        else:
            oficina_id = current_user.oficina_id
        es_valido = True
        # Validar que el inicio sea igual o posterior a la apertura de la oficina
        inicio = form.inicio_tiempo.data
        if inicio < current_user.oficina.apertura:
            flash(
                f"El inicio debe ser igual o posterior a la apertura de la oficina {current_user.oficina.apertura}", "warning"
            )
            es_valido = False
        # Validar que el termino sea igual o anterior al cierre de la oficina
        termino = form.termino_tiempo.data
        if termino > current_user.oficina.cierre:
            flash(f"El termino debe ser igual o anterior al cierre de la oficina {current_user.oficina.cierre}", "warning")
            es_valido = False
        # Si el tiempo de inicio es mayor que el tiempo de termino, vamos a intercambiarlos
        if inicio > termino:
            inicio, termino = termino, inicio
        # Si es valido, actualizar
        if es_valido:
            cit_hora_bloqueada.oficina_id = oficina_id
            cit_hora_bloqueada.fecha = form.fecha.data
            cit_hora_bloqueada.inicio = inicio
            cit_hora_bloqueada.termino = termino
            cit_hora_bloqueada.descripcion = safe_string(form.descripcion.data, save_enie=True)
            cit_hora_bloqueada.save()
            bitacora = Bitacora(
                modulo=Modulo.query.filter_by(nombre=MODULO).first(),
                usuario=current_user,
                descripcion=safe_message(
                    f"Editada Hora Bloqueada {cit_hora_bloqueada.fecha} de {cit_hora_bloqueada.inicio} a {cit_hora_bloqueada.termino}"
                ),
                url=url_for("cit_horas_bloqueadas.detail", cit_hora_bloqueada_id=cit_hora_bloqueada.id),
            )
            bitacora.save()
            flash(bitacora.descripcion, "success")
            return redirect(bitacora.url)
    # Cargar datos al formulario
    form.fecha.data = cit_hora_bloqueada.fecha
    form.inicio_tiempo.data = cit_hora_bloqueada.inicio
    form.termino_tiempo.data = cit_hora_bloqueada.termino
    form.descripcion.data = cit_hora_bloqueada.descripcion
    # Si es administrador, puede elegir la oficina
    if current_user.can_admin(MODULO):
        form.oficina.data = cit_hora_bloqueada.oficina_id
        return render_template("cit_horas_bloqueadas/edit_admin.jinja2", form=form, cit_hora_bloqueada=cit_hora_bloqueada)
    # No es administrador
    form.oficina.data = current_user.oficina.clave + ": " + current_user.oficina.descripcion
    return render_template("cit_horas_bloqueadas/edit.jinja2", form=form, cit_hora_bloqueada=cit_hora_bloqueada)


@cit_horas_bloqueadas.route("/cit_horas_bloqueadas/eliminar/<int:cit_hora_bloqueada_id>")
@permission_required(MODULO, Permiso.MODIFICAR)
def delete(cit_hora_bloqueada_id):
    """Eliminar Hora Bloqueada"""
    cit_hora_bloqueada = CitHoraBloqueada.query.get_or_404(cit_hora_bloqueada_id)
    # Si no es administrador o no es su oficina, no puede eliminar
    if not current_user.can_admin(MODULO) or cit_hora_bloqueada.oficina != current_user.oficina:
        flash("No tiene permiso para eliminar esta hora bloqueada", "warning")
        return redirect(url_for("cit_horas_bloqueadas.detail", cit_hora_bloqueada_id=cit_hora_bloqueada.id))
    if cit_hora_bloqueada.estatus == "A":
        cit_hora_bloqueada.delete()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(
                f"Eliminada Hora Bloqueada {cit_hora_bloqueada.fecha} de {cit_hora_bloqueada.inicio} a {cit_hora_bloqueada.termino}"
            ),
            url=url_for("cit_horas_bloqueadas.detail", cit_hora_bloqueada_id=cit_hora_bloqueada.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("cit_horas_bloqueadas.detail", cit_hora_bloqueada_id=cit_hora_bloqueada.id))


@cit_horas_bloqueadas.route("/cit_horas_bloqueadas/recuperar/<int:cit_hora_bloqueada_id>")
@permission_required(MODULO, Permiso.MODIFICAR)
def recover(cit_hora_bloqueada_id):
    """Recuperar Hora Bloqueada"""
    cit_hora_bloqueada = CitHoraBloqueada.query.get_or_404(cit_hora_bloqueada_id)
    # Si no es administrador o no es su oficina, no puede recuperar
    if not current_user.can_admin(MODULO) or cit_hora_bloqueada.oficina != current_user.oficina:
        flash("No tiene permiso para recuperar esta hora bloqueada", "warning")
        return redirect(url_for("cit_horas_bloqueadas.detail", cit_hora_bloqueada_id=cit_hora_bloqueada.id))
    if cit_hora_bloqueada.estatus == "B":
        cit_hora_bloqueada.recover()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(
                f"Recuperada Hora Bloqueada {cit_hora_bloqueada.fecha} de {cit_hora_bloqueada.inicio} a {cit_hora_bloqueada.termino}"
            ),
            url=url_for("cit_horas_bloqueadas.detail", cit_hora_bloqueada_id=cit_hora_bloqueada.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("cit_horas_bloqueadas.detail", cit_hora_bloqueada_id=cit_hora_bloqueada.id))
