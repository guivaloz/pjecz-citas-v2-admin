"""
Usuarios-Oficinas, vistas
"""

import json

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from citas_admin.blueprints.bitacoras.models import Bitacora
from citas_admin.blueprints.modulos.models import Modulo
from citas_admin.blueprints.oficinas.models import Oficina
from citas_admin.blueprints.permisos.models import Permiso
from citas_admin.blueprints.usuarios.decorators import permission_required
from citas_admin.blueprints.usuarios.models import Usuario
from citas_admin.blueprints.usuarios_oficinas.forms import UsuarioOficinaWithOficinaForm, UsuarioOficinaWithUsuarioForm
from citas_admin.blueprints.usuarios_oficinas.models import UsuarioOficina
from lib.datatables import get_datatable_parameters, output_datatable_json
from lib.safe_string import safe_message, safe_string

MODULO = "USUARIOS OFICINAS"

usuarios_oficinas = Blueprint("usuarios_oficinas", __name__, template_folder="templates")


@usuarios_oficinas.before_request
@login_required
@permission_required(MODULO, Permiso.VER)
def before_request():
    """Permiso por defecto"""


@usuarios_oficinas.route("/usuarios_oficinas/datatable_json", methods=["GET", "POST"])
def datatable_json():
    """DataTable JSON para listado de Usuarios-Oficinas"""
    # Tomar parámetros de Datatables
    draw, start, rows_per_page = get_datatable_parameters()
    # Consultar
    consulta = UsuarioOficina.query
    # Primero filtrar por columnas propias
    if "estatus" in request.form:
        consulta = consulta.filter_by(estatus=request.form["estatus"])
    else:
        consulta = consulta.filter_by(estatus="A")
    if "oficina_id" in request.form:
        consulta = consulta.filter_by(oficina_id=request.form["oficina_id"])
    if "usuario_id" in request.form:
        consulta = consulta.filter_by(usuario_id=request.form["usuario_id"])
    # Ordenar y paginar
    registros = consulta.order_by(UsuarioOficina.id).offset(start).limit(rows_per_page).all()
    total = consulta.count()
    # Elaborar datos para DataTable
    data = []
    for resultado in registros:
        data.append(
            {
                "detalle": {
                    "id": resultado.id,
                    "url": url_for("usuarios_oficinas.detail", usuario_oficina_id=resultado.id),
                },
                "usuario": {
                    "email": resultado.usuario.email,
                    "url": (
                        url_for("usuarios.detail", usuario_id=resultado.usuario_id) if current_user.can_view("USUARIOS") else ""
                    ),
                },
                "usuario_nombre": resultado.usuario.nombre,
                "oficina": {
                    "clave": resultado.oficina.clave,
                    "url": (
                        url_for("oficinas.detail", oficina_id=resultado.oficina_id) if current_user.can_view("OFICINAS") else ""
                    ),
                },
                "oficina_descripcion_corta": resultado.oficina.descripcion_corta,
            }
        )
    # Entregar JSON
    return output_datatable_json(draw, total, data)


@usuarios_oficinas.route("/usuarios_oficinas")
def list_active():
    """Listado de Usuarios-Oficinas activos"""
    return render_template(
        "usuarios_oficinas/list.jinja2",
        filtros=json.dumps({"estatus": "A"}),
        titulo="Usuarios-Oficinas",
        estatus="A",
    )


@usuarios_oficinas.route("/usuarios_oficinas/inactivos")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def list_inactive():
    """Listado de Usuarios-Oficinas inactivos"""
    return render_template(
        "usuarios_oficinas/list.jinja2",
        filtros=json.dumps({"estatus": "B"}),
        titulo="Usuarios-Oficinas inactivos",
        estatus="B",
    )


@usuarios_oficinas.route("/usuarios_oficinas/<int:usuario_oficina_id>")
def detail(usuario_oficina_id):
    """Detalle de un Usuario-Oficina"""
    usuario_oficina = UsuarioOficina.query.get_or_404(usuario_oficina_id)
    return render_template("usuarios_oficinas/detail.jinja2", usuario_oficina=usuario_oficina)


@usuarios_oficinas.route("/usuarios_oficinas/nuevo_con_oficina/<int:oficina_id>", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.CREAR)
def new_with_oficina(oficina_id):
    """Nuevo Usuario-Oficina con Oficina"""
    oficina = Oficina.query.get_or_404(oficina_id)
    form = UsuarioOficinaWithOficinaForm()
    if form.validate_on_submit():
        usuario = Usuario.query.get_or_404(form.usuario.data)
        descripcion = safe_string(f"usuario {usuario.email} en oficina {oficina.clave}", save_enie=True)
        puede_existir = (
            UsuarioOficina.query.filter(UsuarioOficina.oficina_id == oficina.id)
            .filter(UsuarioOficina.usuario_id == usuario.id)
            .first()
        )
        if puede_existir and puede_existir.estatus == "A":
            flash(f"Ya existe la combinación de {descripcion}", "warning")
            return redirect(url_for("usuarios_oficinas.detail", usuario_oficina_id=puede_existir.id))
        if puede_existir:
            puede_existir.recover()
            bitacora = Bitacora(
                modulo=Modulo.query.filter_by(nombre=MODULO).first(),
                usuario=current_user,
                descripcion=safe_message(f"Recuperado Usuario-Oficina con {descripcion}"),
                url=url_for("usuarios_oficinas.detail", usuario_oficina_id=puede_existir.id),
            )
            bitacora.save()
            flash(bitacora.descripcion, "success")
            return redirect(url_for("usuarios_oficinas.detail", usuario_oficina_id=puede_existir.id))
        usuario_oficina = UsuarioOficina(
            oficina_id=oficina.id,
            usuario_id=usuario.id,
            descripcion=descripcion,
        )
        usuario_oficina.save()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Nuevo Usuario-Oficina {descripcion}"),
            url=url_for("usuarios_oficinas.detail", usuario_oficina_id=usuario_oficina.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
        return redirect(url_for("oficinas.detail", oficina_id=oficina.id))
    form.oficina.data = f"{oficina.clave} - {oficina.descripcion_corta}"  # Read only string field
    return render_template(
        "usuarios_oficinas/new_with_oficina.jinja2",
        form=form,
        titulo=f"Agregar un usuario a la oficina {oficina.clave}",
        oficina=oficina,
    )


@usuarios_oficinas.route("/usuarios_oficinas/nuevo_con_usuario/<int:usuario_id>", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.CREAR)
def new_with_usuario(usuario_id):
    """Nuevo Usuario-Oficina con Usuario"""
    usuario = Usuario.query.get_or_404(usuario_id)
    form = UsuarioOficinaWithUsuarioForm()
    if form.validate_on_submit():
        oficina = Oficina.query.get_or_404(form.oficina.data)
        descripcion = safe_string(f"usuario {usuario.email} en oficina {oficina.clave}", save_enie=True)
        puede_existir = (
            UsuarioOficina.query.filter(UsuarioOficina.oficina_id == oficina.id)
            .filter(UsuarioOficina.usuario_id == usuario.id)
            .first()
        )
        if puede_existir and puede_existir.estatus == "A":
            flash(f"Ya existe la combinación de {descripcion}", "warning")
            return redirect(url_for("usuarios_oficinas.detail", usuario_oficina_id=puede_existir.id))
        if puede_existir:
            puede_existir.recover()
            bitacora = Bitacora(
                modulo=Modulo.query.filter_by(nombre=MODULO).first(),
                usuario=current_user,
                descripcion=safe_message(f"Recuperado Usuario-Oficina con {descripcion}"),
                url=url_for("usuarios_oficinas.detail", usuario_oficina_id=puede_existir.id),
            )
            bitacora.save()
            flash(bitacora.descripcion, "success")
            return redirect(url_for("usuarios_oficinas.detail", usuario_oficina_id=puede_existir.id))
        usuario_oficina = UsuarioOficina(
            oficina_id=oficina.id,
            usuario_id=usuario.id,
            descripcion=descripcion,
        )
        usuario_oficina.save()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Nuevo Usuario-Oficina {descripcion}"),
            url=url_for("usuarios_oficinas.detail", usuario_oficina_id=usuario_oficina.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
        return redirect(url_for("usuarios.detail", usuario_id=usuario.id))
    form.usuario_email.data = usuario.email  # Read only string field
    form.usuario_nombre.data = usuario.nombre  # Read only string field
    return render_template(
        "usuarios_oficinas/new_with_usuario.jinja2",
        form=form,
        titulo=f"Agregar {usuario.email} a una oficina",
        usuario=usuario,
    )


@usuarios_oficinas.route("/usuarios_oficinas/eliminar/<int:usuario_oficina_id>")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def delete(usuario_oficina_id):
    """Eliminar Usuario-Oficina"""
    usuario_oficina = UsuarioOficina.query.get_or_404(usuario_oficina_id)
    if usuario_oficina.estatus == "A":
        usuario_oficina.delete()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Eliminado Usuario-Oficina {usuario_oficina.descripcion}"),
            url=url_for("usuarios_oficinas.detail", usuario_oficina_id=usuario_oficina.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("usuarios_oficinas.detail", usuario_oficina_id=usuario_oficina.id))


@usuarios_oficinas.route("/usuarios_oficinas/recuperar/<int:usuario_oficina_id>")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def recover(usuario_oficina_id):
    """Recuperar Usuario-Oficina"""
    usuario_oficina = UsuarioOficina.query.get_or_404(usuario_oficina_id)
    if usuario_oficina.estatus == "B":
        usuario_oficina.recover()
        bitacora = Bitacora(
            modulo=Modulo.query.filter_by(nombre=MODULO).first(),
            usuario=current_user,
            descripcion=safe_message(f"Recuperado Usuario-Oficina {usuario_oficina.descripcion}"),
            url=url_for("usuarios_oficinas.detail", usuario_oficina_id=usuario_oficina.id),
        )
        bitacora.save()
        flash(bitacora.descripcion, "success")
    return redirect(url_for("usuarios_oficinas.detail", usuario_oficina_id=usuario_oficina.id))
