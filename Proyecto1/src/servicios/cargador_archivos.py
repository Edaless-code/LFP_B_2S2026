"""Carga y validacion de archivos fuente con extension .hor."""

import os

EXTENSION_ESPERADA = ".hor"
CODIFICACION = "utf-8"


class ErrorDeCarga(Exception):
    """Se lanza cuando un archivo .hor no puede leerse."""


class CargadorArchivos:
    """Lee archivos .hor desde el disco validando su existencia y formato."""

    @staticmethod
    def validar_extension(ruta: str) -> bool:
        """Indica si la ruta termina en la extension esperada.

        Args:
            ruta: Ruta del archivo a validar.

        Returns:
            True si la extension es .hor, sin distinguir mayusculas.
        """
        largo = len(EXTENSION_ESPERADA)
        if len(ruta) < largo:
            return False
        final = ruta[-largo:]
        return final.lower() == EXTENSION_ESPERADA

    @staticmethod
    def cargar(ruta: str) -> str:
        """Lee el contenido completo de un archivo .hor.

        Args:
            ruta: Ruta absoluta o relativa del archivo.

        Returns:
            El texto del archivo con saltos de linea normalizados a \\n.

        Raises:
            ErrorDeCarga: Si la ruta no existe, no es un archivo, tiene otra
                extension o no puede leerse con la codificacion esperada.
        """
        if not os.path.exists(ruta):
            raise ErrorDeCarga(f"El archivo no existe: {ruta}")

        if not os.path.isfile(ruta):
            raise ErrorDeCarga(f"La ruta no apunta a un archivo: {ruta}")

        if not CargadorArchivos.validar_extension(ruta):
            raise ErrorDeCarga(
                f"El archivo debe tener extension {EXTENSION_ESPERADA}: {ruta}"
            )

        try:
            with open(ruta, "r", encoding=CODIFICACION, newline=None) as archivo:
                return archivo.read()
        except UnicodeDecodeError as error:
            raise ErrorDeCarga(
                f"El archivo no esta codificado en {CODIFICACION}: {ruta}"
            ) from error
        except OSError as error:
            raise ErrorDeCarga(f"No se pudo leer el archivo: {ruta}") from error
