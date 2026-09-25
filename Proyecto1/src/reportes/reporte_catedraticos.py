"""Reporte 2: carga academica de los catedraticos.

Muestra, por catedratico, su categoria, las horas semanales asignadas, el
numero de cursos y secciones que atiende, y un nivel de carga con color.
"""

from modelos.entidades import Horario
from reportes.estilos import envolver, escapar

UMBRAL_BAJA = 4
UMBRAL_NORMAL = 10
UMBRAL_ALTA = 15

NIVELES = (
    (UMBRAL_BAJA, "BAJA", "et-baja"),
    (UMBRAL_NORMAL, "NORMAL", "et-normal"),
    (UMBRAL_ALTA, "ALTA", "et-alta"),
)
NIVEL_SATURADA = ("SATURADA", "et-saturada")


def nivel_de_carga(horas: float) -> tuple[str, str]:
    """Clasifica una carga semanal segun los umbrales del manual tecnico.

    Args:
        horas: Horas semanales asignadas al catedratico.

    Returns:
        Tupla con el nombre del nivel y su clase CSS.
    """
    for limite, nombre, css in NIVELES:
        if horas <= limite:
            return nombre, css
    return NIVEL_SATURADA


def _resumen(horario: Horario) -> list[dict]:
    """Calcula las metricas de carga de cada catedratico."""
    filas = []
    for codigo, catedratico in horario.catedraticos.items():
        minutos = 0
        cursos = set()
        secciones = set()
        for clase in horario.clases:
            if clase.codigo_catedratico == codigo:
                minutos += clase.duracion_minutos
                cursos.add(clase.codigo_curso)
                if clase.seccion:
                    secciones.add(clase.seccion)

        horas = minutos / 60
        nombre_nivel, css_nivel = nivel_de_carga(horas)
        filas.append({
            "nombre": catedratico.nombre,
            "codigo": codigo,
            "categoria": catedratico.categoria,
            "horas": horas,
            "cursos": len(cursos),
            "secciones": len(secciones),
            "nivel": nombre_nivel,
            "css": css_nivel,
        })

    filas.sort(key=lambda fila: fila["horas"], reverse=True)
    return filas


def generar(horario: Horario) -> str:
    """Genera el documento HTML de carga de catedraticos.

    Args:
        horario: Horario reconstruido a partir de los tokens.

    Returns:
        El documento HTML completo.
    """
    filas = _resumen(horario)

    if not filas:
        cuerpo = '<div class="vacio">El archivo no declara catedraticos.</div>'
    else:
        cuerpo_filas = ""
        for fila in filas:
            cuerpo_filas += (
                "<tr>"
                f"<td>{escapar(fila['nombre'])}</td>"
                f"<td>{escapar(fila['codigo'])}</td>"
                f"<td>{escapar(fila['categoria'])}</td>"
                f"<td class=\"num\">{fila['horas']:.2f}</td>"
                f"<td class=\"num\">{fila['cursos']}</td>"
                f"<td class=\"num\">{fila['secciones']}</td>"
                f"<td class=\"centro\"><span class=\"etiqueta {fila['css']}\">{fila['nivel']}</span></td>"
                "</tr>"
            )
        cuerpo = (
            "<section><h2>Carga semanal por catedratico</h2><table><thead><tr>"
            "<th>Catedratico</th><th>Codigo</th><th>Categoria</th>"
            '<th class="num">Horas semanales</th><th class="num">Cursos</th>'
            '<th class="num">Secciones</th><th class="centro">Nivel de carga</th>'
            "</tr></thead>"
            f"<tbody>{cuerpo_filas}</tbody></table>"
            "<p class=\"barra-texto\">Umbrales: BAJA hasta "
            f"{UMBRAL_BAJA} h, NORMAL hasta {UMBRAL_NORMAL} h, "
            f"ALTA hasta {UMBRAL_ALTA} h, SATURADA por encima.</p></section>"
        )

    subtitulo = f"{len(filas)} catedraticos registrados"
    return envolver("Reporte 2 - Carga de Catedraticos", subtitulo, cuerpo)
