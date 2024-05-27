"""
Usuarios-Oficinas, vistas
"""

import json
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from lib.datatables import get_datatable_parameters, output_datatable_json
from lib.safe_string import safe_message

from citas_admin.blueprints.bitacoras.models import Bitacora
from citas_admin.blueprints.modulos.models import Modulo
from citas_admin.blueprints.permisos.models import Permiso
from citas_admin.blueprints.usuarios.decorators import permission_required
from citas_admin.blueprints.usuarios.models import Usuario
from citas_admin.blueprints.usuarios_oficinas.models import UsuarioOficina
from citas_admin.blueprints.usuarios_oficinas.forms import UsuarioOficinaWithUsuarioForm, UsuarioOficinaWithOficinaForm

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
    # Luego filtrar por columnas de otras tablas
    # if "persona_rfc" in request.form:
    #     consulta = consulta.join(Persona)
    #     consulta = consulta.filter(Persona.rfc.contains(safe_rfc(request.form["persona_rfc"], search_fragment=True)))
    # Ordenar y paginar
    registros = consulta.order_by(UsuarioOficina.id).offset(start).limit(rows_per_page).all()
    total = consulta.count()
    # Elaborar datos para DataTable
    data = []
    for resultado in registros:
        data.append(
            {
                "detalle": {
                    "nombre": resultado.nombre,
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


@usuarios_oficinas.route("/usuarios_oficinas/nuevo_con_usuario/<int:usuario_id>", methods=["GET", "POST"])
@permission_required(MODULO, Permiso.CREAR)
def new_with_usuario(usuario_id):
    """Nuevo Usuario-Oficina con Usuario"""
    usuario = Usuario.query.get_or_404(usuario_id)
    form = UsuarioOficinaWithUsuarioForm()
    if form.validate_on_submit():
        oficina = form.oficina.data
        descripcion = f"{usuario.email} en {oficina.descripcion_corta}"
        puede_existir = (
            UsuarioOficina.query.filter(UsuarioOficina.oficina == oficina).filter(UsuarioOficina.usuario == usuario).first()
        )
        if puede_existir is not None:
            flash(f"CONFLICTO: Ya existe {descripcion}. Si aparece eliminado (oscuro), recupérelo.", "warning")
            return redirect(url_for("usuarios_oficinas.detail", usuario_oficina_id=puede_existir.id))
        usuario_oficina = UsuarioOficina(
            oficina=oficina,
            usuario=usuario,
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
    form.usuario_email.data = usuario.email  # Solo lectura
    form.usuario_nombre.data = usuario.nombre  # Solo lectura
    return render_template(
        "usuarios_oficinas/new_with_usuario.jinja2",
        form=form,
        usuario=usuario,
        titulo=f"Agregar oficina al usuario {usuario.email} para citas inmediatas",
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
