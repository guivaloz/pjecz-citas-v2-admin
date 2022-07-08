"""
Cit Citas, vistas
"""
from datetime import datetime, timedelta
import json
from flask import Blueprint, flash, redirect, render_template, request, url_for, abort
from flask_login import current_user, login_required

from dateutil.relativedelta import relativedelta

from lib.datatables import get_datatable_parameters, output_datatable_json
from lib.safe_string import safe_message

from citas_admin.blueprints.bitacoras.models import Bitacora
from citas_admin.blueprints.modulos.models import Modulo
from citas_admin.blueprints.cit_citas.models import CitCita, CitCitaStats
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
            fecha_anterior=fecha_anterior_str,
            fecha_siguiente=fecha_siguiente_str,
        )
    # NO es administrador, entonces se filtra por su propia oficina
    return render_template(
        "cit_citas/list.jinja2",
        filtros=json.dumps({"estatus": "A", "oficina_id": current_user.oficina_id, "fecha": fecha_str}),
        titulo=f"Citas del {fecha.strftime('%Y-%m-%d')} de {current_user.oficina.descripcion_corta}",
        estatus="A",
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
        titulo=f"Citas eliminadas del {fecha.strftime('%Y-%m-%d')} de {current_user.oficina.descripcion_corta}",
        estatus="B",
        fecha_anterior=fecha_anterior_str,
        fecha_siguiente=fecha_siguiente_str,
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


@cit_citas.route("/cit_citas/estadisticas")
@permission_required(MODULO, Permiso.ADMINISTRAR)
def stats():
    """Estadísticas del módulo citas"""

    return render_template(
        "cit_citas/stats.jinja2",
        titulo="Estadísticas de Citas",
    )


@cit_citas.route("/cit_citas/estadisticas/data/<string:rango>", methods=["POST", "GET"])
@permission_required(MODULO, Permiso.ADMINISTRAR)
def stats_json(rango):
    """Entrega los datos para gráficas"""

    if rango == "HOY":
        etiquetas, datos, subtitulo = _obtener_labels_datos_stats("HOY")
        titulo = f"Día de hoy: {datetime.now().strftime('%d %B %Y')}"
        label = "Citas por Hora"
    elif rango == "SEMANA":
        etiquetas, datos, subtitulo = _obtener_labels_datos_stats("SEMANA")
        # Crea el titulo: númDía del Lunes, númDía del Viernes de la semana actual
        lunes, viernes =_calcular_lunes_viernes_fecha(datetime.now())
        titulo = f"Semana Actual: {lunes.day}-{viernes.day} {datetime.now().strftime('%B %Y')}"
        label = "Citas por Día"
    elif rango == "MES":
        etiquetas, datos, subtitulo = _obtener_labels_datos_stats("MES")
        titulo = f"Mes Actual: {datetime.now().strftime('%B %Y')}"
        label = "Citas por Día"
    elif rango == "CINCO_MESES":
        etiquetas, datos, subtitulo = _obtener_labels_datos_stats("CINCO_MESES")
        hoy = datetime.now()
        dos_meses_atras = hoy - relativedelta(months=3)
        dos_meses_adelante = hoy + relativedelta(months=1)
        titulo = f"Cinco Meses: {dos_meses_atras.strftime('%B')}-{dos_meses_adelante.strftime('%B')} {hoy.year}"
        label = "Citas por Meses"
    elif rango == "ANO":
        etiquetas, datos, subtitulo = _obtener_labels_datos_stats("ANO")
        titulo = f"Año Actual: {datetime.now().year}"
        label = "Citas por Mes"

    respuesta = {
        "titulo": titulo,
        "subtitulo": subtitulo,
        "label": label,
        "etiquetas": etiquetas,
        "datos": datos,
    }
    # Entregar JSON
    return respuesta


def _obtener_labels_datos_stats(stat_name):
    """Extrae las etiquetas y datos de la estadística indicada"""
    results = CitCitaStats.query.filter(CitCitaStats.estatus == 'A').filter(CitCitaStats.tipo == stat_name).order_by(CitCitaStats.id).all()
    etiquetas = []
    datos = []
    ultima_actualizacion = None
    for result in results:
        etiquetas.append(result.etiqueta)
        datos.append(result.dato)
    if len(results) > 0:
        ultima_actualizacion = results[len(results) - 1].modificado.strftime("Reporte Generado: %Y/%m/%d a las %H:%M")
    return etiquetas, datos, ultima_actualizacion


@cit_citas.route("/cit_citas/estadisticas/actualizar", methods=["GET"])
@permission_required(MODULO, Permiso.ADMINISTRAR)
def actualizar_estadisticas():
    """Actualiza las estadísticas"""

    # Obtiene los nuevos datos de la estadística 'HOY'
    labels, resultados, tipo = _stats_hoy()
    actualizar_estadistica(labels, resultados, tipo)
    # Obtiene los nuevos datos de la estadística 'SEMANA'
    labels, resultados, tipo = _stats_semana()
    actualizar_estadistica(labels, resultados, tipo)
    # Obtiene los nuevos datos de la estadística 'MES'
    labels, resultados, tipo = _stats_mes()
    actualizar_estadistica(labels, resultados, tipo)
    # Obtiene los nuevos datos de la estadística 'CINCO_MESES'
    labels, resultados, tipo = _stats_cinco_meses()
    actualizar_estadistica(labels, resultados, tipo)
    # Obtiene los nuevos datos de la estadística 'ANO'
    labels, resultados, tipo = _stats_ano()
    actualizar_estadistica(labels, resultados, tipo)

    flash("Actualización de los datos estadísticos de citas", "success")
    return redirect("/cit_citas/estadisticas")


def actualizar_estadistica(labels, datos, tipo):
    """Actualiza los datos de una estadística"""
    for label in labels:
        # busca el registro de ese dato, para actualizarlo sino para crearlo
        stat_result = CitCitaStats.query.filter(CitCitaStats.etiqueta == label).filter(CitCitaStats.tipo == tipo).first()
        if stat_result:
            stat_result.dato = datos[label]
            # Si el dato no cambiaba, seguía siendo el mismo no hacía la actualización de la hora. Ahora lo forzamos.
            stat_result.modificado = datetime.now()
            stat_result.save()      
        else:
            CitCitaStats(
                etiqueta=label,
                dato=datos[label],
                tipo=tipo,
            ).save()


def _calcular_lunes_viernes_fecha(fecha:datetime):
    """Calcula la fecha para el Lunes y Viernes con la fecha dada"""
    lunes = None
    viernes = None
    # Calculamos el Viernes más próximo
    dia = fecha
    for i in range(7):
        if dia.weekday() == 4:
            viernes = dia.date()
            break
        dia = fecha + timedelta(days=i)

    # Calculamos el Lunes más próximo
    dia = fecha
    for i in range(7):
        if dia.weekday() == 0:
            lunes = dia.date()
            break
        dia = fecha - timedelta(days=i)

    return lunes, viernes


def _calcular_dias_mes(fecha:datetime):
    """Regresa el número de días en un mes dado"""
    numero_dias = (fecha.replace(month = fecha.month % 12+1, day=1) - timedelta(days=1)).day
    return numero_dias


def _stats_hoy():
    """Generador de la estadística HOY, citas por hora"""
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    fecha_hora_inicio = None
    fecha_hora_fin = None
    resultados = {}
    labels = ["8:00", "9:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00", "17:00"] # Tiene un elemento de más, para formar los rangos de búsqueda
    for i in range(len(labels)-1):
        fecha_hora_inicio = fecha_hoy + " " + labels[i]
        fecha_hora_inicio = datetime.strptime(fecha_hora_inicio, "%Y-%m-%d %H:%M")
        fecha_hora_fin = fecha_hoy + " " + labels[i+1]
        fecha_hora_fin = datetime.strptime(fecha_hora_fin, "%Y-%m-%d %H:%M")
        # La regla es: Cita que comienza a cierta hora y termina antes del comienzo del otro horario
        conteo = CitCita.query.filter(CitCita.inicio >= fecha_hora_inicio).filter(CitCita.inicio < fecha_hora_fin).count()
        resultados[labels[i]] = conteo
    # Quita de las etiquetas el último elemento, que solo se utiliza para hacer los rangos de búsqueda
    labels.pop()
    return labels, resultados, 'HOY'


def _stats_semana():
    """Generador de la estadística SEMANA, citas por día de la semana"""
    lunes, _ =_calcular_lunes_viernes_fecha(datetime.now())
    dia_inicio = lunes
    dia_fin = lunes + timedelta(days=1)
    resultados = {}
    labels = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"]
    for i in range(len(labels)):
        conteo = CitCita.query.filter(CitCita.inicio >= dia_inicio).filter(CitCita.inicio < dia_fin).count()
        resultados[labels[i]] = conteo
        dia_inicio = dia_inicio + timedelta(days=1)
        dia_fin = dia_fin + timedelta(days=1)
    return labels, resultados, 'SEMANA'


def _stats_mes():
    """Generador de la estadística MES, citas por día del mes"""
    dia_ini = datetime.now().date().replace(day=1)
    dia_fin = _calcular_dias_mes(dia_ini)
    dia = dia_ini
    resultados = {}
    labels = []
    for i in range(1, 32):
        if i <= dia_fin:
            labels.append(str(i))
            conteo = CitCita.query.filter(CitCita.inicio >= dia).filter(CitCita.inicio < dia + timedelta(days=1)).count()
            resultados[str(i)] = conteo
            dia = dia + timedelta(days=1)

            if i >= 28:
                registro = CitCitaStats.query.filter(CitCitaStats.etiqueta == str(i)).filter(CitCitaStats.tipo == 'MES').first()
                if registro:
                    registro.estatus = 'A'
                    registro.save()
        else:
            # borra los regitros no utilizados
            registro = CitCitaStats.query.filter(CitCitaStats.etiqueta == str(i)).filter(CitCitaStats.tipo == 'MES').first()
            if registro:
                registro.delete()

    return labels, resultados, 'MES'


def _stats_cinco_meses():
    """Generador de la estadística SEIS_MESES, citas por mes"""
    mes_fin = datetime.now().date().replace(day=1) + relativedelta(months=2)
    mes_ini = datetime.now().date().replace(day=1) - relativedelta(months=2)
    mes = datetime.now().date().replace(day=1, month=1)
    resultados = {}
    labels = []
    label = ''
    for i in range(1, 13):
        label = mes.strftime('%B')
        if i >= mes_ini.month and i <= mes_fin.month:
            labels.append(label)
            conteo = CitCita.query.filter(CitCita.inicio >= mes).filter(CitCita.inicio < mes + relativedelta(months=1)).count()
            resultados[label] = conteo

            registro = CitCitaStats.query.filter(CitCitaStats.etiqueta == label).filter(CitCitaStats.tipo == 'CINCO_MESES').first()
            if registro:
                registro.estatus = 'A'
                registro.save()
        else:
            # borra los regitros no utilizados
            registro = CitCitaStats.query.filter(CitCitaStats.etiqueta == label).filter(CitCitaStats.tipo == 'CINCO_MESES').first()
            if registro:
                registro.delete()
        mes = mes + relativedelta(months=1)

    return labels, resultados, 'CINCO_MESES'


def _stats_ano():
    """Generador de la estadística ANO, citas por mes"""
    mes_ini = datetime.now().date().replace(day=1, month=1)
    mes = mes_ini
    resultados = {}
    labels = []
    for i in range(13):
        label = mes.strftime('%B')
        labels.append(label)
        conteo = CitCita.query.filter(CitCita.inicio >= mes).filter(CitCita.inicio < mes + relativedelta(months=1)).count()
        resultados[label] = conteo
        mes = mes + relativedelta(months=1)
    return labels, resultados, 'ANO'