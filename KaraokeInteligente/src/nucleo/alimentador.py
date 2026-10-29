"""Alimentacion de la base de datos CANCIONES (opcion f del menu principal).

(t) Archivo de texto plano. Formato (el del enunciado):

        NOMBRE DE LA CANCION
        primera linea de la letra
        segunda linea de la letra
        ...
        <linea vacia>
        NOMBRE DE OTRA CANCION
        ...

    Una linea vacia termina la cancion, igual que en la captura manual. Si la
    letra trae estrofas separadas por lineas vacias, las canciones se pueden
    separar con una linea de tres o mas guiones (---), signos igual (===),
    asteriscos (***) o numerales (###); en ese caso las lineas vacias se ignoran.
    El nombre puede llevar opcionalmente el prefijo "NOMBRE:" o "TITULO:".
    Los renglones que empiezan con un solo "#" son comentarios y se ignoran.

(e) Captura manual: nombre y luego linea por linea; la linea vacia termina.

El largo de las lineas se controla con max_caracteres_linea y lineas_largas
de config.json (ver configuracion.py).
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass

from nucleo.modelos import ResultadoImportacion
from nucleo.texto import partir_linea

SEPARADOR = re.compile(r"^\s*(-{3,}|={3,}|\*{3,}|#{3,})\s*$")
PREFIJO_NOMBRE = re.compile(r"^\s*(nombre(\s+(de\s+la\s+)?canci[oó]n)?|t[ií]tulo)\s*:\s*", re.IGNORECASE)
CODIFICACIONES = ("utf-8-sig", "cp1252", "latin-1")
MAX_CARACTERES_NOMBRE = 150

# Que hacer si al importar ya existe una cancion con el mismo nombre.
DUPLICADOS_OMITIR = "omitir"
DUPLICADOS_REEMPLAZAR = "reemplazar"
DUPLICADOS_AGREGAR = "agregar"


@dataclass
class CancionLeida:
    nombre: str
    lineas: list[str]
    renglon: int  # renglon del archivo donde esta el nombre (desde 1)


class ErrorArchivo(Exception):
    """El archivo no existe o no se puede leer."""


def limpiar_ruta(ruta: str) -> str:
    """Quita espacios y comillas (Windows las agrega al arrastrar un archivo a la consola)."""
    ruta = (ruta or "").strip()
    if len(ruta) >= 2 and ruta[0] == ruta[-1] and ruta[0] in "\"'":
        ruta = ruta[1:-1].strip()
    return os.path.expanduser(ruta)


def leer_archivo_texto(ruta: str) -> str:
    """Lee un archivo de texto probando UTF-8 y luego ANSI de Windows (Bloc de notas)."""
    ruta = limpiar_ruta(ruta)
    if not ruta:
        raise ErrorArchivo("No se indicó ningún archivo.")
    if not os.path.isfile(ruta):
        raise ErrorArchivo(f"No existe el archivo: {ruta}")
    try:
        with open(ruta, "rb") as archivo:
            contenido = archivo.read()
    except OSError as error:
        raise ErrorArchivo(f"No se pudo leer {ruta}: {error}") from error
    for codificacion in CODIFICACIONES:
        try:
            return contenido.decode(codificacion)
        except UnicodeDecodeError:
            continue
    return contenido.decode("utf-8", errors="replace")


def es_comentario(renglon: str) -> bool:
    return renglon.lstrip().startswith("#") and not SEPARADOR.match(renglon)


def limpiar_nombre(nombre: str) -> str:
    nombre = PREFIJO_NOMBRE.sub("", nombre.strip(), count=1)
    return " ".join(nombre.split())[:MAX_CARACTERES_NOMBRE]


def interpretar_canciones(texto: str) -> tuple[list[CancionLeida], list[str]]:
    """Separa el texto en canciones. Devuelve (canciones, advertencias)."""
    renglones = texto.replace("\ufeff", "").replace("\r\n", "\n").replace("\r", "\n").split("\n")
    con_separadores = any(SEPARADOR.match(r) for r in renglones)
    canciones: list[CancionLeida] = []
    advertencias: list[str] = []
    bloque: list[tuple[int, str]] = []

    def cerrar_bloque() -> None:
        utiles = [(n, r.strip()) for n, r in bloque if r.strip()]
        bloque.clear()
        if not utiles:
            return
        renglon, nombre = utiles[0]
        nombre = limpiar_nombre(nombre)
        lineas = [r for _, r in utiles[1:]]
        if not nombre:
            advertencias.append(f"Renglón {renglon}: canción sin nombre; se omitió.")
        elif not lineas:
            advertencias.append(f"Renglón {renglon}: «{nombre}» no tiene letra; se omitió.")
        else:
            canciones.append(CancionLeida(nombre, lineas, renglon))

    for numero, renglon in enumerate(renglones, start=1):
        if es_comentario(renglon):
            continue
        if con_separadores:
            if SEPARADOR.match(renglon):
                cerrar_bloque()
            else:
                bloque.append((numero, renglon))
        elif renglon.strip():
            bloque.append((numero, renglon))
        else:
            cerrar_bloque()
    cerrar_bloque()
    return canciones, advertencias


def preparar_lineas(lineas: list[str], max_caracteres: int, modo_largas: str, max_lineas: int) -> tuple[list[str], list[str]]:
    """Limpia espacios, aplica la regla de lineas largas y el limite de lineas.

    modo_largas = "partir": divide la linea en varias de hasta max_caracteres.
    modo_largas = "aceptar": la guarda completa (en pantalla se ajusta al ancho).
    """
    resultado: list[str] = []
    largas = 0
    for linea in lineas:
        linea = " ".join(linea.split())
        if not linea:
            continue
        if max_caracteres > 0 and len(linea) > max_caracteres:
            largas += 1
            if modo_largas == "partir":
                resultado.extend(partir_linea(linea, max_caracteres))
                continue
        resultado.append(linea)
    advertencias = []
    if largas:
        accion = "se partieron" if modo_largas == "partir" else "se guardaron completas"
        advertencias.append(f"{largas} línea(s) pasan de {max_caracteres} caracteres; {accion}.")
    if max_lineas > 0 and len(resultado) > max_lineas:
        advertencias.append(f"La letra tenía {len(resultado)} líneas; se guardaron las primeras {max_lineas}.")
        resultado = resultado[:max_lineas]
    return resultado, advertencias


class Alimentador:
    def __init__(self, repositorio, configuracion) -> None:
        self.repositorio = repositorio
        self.configuracion = configuracion

    def preparar(self, lineas: list[str]) -> tuple[list[str], list[str]]:
        c = self.configuracion
        return preparar_lineas(
            lineas,
            c.obtener_entero("max_caracteres_linea", minimo=0),
            str(c["lineas_largas"]),
            c.obtener_entero("max_lineas_cancion", minimo=0),
        )

    # ------------------------------------------------------------ opcion (t)
    def importar_archivo(self, ruta: str, duplicados: str = DUPLICADOS_OMITIR) -> ResultadoImportacion:
        try:
            texto = leer_archivo_texto(ruta)
        except ErrorArchivo as error:
            resultado = ResultadoImportacion()
            resultado.errores.append(str(error))
            return resultado
        return self.importar_texto(texto, duplicados)

    def repetidas(self, canciones: list[CancionLeida]) -> list[str]:
        """Nombres del archivo que ya existen en la base de datos."""
        return [c.nombre for c in canciones if self.repositorio.codigo_por_nombre(c.nombre) is not None]

    def importar_texto(self, texto: str, duplicados: str = DUPLICADOS_OMITIR, origen: str = "t") -> ResultadoImportacion:
        resultado = ResultadoImportacion()
        canciones, advertencias = interpretar_canciones(texto)
        resultado.advertencias.extend(advertencias)
        if not canciones:
            resultado.errores.append("El archivo no contiene canciones con el formato esperado.")
            return resultado
        for cancion in canciones:
            lineas, avisos = self.preparar(cancion.lineas)
            resultado.advertencias.extend(f"«{cancion.nombre}»: {a}" for a in avisos)
            existente = self.repositorio.codigo_por_nombre(cancion.nombre)
            try:
                if existente is not None and duplicados == DUPLICADOS_OMITIR:
                    resultado.omitidas.append(cancion.nombre)
                elif existente is not None and duplicados == DUPLICADOS_REEMPLAZAR:
                    self.repositorio.reemplazar_letra(existente, lineas)
                    resultado.reemplazadas.append((existente, cancion.nombre))
                else:
                    codigo = self.repositorio.agregar_cancion(cancion.nombre, lineas, origen=origen)
                    resultado.agregadas.append((codigo, cancion.nombre))
            except ValueError as error:
                resultado.errores.append(f"Renglón {cancion.renglon} «{cancion.nombre}»: {error}")
        return resultado

    # ------------------------------------------------------------ opcion (e)
    def agregar_manual(self, nombre: str, lineas: list[str]) -> tuple[int, list[str]]:
        """Guarda una cancion tecleada en pantalla. Devuelve (codigo generado, advertencias)."""
        nombre = limpiar_nombre(nombre)
        lineas, advertencias = self.preparar(lineas)
        codigo = self.repositorio.agregar_cancion(nombre, lineas, origen="e")
        return codigo, advertencias

    def existe_nombre(self, nombre: str) -> int | None:
        return self.repositorio.codigo_por_nombre(limpiar_nombre(nombre))

    # ------------------------------------------------------------ respaldo
    def exportar(self, ruta: str, codigos: list[int] | None = None) -> int:
        """Escribe las canciones con el mismo formato de la opcion (t). Devuelve cuantas escribio."""
        canciones = self.repositorio.todas_las_canciones()
        if codigos is not None:
            elegidos = set(codigos)
            canciones = [c for c in canciones if c.codigo in elegidos]
        directorio = os.path.dirname(ruta)
        if directorio:
            os.makedirs(directorio, exist_ok=True)
        with open(ruta, "w", encoding="utf-8") as archivo:
            for numero, cancion in enumerate(canciones):
                if numero:
                    archivo.write("\n")
                archivo.write(cancion.nombre + "\n")
                for linea in cancion.lineas:
                    archivo.write(linea + "\n")
        return len(canciones)
