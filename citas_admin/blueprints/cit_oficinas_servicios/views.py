"""
Cit Oficinas-Servicios, vistas
"""
import json
from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from lib.datatables import get_datatable_parameters, output_datatable_json
from lib.safe_string import safe_message, safe_string

from citas_admin.blueprints.bitacoras.models import Bitacora
from citas_admin.blueprints.cit_categorias.models import CitCategoria
from citas_admin.blueprints.cit_oficinas_servicios.models import CitOficinaServicio
from citas_admin.blueprints.cit_oficinas_servicios.forms import CitOficinaServicioFormWithOficina, CitOficinaServicioFormWithCitServicio, CitOficinaServicioFormWithCitCategoria, CitOficinaServicioFormWithDistrito
from citas_admin.blueprints.cit_servicios.models import CitServicio
from citas_admin.blueprints.distritos.models import Distrito
from citas_admin.blueprints.modulos.models import Modulo
from citas_admin.blueprints.oficinas.models import Oficina
from citas_admin.blueprints.permisos.models import Permiso
from citas_admin.blueprints.usuarios.decorators import permission_required

MODULO = "CIT OFICINAS SERVICIOS"

cit_oficinas_servicios = Blueprint("cit_oficinas_servicios", __name__, template_folder="templates")


@cit_oficinas_servicios.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""


@cit_oficinas_servicios.route("/cit_oficinas_servicios/datatable_json", methods=["GET", "POST"])
def datatable_json():
    """DataTable JSON para listado de Oficinas-Servicios"""
    # Tomar parámetros de Datatables
    draw, start, rows_per_page = get_datatable_parameters()
    # Consultar
    consulta = CitOficinaServicio.query
    if "estatus" in request.form:
        consulta = consulta.filter_by(estatus=request.form["estatus"])
    else:
        consulta = consulta.filter_by(estatus="A")
    if "oficina_id" in request.form:
        consulta = consulta.filter_by(oficina_id=request.form["oficina_id"])
    if "cit_servicio_id" in request.form:
        consulta = consulta.filter_by(cit_servicio_id=request.form["cit_servicio_id"])
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
                    "url": url_for("oficinas.detail", oficina_id=resultado.oficina_id),
                },
                "oficina_descripcion_corta": resultado.oficina.descripcion_corta,
                "oficina_es_jurisdiccional": resultado.oficina.es_jurisdiccional,
                "oficina_puede_agendar_citas": resultado.oficina.puede_agendar_citas,
                "oficina_distrito_nombre_corto": resultado.oficina.distrito.nombre_corto,
                "cit_servicio": {
                    "clave": resultado.cit_servicio.clave,
                    "url": url_for("cit_servicios.detail", cit_servicio_id=resultado.cit_servicio_id),
                },
                "cit_servicio_descripcion": resultado.cit_servicio.descripcion,
                "cit_servicio_duracion": resultado.cit_servicio.duracion.strftime("%H:%M"),
                "cit_servicio_documentos_limite": resultado.cit_servicio.documentos_limite,
                "cit_servicio_categoria_nombre": resultado.cit_servicio.cit_categoria.nombre,
            }
        )
    # Entregar JSON
    return output_datatable_json(draw, total, data)


@cit_oficinas_servicios.route("/cit_oficinas_servicios")
def list_active():
    """Listado de Oficinas-Servicios activos"""
    return render_template(
        "cit_oficinas_servicios/list.jinja2",
        filtros=json.dumps({"estatus": "A"}),
        titulo="Oficinas-Servicios",
        estatus="A",
    )


@cit_oficinas_servicios.route("/cit_oficinas_servicios/inactivos")
@permission_required(MODULO, Permiso.MODIFICAR)
def list_inactive():
    """Listado de Oficinas-Servicios inactivos"""
    return render_template(
        "cit_oficinas_servicios/list.jinja2",
        filtros=json.dumps({"estatus": "B"}),
        titulo="Oficinas-Servicios inactivos",
        estatus="B",
    )


@cit_oficinas_servicios.route("/cit_oficinas_servicios/<int:cit_oficina_servicio_id>")
def detail(cit_oficina_servicio_id):
    """Detalle de un Oficina-Servicio"""
    cit_oficina_servicio = CitOficinaServicio.query.get_or_404(cit_oficina_servicio_id)
    return render_template("cit_oficinas_servicios/detail.jinja2", cit_oficina_servicio=cit_oficina_servicio)


@cit_oficinas_servicios.route("/cit_oficinas_servicios/nuevo_con_oficina/<int:oficina_id>", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.CREAR)
def new_with_oficina(oficina_id):
    """Nuevo Oficina-Servicio con Oficina"""
    oficina = Oficina.query.get_or_404(oficina_id)
    form = CitOficinaServicioFormWithOficina()
    if form.validate_on_submit():
        cit_servicio = form.cit_servicio.data
        descripcion = safe_string(f"{oficina.clave} con {cit_servicio.clave}")
        cit_oficina_servicio_existente = CitOficinaServicio.query.filter(CitOficinaServicio.oficina == oficina).filter(CitOficinaServicio.cit_servicio == cit_servicio).first()
        if cit_oficina_servicio_existente is not None:
            flash(f"CONFLICTO: Ya existe {descripcion}. Si esta eliminado, recupere.", "warning")
            return redirect(url_for("cit_oficinas_servicios.detail", cit_oficina_servicio_id=cit_oficina_servicio_existente.id))
        cit_oficina_servicio = CitOficinaServicio(
            oficina=oficina,
            cit_servicio=cit_servicio,
            descripcion=descripcion,
        )
        cit_oficina_servicio.save()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Nuevo Oficina-Servicio {descripcion}"),
            url=url_for("cit_oficinas_servicios.detail", cit_oficina_servicio_id=cit_oficina_servicio.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
        return redirect(bitacora.url)
    form.oficina.data = oficina.compuesto  # Read only
    return render_template(
        "cit_oficinas_servicios/new_with_oficina.jinja2",
        form=form,
        oficina=oficina,
    )


@cit_oficinas_servicios.route("/cit_oficinas_servicios/nuevo_con_cit_servicio/<int:cit_servicio_id>", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.CREAR)
def new_with_cit_servicio(cit_servicio_id):
    """Nuevo Oficina-Servicio con Servicio"""
    cit_servicio = CitServicio.query.get_or_404(cit_servicio_id)
    form = CitOficinaServicioFormWithCitServicio()
    if form.validate_on_submit():
        oficina = form.oficina.data
        descripcion = safe_string(f"{oficina.clave} con {cit_servicio.clave}")
        cit_oficina_servicio_existente = CitOficinaServicio.query.filter(CitOficinaServicio.oficina == oficina).filter(CitOficinaServicio.cit_servicio == cit_servicio).first()
        if cit_oficina_servicio_existente is not None:
            flash(f"CONFLICTO: Ya existe {descripcion}. Si esta eliminado, recupere.", "warning")
            return redirect(url_for("cit_oficinas_servicios.detail", cit_oficina_servicio_id=cit_oficina_servicio_existente.id))
        cit_oficina_servicio = CitOficinaServicio(
            oficina=oficina,
            cit_servicio=cit_servicio,
            descripcion=descripcion,
        )
        cit_oficina_servicio.save()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Nuevo Oficina-Servicio {descripcion}"),
            url=url_for("cit_oficinas_servicios.detail", cit_oficina_servicio_id=cit_oficina_servicio.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
        return redirect(bitacora.url)
    form.cit_servicio.data = cit_servicio.compuesto  # Read only
    return render_template(
        "cit_oficinas_servicios/new_with_cit_servicio.jinja2",
        form=form,
        cit_servicio=cit_servicio,
    )


@cit_oficinas_servicios.route("/cit_oficinas_servicios/asignar_cit_categoria_a_distrito/<int:distrito_id>", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.CREAR)
def add_cit_categoria_to_distrito(distrito_id):
    """Asignar servicios de una categoria a todas las oficinas de un distrito"""
    distrito = Distrito.query.get_or_404(distrito_id)
    form = CitOficinaServicioFormWithDistrito()
    if form.validate_on_submit():
        cit_categoria = form.cit_categoria.data
        current_app.task_queue.enqueue(
            "citas_admin.blueprints.cit_oficinas_servicios.tasks.asignar_a_cit_categoria_con_distrito",
            cit_categoria_id=cit_categoria.id,
            distrito_id=distrito.id,
        )
        flash(f"Tarea en el fondo lanzada: Asignar servicios de {cit_categoria.nombre} a todas las oficinas de {distrito.nombre}", "success")
        return redirect(url_for("distritos.detail", distrito_id=distrito.id))
    form.distrito.data = distrito.nombre  # Read only
    return render_template("cit_oficinas_servicios/add_cit_categoria_to_distrito.jinja2", form=form, distrito=distrito)


@cit_oficinas_servicios.route("/cit_oficinas_servicios/asignar_distrito_a_cit_categoria/<int:cit_categoria_id>", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.CREAR)
def add_distrito_to_cit_categoria(cit_categoria_id):
    """Asignar a todas las oficinas de un distrito los servicios de una categoria"""
    cit_categoria = CitCategoria.query.get_or_404(cit_categoria_id)
    form = CitOficinaServicioFormWithCitCategoria()
    if form.validate_on_submit():
        distrito = form.distrito.data
        current_app.task_queue.enqueue(
            "citas_admin.blueprints.cit_oficinas_servicios.tasks.asignar_a_cit_categoria_con_distrito",
            cit_categoria_id=cit_categoria.id,
            distrito_id=distrito.id,
        )
        flash(f"Tarea en el fondo lanzada: Asignar a todas las oficinas de {distrito.nombre} los servicios de {cit_categoria.nombre}", "success")
        return redirect(url_for("cit_categorias.detail", cit_categoria_id=cit_categoria.id))
    form.cit_categoria.data = cit_categoria.nombre  # Read only
    return render_template("cit_oficinas_servicios/add_distrito_to_cit_categoria.jinja2", form=form, cit_categoria=cit_categoria)


@cit_oficinas_servicios.route("/cit_oficinas_servicios/eliminar/<int:cit_oficina_servicio_id>")
@permission_required(MODULO, Permiso.MODIFICAR)
def delete(cit_oficina_servicio_id):
    """Eliminar Oficina-Servicio"""
    cit_oficina_servicio = CitOficinaServicio.query.get_or_404(cit_oficina_servicio_id)
    if cit_oficina_servicio.estatus == "A":
        cit_oficina_servicio.delete()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Eliminado Oficina-Servicio {cit_oficina_servicio.descripcion}"),
            url=url_for("cit_oficinas_servicios.detail", cit_oficina_servicio_id=cit_oficina_servicio.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("cit_oficinas_servicios.detail", cit_oficina_servicio_id=cit_oficina_servicio.id))


@cit_oficinas_servicios.route("/cit_oficinas_servicios/recuperar/<int:cit_oficina_servicio_id>")
@permission_required(MODULO, Permiso.MODIFICAR)
def recover(cit_oficina_servicio_id):
    """Recuperar Oficina-Servicio"""
    cit_oficina_servicio = CitOficinaServicio.query.get_or_404(cit_oficina_servicio_id)
    if cit_oficina_servicio.estatus == "B":
        cit_oficina_servicio.recover()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Recuperado Oficina-Servicio {cit_oficina_servicio.descripcion}"),
            url=url_for("cit_oficinas_servicios.detail", cit_oficina_servicio_id=cit_oficina_servicio.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("cit_oficinas_servicios.detail", cit_oficina_servicio_id=cit_oficina_servicio.id))
