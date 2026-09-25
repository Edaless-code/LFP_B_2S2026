"""Reporte 1: horario semanal por seccion.

Presenta una rejilla de Lunes a Sabado con los bloques de cada seccion. Las
celdas cuyas clases participan en un choque se resaltan en rojo con una marca
de advertencia; el resto aparece en verde como CONFIRMADO.
"""

from modelos.entidades import Horario
from reportes.estilos import envolver, escapar

DIAS_SEMANA = ("LUNES", "MARTES", "MIERCOLES", "JUEVES", "VIERNES", "SABADO")
SECCION_SIN_DEFINIR = "SIN SECCION"


def _secciones(horario: Horario) -> list[str]:
    """Devuelve las secciones presentes en el horario, ordenadas."""
    encontradas = set()
    for clase in horario.clases:
        encontradas.add(clase.seccion if clase.seccion else SECCION_SIN_DEFINIR)
    return sorted(encontradas)


def _bloques(clases: list) -> list[tuple[int, int, str, str]]:
    """Devuelve los bloques horarios distintos, ordenados por hora de inicio.

    Args:
        clases: Clases de una seccion.

    Returns:
        Lista de tuplas (inicio_minutos, fin_minutos, inicio, fin).
    """
    distintos = set()
    for clase in clases:
        distintos.add(
            (clase.inicio_minutos, clase.fin_minutos, clase.inicio, clase.fin)
        )
    return sorted(distintos)


def _celda(clase, horario: Horario, en_choque: bool) -> str:
    """Genera el contenido HTML de una celda ocupada."""
    curso = horario.cursos.get(clase.codigo_curso)
    catedratico = horario.catedraticos.get(clase.codigo_catedratico)

    nombre_curso = curso.nombre if curso else clase.codigo_curso
    nombre_docente = catedratico.nombre if catedratico else clase.codigo_catedratico

    clase_css = "celda-choque" if en_choque else "celda-ok"
    marca = '<span class="marca">CHOQUE DE HORARIO</span>' if en_choque else ""

    return (
        f'<td class="celda {clase_css}">'
        f'<span class="curso">{escapar(nombre_curso)}</span>'
        f'<span class="detalle">{escapar(nombre_docente)}</span>'
        f'<span class="detalle">Aula {escapar(clase.codigo_aula)}</span>'
        f"{marca}</td>"
    )


def _tabla_de_seccion(seccion: str, clases: list, horario: Horario,
                      ids_en_choque: set) -> str:
    """Genera la rejilla semanal de una seccion."""
    bloques = _bloques(clases)
    if not bloques:
        return ""

    encabezados = "".join(f"<th>{dia.capitalize()}</th>" for dia in DIAS_SEMANA)
    filas = ""

    for inicio_min, fin_min, inicio, fin in bloques:
        filas += f'<tr><td class="hora">{escapar(inicio)} - {escapar(fin)}</td>'
        for dia in DIAS_SEMANA:
            ocupada = None
            for clase in clases:
                if (clase.dia == dia
                        and clase.inicio_minutos == inicio_min
                        and clase.fin_minutos == fin_min):
                    ocupada = clase
                    break
            if ocupada is None:
                filas += '<td class="celda-vacia"></td>'
            else:
                filas += _celda(ocupada, horario, id(ocupada) in ids_en_choque)
        filas += "</tr>"

    return (
        f"<section><h2>Seccion {escapar(seccion)}</h2>"
        f'<table class="rejilla"><thead><tr><th class="hora">Bloque</th>'
        f"{encabezados}</tr></thead><tbody>{filas}</tbody></table></section>"
    )


def generar(horario: Horario, ids_en_choque: set) -> str:
    """Genera el documento HTML del horario semanal.

    Args:
        horario: Horario reconstruido a partir de los tokens.
        ids_en_choque: Identificadores de las clases involucradas en choques.

    Returns:
        El documento HTML completo.
    """
    if not horario.clases:
        cuerpo = '<div class="vacio">El archivo no declara clases.</div>'
    else:
        cuerpo = ""
        for seccion in _secciones(horario):
            clases = [
                clase for clase in horario.clases
                if (clase.seccion if clase.seccion else SECCION_SIN_DEFINIR) == seccion
            ]
            cuerpo += _tabla_de_seccion(seccion, clases, horario, ids_en_choque)

    total_choques = len(ids_en_choque)
    subtitulo = (
        f"{len(horario.clases)} clases programadas - "
        f"{total_choques} clases involucradas en choques de horario"
    )
    return envolver("Reporte 1 - Horario Semanal por Seccion", subtitulo, cuerpo)
