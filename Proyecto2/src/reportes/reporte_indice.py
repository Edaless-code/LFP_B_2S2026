"""Reporte 3: tabla de contenido a partir de los encabezados reconocidos."""

from reportes.estilos import ARCHIVO_DOCUMENTO, ARCHIVO_INDICE, atributo_html, pagina, texto_html
from reportes.generador_html import Encabezado

SANGRIA_POR_NIVEL = 22  # pixeles


def generar_reporte_indice(encabezados: list[Encabezado], nombre_archivo: str) -> str:
    """Reporte 3 completo: pagina HTML independiente con CSS embebido.

    Cada entrada enlaza al id del encabezado en el Reporte 1 y se indenta
    segun su nivel. Si el documento no tiene encabezados se indica de forma
    explicita.
    """
    if encabezados:
        entradas = []
        for encabezado in encabezados:
            margen = (encabezado.nivel - 1) * SANGRIA_POR_NIVEL
            entradas.append(
                f'<div class="entrada n{encabezado.nivel}" style="margin-left: {margen}px">'
                f'<span class="nivel-h">H{encabezado.nivel}</span>'
                f'<a href="{ARCHIVO_DOCUMENTO}#{atributo_html(encabezado.ancla)}">'
                f"{texto_html(encabezado.texto) or '(encabezado vacío)'}</a></div>"
            )
        contenido = f'<div class="indice">{"".join(entradas)}</div>\n'
        nota = (
            "Cada entrada enlaza a su sección dentro del Reporte 1. "
            "La sangría de cada entrada corresponde al nivel del encabezado."
        )
    else:
        contenido = (
            '<div class="vacio">El documento no contiene encabezados (# a ######), '
            "por lo que no hay entradas para la tabla de contenido.</div>\n"
        )
        nota = "El índice se genera únicamente a partir de los encabezados reconocidos por el parser."

    cuerpo = (
        '<h1 class="titulo-reporte">Tabla de Contenido</h1>\n'
        f'<p class="subtitulo">{texto_html(nombre_archivo)} — generado a partir de los encabezados reconocidos</p>\n'
        f"{contenido}"
        f'<p class="nota">{nota}</p>'
    )
    return pagina(f"{nombre_archivo} - Tabla de contenido", cuerpo, ARCHIVO_INDICE)
