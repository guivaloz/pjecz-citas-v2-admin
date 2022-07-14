"""
Archivo con funciones para actualizar los datos estadísticos
"""

from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta

from citas_admin.blueprints.cit_citas.models import CitCita
from citas_admin.blueprints.cit_citas_stats.models import CitCitaStats


def obtener_stats_json_estados(subcategoria: str):
    """Entrega los datos para gráficas"""

    etiquetas, datos, subtitulo = _obtener_labels_datos_stats(subcategoria)
    if subcategoria == CitCitaStats.SUBCAT_CITAS_ESTADO_PORCENTAJE:
        titulo = f"Porcentaje de los diferentes estados de las citas totales"
        label = "Citas por Hora"

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
    results = CitCitaStats.query.filter(CitCitaStats.estatus == "A")
    results = results.filter(CitCitaStats.categoria == CitCitaStats.CAT_CITAS_ESTADO)
    results = results.filter(CitCitaStats.subcategoria == subcategoria)
    results = results.order_by(CitCitaStats.id).all()
    etiquetas = []
    datos = []
    ultima_actualizacion = None
    for result in results:
        etiquetas.append(result.etiqueta)
        datos.append(result.dato)
    if len(results) > 0:
        ultima_actualizacion = results[len(results) - 1].modificado.strftime("Reporte Generado: %Y/%m/%d a las %H:%M")
    return etiquetas, datos, ultima_actualizacion


def actualizar_stats_estados():
    """Actualiza las estadísticas, ejecuta query's de actualización de los registros"""

    # Obtiene los nuevos datos de la estadística
    labels, resultados, subcategoria = _stats_porcentaje_estado()
    actualizar_estadistica(labels, resultados, subcategoria)


def actualizar_estadistica(labels, datos, subcategoria):
    """Actualiza los datos de una estadística"""
    for label in labels:
        # busca el registro de ese dato, para actualizarlo sino para crearlo
        stat_result = CitCitaStats.query
        stat_result = stat_result.filter(CitCitaStats.etiqueta == label)
        stat_result = stat_result.filter(CitCitaStats.categoria == CitCitaStats.CAT_CITAS_ESTADO)
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
                categoria=CitCitaStats.CAT_CITAS_ESTADO,
                subcategoria=subcategoria,
            ).save()


def _stats_porcentaje_estado():
    """Generador de la estadística PORCENTAJE, da el porcentaje del estado de las citas totales"""
    resultados = {}
    labels = ["ASISTIO", "CANCELO", "PENDIENTE"]
    #total = CitCita.query.count()
    for label in labels:
        conteo = CitCita.query
        conteo = conteo.filter(CitCita.estado == label)
        conteo = conteo.count()
        resultados[label] = conteo
    return labels, resultados, CitCitaStats.SUBCAT_CITAS_ESTADO_PORCENTAJE
