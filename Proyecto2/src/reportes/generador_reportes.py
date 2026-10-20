"""Escritura de los reportes HTML y del archivo arbol.dot.

Los archivos de cada analisis se guardan en salidas/<nombre del archivo>/.
Cuando el analisis termina sin errores se generan los tres reportes y el
arbol; cuando hay errores se genera solo el reporte de errores.
"""

import os
import shutil
import subprocess

from modelos.error_analisis import ErrorAnalisis
from modelos.nodo_ast import NodoAST
from reportes.estilos import (
    ARCHIVO_DOCUMENTO,
    ARCHIVO_DOT,
    ARCHIVO_ERRORES,
    ARCHIVO_ESTADISTICAS,
    ARCHIVO_INDICE,
    pagina,
    texto_html,
)
from reportes.generador_dot import generar_dot
from reportes.generador_html import GeneradorHTML
from reportes.reporte_estadisticas import calcular_estadisticas, generar_reporte_estadisticas
from reportes.reporte_indice import generar_reporte_indice

ARCHIVO_IMAGEN_ARBOL = "arbol.svg"
SEGUNDOS_MAXIMOS_GRAPHVIZ = 20


class SalidasGeneradas:
    """Rutas de los archivos producidos por un analisis.

    Los atributos que no se generaron quedan en None.
    """

    def __init__(self, directorio: str) -> None:
        self.directorio = directorio
        self.documento: str | None = None
        self.estadisticas: str | None = None
        self.indice: str | None = None
        self.arbol_dot: str | None = None
        self.arbol_imagen: str | None = None
        self.errores: str | None = None


class GeneradorReportes:
    """Escribe en disco los reportes de un analisis."""

    def __init__(self, directorio_salidas: str) -> None:
        """
        Args:
            directorio_salidas: Carpeta base (salidas/ del proyecto).
        """
        self._directorio_salidas = directorio_salidas

    def directorio_para(self, nombre_archivo: str) -> str:
        """Carpeta de salida de un archivo: salidas/<nombre sin extension>/."""
        base = os.path.splitext(os.path.basename(nombre_archivo))[0] or "sin_titulo"
        return os.path.join(self._directorio_salidas, base)

    def generar(
        self, raiz: NodoAST, nombre_archivo: str, directorio_documento: str | None = None
    ) -> SalidasGeneradas:
        """Genera los tres reportes HTML y arbol.dot de un analisis sin errores.

        Si Graphviz esta instalado tambien convierte el arbol a SVG; si no lo
        esta, solo se genera el archivo .dot.

        Args:
            raiz: Raiz del arbol de derivacion.
            nombre_archivo: Nombre del archivo .md analizado.
            directorio_documento: Carpeta del archivo .md, para ajustar las
                rutas relativas de imagenes y enlaces. None si el documento
                no se ha guardado.

        Raises:
            OSError: Si no se puede crear la carpeta o escribir un archivo.
        """
        salidas = SalidasGeneradas(self.directorio_para(nombre_archivo))
        os.makedirs(salidas.directorio, exist_ok=True)

        prefijo = ""
        if directorio_documento is not None:
            prefijo = os.path.relpath(directorio_documento, salidas.directorio).replace(os.sep, "/")
        generador_html = GeneradorHTML(raiz, prefijo)
        salidas.documento = self._escribir(
            salidas.directorio, ARCHIVO_DOCUMENTO, generador_html.generar_reporte(nombre_archivo)
        )
        salidas.estadisticas = self._escribir(
            salidas.directorio,
            ARCHIVO_ESTADISTICAS,
            generar_reporte_estadisticas(calcular_estadisticas(raiz), nombre_archivo),
        )
        salidas.indice = self._escribir(
            salidas.directorio,
            ARCHIVO_INDICE,
            generar_reporte_indice(generador_html.encabezados, nombre_archivo),
        )
        salidas.arbol_dot = self._escribir(salidas.directorio, ARCHIVO_DOT, generar_dot(raiz))
        salidas.arbol_imagen = self._convertir_dot(salidas.arbol_dot)

        self._eliminar(salidas.directorio, ARCHIVO_ERRORES)
        return salidas

    def generar_errores(self, errores: list[ErrorAnalisis], nombre_archivo: str) -> SalidasGeneradas:
        """Genera el reporte de errores y elimina los reportes de un analisis anterior.

        Asi la carpeta nunca contiene reportes que no corresponden al
        contenido actual del archivo.

        Raises:
            OSError: Si no se puede crear la carpeta o escribir el archivo.
        """
        salidas = SalidasGeneradas(self.directorio_para(nombre_archivo))
        os.makedirs(salidas.directorio, exist_ok=True)
        salidas.errores = self._escribir(
            salidas.directorio, ARCHIVO_ERRORES, generar_reporte_errores(errores, nombre_archivo)
        )
        for archivo in (ARCHIVO_DOCUMENTO, ARCHIVO_ESTADISTICAS, ARCHIVO_INDICE, ARCHIVO_DOT, ARCHIVO_IMAGEN_ARBOL):
            self._eliminar(salidas.directorio, archivo)
        return salidas

    # ------------------------------------------------------------------
    # Auxiliares
    # ------------------------------------------------------------------

    @staticmethod
    def _escribir(directorio: str, archivo: str, contenido: str) -> str:
        ruta = os.path.join(directorio, archivo)
        with open(ruta, "w", encoding="utf-8", newline="\n") as salida:
            salida.write(contenido)
        return ruta

    @staticmethod
    def _eliminar(directorio: str, archivo: str) -> None:
        ruta = os.path.join(directorio, archivo)
        if os.path.isfile(ruta):
            os.remove(ruta)

    @staticmethod
    def _convertir_dot(ruta_dot: str) -> str | None:
        """Convierte arbol.dot a SVG con el comando dot, si esta disponible.

        Returns:
            La ruta del SVG, o None si Graphviz no esta instalado o fallo.
        """
        ejecutable = shutil.which("dot")
        if ejecutable is None:
            return None
        ruta_imagen = os.path.join(os.path.dirname(ruta_dot), ARCHIVO_IMAGEN_ARBOL)
        try:
            subprocess.run(
                [ejecutable, "-Tsvg", ruta_dot, "-o", ruta_imagen],
                check=True,
                capture_output=True,
                timeout=SEGUNDOS_MAXIMOS_GRAPHVIZ,
            )
        except (OSError, subprocess.SubprocessError):
            return None
        return ruta_imagen


def generar_reporte_errores(errores: list[ErrorAnalisis], nombre_archivo: str) -> str:
    """Tabla de errores lexicos y sintacticos en una pagina HTML."""
    filas = []
    for error in errores:
        filas.append(
            "<tr>"
            f'<td class="numero">{error.numero}</td>'
            f"<td><code>{texto_html(error.lexema)}</code></td>"
            f'<td class="tipo">{error.tipo.value}</td>'
            f"<td>{error.fase.value}</td>"
            f"<td>{texto_html(error.descripcion)}</td>"
            f'<td class="numero">{error.linea}</td>'
            f'<td class="numero">{error.columna}</td>'
            "</tr>"
        )
    total = len(errores)
    cuerpo = (
        '<h1 class="titulo-reporte">Tabla de Errores</h1>\n'
        f'<p class="subtitulo">{texto_html(nombre_archivo)}</p>\n'
        f'<div class="insignia error">{total} {"error encontrado" if total == 1 else "errores encontrados"}</div>\n'
        '<table class="errores">'
        "<tr><th>No.</th><th>Lexema</th><th>Tipo</th><th>Fase</th>"
        "<th>Descripción</th><th>Línea</th><th>Columna</th></tr>"
        f'{"".join(filas)}</table>\n'
        '<p class="nota">Los reportes 1, 2 y 3 se generan únicamente cuando el análisis termina sin errores.</p>'
    )
    return pagina(f"{nombre_archivo} - Errores", cuerpo)
