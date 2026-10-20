"""Lectura y escritura de archivos .md con validacion."""

import os

EXTENSION_VALIDA = ".md"

# Codificaciones que se intentan en orden. cp1252 cubre los archivos guardados
# con el Bloc de notas antiguo de Windows; latin-1 nunca falla y es el ultimo
# recurso para no rechazar un archivo legible.
CODIFICACIONES = ("utf-8", "cp1252", "latin-1")


class ErrorCarga(Exception):
    """Error al leer o escribir un archivo, con un mensaje para el usuario."""


class CargadorArchivos:
    """Valida y lee archivos .md, y guarda el contenido del editor."""

    @staticmethod
    def cargar(ruta: str) -> str:
        """Lee un archivo .md despues de validar que exista y sea legible.

        Args:
            ruta: Ruta del archivo a leer.

        Returns:
            El contenido completo del archivo.

        Raises:
            ErrorCarga: Si el archivo no existe, no es un archivo, no tiene
                extension .md o no se puede leer.
        """
        if not os.path.exists(ruta):
            raise ErrorCarga(f"El archivo no existe:\n{ruta}")
        if not os.path.isfile(ruta):
            raise ErrorCarga(f"La ruta no corresponde a un archivo:\n{ruta}")
        if not ruta.lower().endswith(EXTENSION_VALIDA):
            raise ErrorCarga(f"Solo se admiten archivos con extensión {EXTENSION_VALIDA}:\n{ruta}")

        try:
            with open(ruta, "rb") as archivo:
                contenido = archivo.read()
        except OSError as error:
            raise ErrorCarga(f"No se pudo leer el archivo:\n{ruta}\n\n{error.strerror}") from error

        for codificacion in CODIFICACIONES:
            try:
                return contenido.decode(codificacion)
            except UnicodeDecodeError:
                continue
        raise ErrorCarga(f"No se pudo interpretar la codificación del archivo:\n{ruta}")

    @staticmethod
    def guardar(ruta: str, texto: str) -> None:
        """Guarda el texto en UTF-8.

        Raises:
            ErrorCarga: Si el archivo no se puede escribir.
        """
        try:
            with open(ruta, "w", encoding="utf-8", newline="\n") as archivo:
                archivo.write(texto)
        except OSError as error:
            raise ErrorCarga(f"No se pudo guardar el archivo:\n{ruta}\n\n{error.strerror}") from error
