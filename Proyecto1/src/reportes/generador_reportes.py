"""Fachada que genera y guarda en disco los reportes HTML del sistema."""

import os

from modelos.entidades import Horario
from reportes import (
    reporte_catedraticos,
    reporte_errores,
    reporte_estadistico,
    reporte_horario,
)

ARCHIVO_HORARIO = "reporte_horario_semanal.html"
ARCHIVO_CATEDRATICOS = "reporte_carga_catedraticos.html"
ARCHIVO_ESTADISTICO = "reporte_estadistico.html"
ARCHIVO_ERRORES = "reporte_errores.html"


class GeneradorReportes:
    """Genera los tres reportes exigidos mas el reporte de errores."""

    def __init__(self, directorio_salida: str) -> None:
        """Inicializa el generador.

        Args:
            directorio_salida: Carpeta donde se escriben los archivos HTML.
                Se crea si no existe.
        """
        self._directorio = directorio_salida
        os.makedirs(self._directorio, exist_ok=True)

    def _escribir(self, nombre: str, contenido: str) -> str:
        """Escribe un documento HTML y devuelve su ruta absoluta."""
        ruta = os.path.join(self._directorio, nombre)
        with open(ruta, "w", encoding="utf-8") as archivo:
            archivo.write(contenido)
        return os.path.abspath(ruta)

    def generar_todos(self, horario: Horario, choques: list,
                      ids_en_choque: set, errores: list) -> dict[str, str]:
        """Genera los cuatro reportes y los guarda en disco.

        Args:
            horario: Horario reconstruido a partir de los tokens.
            choques: Lista de choques detectados.
            ids_en_choque: Identificadores de las clases en conflicto.
            errores: Lista de errores lexicos acumulados.

        Returns:
            Diccionario que asocia cada reporte con la ruta de su archivo.
        """
        return {
            "horario": self._escribir(
                ARCHIVO_HORARIO, reporte_horario.generar(horario, ids_en_choque)
            ),
            "catedraticos": self._escribir(
                ARCHIVO_CATEDRATICOS, reporte_catedraticos.generar(horario)
            ),
            "estadistico": self._escribir(
                ARCHIVO_ESTADISTICO,
                reporte_estadistico.generar(horario, len(choques)),
            ),
            "errores": self._escribir(
                ARCHIVO_ERRORES, reporte_errores.generar(errores)
            ),
        }
