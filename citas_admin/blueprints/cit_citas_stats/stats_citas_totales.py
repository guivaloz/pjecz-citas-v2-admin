"""
Archivo con funciones para actualizar los datos estadísticos
"""

from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta

from citas_admin.blueprints.cit_citas.models import CitCita
from citas_admin.blueprints.cit_citas_stats.models import CitCitaStats


def obtener_stats_json_citas_totales(subcategoria: str):
    """Entrega los datos para gráficas"""

    etiquetas, datos, subtitulo = _obtener_labels_datos_stats(subcategoria)
    if subcategoria == CitCitaStats.SUBCAT_CITAS_TOTALES_HOY:
        titulo = f"Día de hoy: {datetime.now().strftime('%d %B %Y')}"
        label = "Citas por Hora"
    elif subcategoria == CitCitaStats.SUBCAT_CITAS_TOTALES_SEMANA:
        # Crea el titulo: númDía del Lunes, númDía del Viernes de la semana actual
        lunes, viernes = _calcular_lunes_viernes_fecha(datetime.now())
        titulo = f"Semana Actual: {lunes.day}-{viernes.day} {datetime.now().strftime('%B %Y')}"
        label = "Citas por Día"
    elif subcategoria == CitCitaStats.SUBCAT_CITAS_TOTALES_MES:
        titulo = f"Mes Actual: {datetime.now().strftime('%B %Y')}"
        label = "Citas por Día"
    elif subcategoria == CitCitaStats.SUBCAT_CITAS_TOTALES_CINCO_MESES:
        hoy = datetime.now()
        dos_meses_atras = hoy - relativedelta(months=3)
        dos_meses_adelante = hoy + relativedelta(months=1)
        titulo = f"Cinco Meses: {dos_meses_atras.strftime('%B')}-{dos_meses_adelante.strftime('%B')} {hoy.year}"
        label = "Citas por Meses"
    elif subcategoria == CitCitaStats.SUBCAT_CITAS_TOTALES_ANO:
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


def _obtener_labels_datos_stats(subcategoria: str):
    """Extrae las etiquetas y datos de la estadística indicada"""
    results = CitCitaStats.query.filter(CitCitaStats.estatus == "A").filter(CitCitaStats.categoria == CitCitaStats.CAT_CITAS_TOTALES).filter(CitCitaStats.subcategoria == subcategoria).order_by(CitCitaStats.id).all()
    etiquetas = []
    datos = []
    ultima_actualizacion = None
    for result in results:
        etiquetas.append(result.etiqueta)
        datos.append(result.dato)
    if len(results) > 0:
        ultima_actualizacion = results[len(results) - 1].modificado.strftime("Reporte Generado: %Y/%m/%d a las %H:%M")
    return etiquetas, datos, ultima_actualizacion


def actualizar_stats_citas_totales():
    """Actualiza las estadísticas, ejecuta query's de actualización de los registros"""

    # Obtiene los nuevos datos de la estadística 'HOY'
    labels, resultados, subcategoria = _stats_hoy()
    actualizar_estadistica(labels, resultados, subcategoria)
    # Obtiene los nuevos datos de la estadística 'SEMANA'
    labels, resultados, subcategoria = _stats_semana()
    actualizar_estadistica(labels, resultados, subcategoria)
    # Obtiene los nuevos datos de la estadística 'MES'
    labels, resultados, subcategoria = _stats_mes()
    actualizar_estadistica(labels, resultados, subcategoria)
    # Obtiene los nuevos datos de la estadística 'CINCO_MESES'
    labels, resultados, subcategoria = _stats_cinco_meses()
    actualizar_estadistica(labels, resultados, subcategoria)
    # Obtiene los nuevos datos de la estadística 'ANO'
    labels, resultados, subcategoria = _stats_ano()
    actualizar_estadistica(labels, resultados, subcategoria)


def actualizar_estadistica(labels, datos, subcategoria):
    """Actualiza los datos de una estadística"""
    for label in labels:
        # busca el registro de ese dato, para actualizarlo sino para crearlo
        stat_result = CitCitaStats.query
        stat_result = stat_result.filter(CitCitaStats.etiqueta == label)
        stat_result = stat_result.filter(CitCitaStats.categoria == CitCitaStats.CAT_CITAS_TOTALES)
        stat_result = stat_result.filter(CitCitaStats.subcategoria == subcategoria).first()
        if stat_result:
            stat_result.dato = datos[label]
            # Si el dato no cambiaba, seguía siendo el mismo no hacía la actualización de la hora. Ahora lo forzamos.
            stat_result.modificado = datetime.now()
            stat_result.save()
        else:
            CitCitaStats(
                etiqueta=label,
                dato=datos[label],
                categoria=CitCitaStats.CAT_CITAS_TOTALES,
                subcategoria=subcategoria,
            ).save()


def _calcular_lunes_viernes_fecha(fecha: datetime):
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


def _calcular_dias_mes(fecha: datetime):
    """Regresa el número de días en un mes dado"""
    numero_dias = (fecha.replace(month=fecha.month % 12 + 1, day=1) - timedelta(days=1)).day
    return numero_dias


def _stats_hoy():
    """Generador de la estadística HOY, citas por hora"""
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    fecha_hora_inicio = None
    fecha_hora_fin = None
    resultados = {}
    labels = ["8:00", "9:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00", "17:00"]  # Tiene un elemento de más, para formar los rangos de búsqueda
    for i in range(len(labels) - 1):
        fecha_hora_inicio = fecha_hoy + " " + labels[i]
        fecha_hora_inicio = datetime.strptime(fecha_hora_inicio, "%Y-%m-%d %H:%M")
        fecha_hora_fin = fecha_hoy + " " + labels[i + 1]
        fecha_hora_fin = datetime.strptime(fecha_hora_fin, "%Y-%m-%d %H:%M")
        # La regla es: Cita que comienza a cierta hora y termina antes del comienzo del otro horario
        conteo = CitCita.query.filter(CitCita.inicio >= fecha_hora_inicio).filter(CitCita.inicio < fecha_hora_fin).count()
        resultados[labels[i]] = conteo
    # Quita de las etiquetas el último elemento, que solo se utiliza para hacer los rangos de búsqueda
    labels.pop()
    return labels, resultados, CitCitaStats.SUBCAT_CITAS_TOTALES_HOY


def _stats_semana():
    """Generador de la estadística SEMANA, citas por día de la semana"""
    lunes, _ = _calcular_lunes_viernes_fecha(datetime.now())
    dia_inicio = lunes
    dia_fin = lunes + timedelta(days=1)
    resultados = {}
    labels = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"]
    for i in range(len(labels)):
        conteo = CitCita.query.filter(CitCita.inicio >= dia_inicio).filter(CitCita.inicio < dia_fin).count()
        resultados[labels[i]] = conteo
        dia_inicio = dia_inicio + timedelta(days=1)
        dia_fin = dia_fin + timedelta(days=1)
    return labels, resultados, CitCitaStats.SUBCAT_CITAS_TOTALES_SEMANA


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
                registro = CitCitaStats.query
                registro = registro.filter(CitCitaStats.etiqueta == str(i))
                registro = registro.filter(CitCitaStats.categoria == CitCitaStats.CAT_CITAS_TOTALES)
                registro = registro.filter(CitCitaStats.subcategoria == CitCitaStats.SUBCAT_CITAS_TOTALES_MES).first()
                if registro:
                    registro.estatus = "A"
                    registro.save()
        else:
            # borra los regitros no utilizados
            registro = CitCitaStats.query
            registro = registro.filter(CitCitaStats.etiqueta == str(i))
            registro = registro.filter(CitCitaStats.categoria == CitCitaStats.CAT_CITAS_TOTALES)
            registro = registro.filter(CitCitaStats.subcategoria == CitCitaStats.SUBCAT_CITAS_TOTALES_MES).first()
            if registro:
                registro.delete()

    return labels, resultados, CitCitaStats.SUBCAT_CITAS_TOTALES_MES


def _stats_cinco_meses():
    """Generador de la estadística SEIS_MESES, citas por mes"""
    mes_fin = datetime.now().date().replace(day=1) + relativedelta(months=2)
    mes_ini = datetime.now().date().replace(day=1) - relativedelta(months=2)
    mes = datetime.now().date().replace(day=1, month=1)
    resultados = {}
    labels = []
    label = ""
    for i in range(1, 13):
        label = mes.strftime("%B")
        if i >= mes_ini.month and i <= mes_fin.month:
            labels.append(label)
            conteo = CitCita.query.filter(CitCita.inicio >= mes).filter(CitCita.inicio < mes + relativedelta(months=1)).count()
            resultados[label] = conteo

            registro = CitCitaStats.query
            registro = registro.filter(CitCitaStats.etiqueta == label)
            registro = registro.filter(CitCitaStats.categoria == CitCitaStats.CAT_CITAS_TOTALES)
            registro = registro.filter(CitCitaStats.subcategoria == CitCitaStats.SUBCAT_CITAS_TOTALES_CINCO_MESES).first()
            if registro:
                registro.estatus = "A"
                registro.save()
        else:
            # borra los regitros no utilizados
            registro = CitCitaStats.query
            registro = registro.filter(CitCitaStats.etiqueta == label)
            registro = registro.filter(CitCitaStats.categoria == CitCitaStats.CAT_CITAS_TOTALES)
            registro = registro.filter(CitCitaStats.subcategoria == CitCitaStats.SUBCAT_CITAS_TOTALES_CINCO_MESES).first()
            if registro:
                registro.delete()
        mes = mes + relativedelta(months=1)

    return labels, resultados, CitCitaStats.SUBCAT_CITAS_TOTALES_CINCO_MESES


def _stats_ano():
    """Generador de la estadística ANO, citas por mes"""
    mes_ini = datetime.now().date().replace(day=1, month=1)
    mes = mes_ini
    resultados = {}
    labels = []
    for i in range(13):
        label = mes.strftime("%B")
        labels.append(label)
        conteo = CitCita.query.filter(CitCita.inicio >= mes).filter(CitCita.inicio < mes + relativedelta(months=1)).count()
        resultados[label] = conteo
        mes = mes + relativedelta(months=1)
    return labels, resultados, CitCitaStats.SUBCAT_CITAS_TOTALES_ANO
