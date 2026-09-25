"""Reporte 3: estadistico general del ciclo.

Resume el horario en un panel de indicadores clave y una tabla de ocupacion
de aulas con barra de progreso. Las aulas con mas del 80 por ciento de
ocupacion se resaltan en rojo.
"""

from modelos.entidades import Horario
from reportes.estilos import envolver, escapar

DIAS_HABILES = 6
HORAS_POR_DIA = 15  # jornada institucional de 06:00 a 21:00
MINUTOS_DISPONIBLES_POR_AULA = DIAS_HABILES * HORAS_POR_DIA * 60
UMBRAL_OCUPACION_CRITICA = 80.0


def _ocupacion_de_aulas(horario: Horario) -> list[dict]:
    """Calcula la ocupacion semanal de cada aula."""
    filas = []
    for codigo, aula in horario.aulas.items():
        minutos = 0
        asignadas = 0
        for clase in horario.clases:
            if clase.codigo_aula == codigo:
                minutos += clase.duracion_minutos
                asignadas += 1

        porcentaje = 0.0
        if MINUTOS_DISPONIBLES_POR_AULA > 0:
            porcentaje = minutos * 100 / MINUTOS_DISPONIBLES_POR_AULA

        filas.append({
            "codigo": codigo,
            "edificio": aula.edificio,
            "capacidad": aula.capacidad,
            "clases": asignadas,
            "horas": minutos / 60,
            "porcentaje": porcentaje,
        })

    filas.sort(key=lambda fila: fila["porcentaje"], reverse=True)
    return filas


def _kpi(titulo: str, valor, critico: bool = False) -> str:
    """Genera una tarjeta de indicador clave."""
    clase = "kpi critico" if critico else "kpi"
    return (f'<div class="{clase}"><div class="titulo">{escapar(titulo)}</div>'
            f'<div class="valor">{escapar(valor)}</div></div>')


def generar(horario: Horario, total_choques: int) -> str:
    """Genera el documento HTML del reporte estadistico.

    Args:
        horario: Horario reconstruido a partir de los tokens.
        total_choques: Cantidad de choques detectados.

    Returns:
        El documento HTML completo.
    """
    minutos_por_docente: dict[str, int] = {}
    for clase in horario.clases:
        codigo = clase.codigo_catedratico
        minutos_por_docente[codigo] = (
            minutos_por_docente.get(codigo, 0) + clase.duracion_minutos
        )

    docente_top = "-"
    if minutos_por_docente:
        codigo_top = max(minutos_por_docente, key=minutos_por_docente.get)
        catedratico = horario.catedraticos.get(codigo_top)
        nombre = catedratico.nombre if catedratico else codigo_top
        docente_top = f"{nombre} ({minutos_por_docente[codigo_top] / 60:.1f} h)"

    promedio = 0.0
    if horario.catedraticos:
        total_minutos = sum(clase.duracion_minutos for clase in horario.clases)
        promedio = total_minutos / 60 / len(horario.catedraticos)

    ocupacion = _ocupacion_de_aulas(horario)
    aula_top = "-"
    if ocupacion and ocupacion[0]["clases"] > 0:
        aula_top = f"{ocupacion[0]['codigo']} ({ocupacion[0]['porcentaje']:.1f}%)"

    tarjetas = (
        _kpi("Cursos", len(horario.cursos))
        + _kpi("Catedraticos", len(horario.catedraticos))
        + _kpi("Aulas", len(horario.aulas))
        + _kpi("Clases programadas", len(horario.clases))
        + _kpi("Choques de horario", total_choques, critico=total_choques > 0)
        + _kpi("Promedio h/catedratico", f"{promedio:.2f}")
    )

    destacados = (
        _kpi("Catedratico con mayor carga", docente_top)
        + _kpi("Aula con mayor ocupacion", aula_top)
    )

    if not ocupacion:
        tabla = '<div class="vacio">El archivo no declara aulas.</div>'
    else:
        filas = ""
        for fila in ocupacion:
            critica = fila["porcentaje"] > UMBRAL_OCUPACION_CRITICA
            clase_fila = ' class="fila-critica"' if critica else ""
            clase_barra = "barra alta" if critica else "barra"
            ancho = min(fila["porcentaje"], 100.0)
            filas += (
                f"<tr{clase_fila}>"
                f"<td>{escapar(fila['codigo'])}</td>"
                f"<td>{escapar(fila['edificio'])}</td>"
                f"<td class=\"num\">{fila['capacidad']}</td>"
                f"<td class=\"num\">{fila['clases']}</td>"
                f"<td class=\"num\">{fila['horas']:.2f}</td>"
                f'<td><div class="{clase_barra}"><span style="width:{ancho:.1f}%"></span></div>'
                f'<span class="barra-texto">{fila["porcentaje"]:.1f}%</span></td>'
                "</tr>"
            )
        tabla = (
            "<table><thead><tr><th>Aula</th><th>Edificio</th>"
            '<th class="num">Capacidad</th><th class="num">Clases</th>'
            '<th class="num">Horas semanales</th><th>Ocupacion</th>'
            f"</tr></thead><tbody>{filas}</tbody></table>"
            "<p class=\"barra-texto\">La ocupacion se calcula sobre "
            f"{DIAS_HABILES} dias de {HORAS_POR_DIA} horas (jornada 06:00-21:00). "
            f"Se resaltan las aulas por encima del {UMBRAL_OCUPACION_CRITICA:.0f}%.</p>"
        )

    cuerpo = (
        f'<section><h2>Indicadores generales</h2><div class="kpis">{tarjetas}</div></section>'
        f'<section><h2>Destacados</h2><div class="kpis">{destacados}</div></section>'
        f"<section><h2>Ocupacion de aulas</h2>{tabla}</section>"
    )

    return envolver(
        "Reporte 3 - Estadistico General del Ciclo",
        f"{len(horario.clases)} clases analizadas",
        cuerpo,
    )
