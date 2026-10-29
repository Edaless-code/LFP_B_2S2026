"""Arma las piezas del programa (configuracion, base de datos, buscador, programa).

Lo usan por igual la version de consola y la interfaz grafica.
"""

from __future__ import annotations

import os

from configuracion import Configuracion
from datos.base_datos import BaseDatos
from datos.repositorio import Repositorio
from nucleo.alimentador import Alimentador, ErrorArchivo
from nucleo.buscador import BuscadorCanciones
from nucleo.programa import ProgramaCantante
from nucleo.sesion import SesionKaraoke
from plataforma import nombre_plataforma


class Aplicacion:
    def __init__(self, directorio_datos: str | None = None) -> None:
        self.configuracion = Configuracion(directorio_datos)
        self.base = BaseDatos(self.configuracion.ruta_base_datos)
        self.repositorio = Repositorio(self.base)
        self.buscador = BuscadorCanciones(self.repositorio)
        self.alimentador = Alimentador(self.repositorio, self.configuracion)
        self.programa = ProgramaCantante(self.repositorio)
        self.mensajes_inicio: list[str] = list(self.base.mensajes)
        if not self.base.existia and self.configuracion["cargar_ejemplos_al_crear"]:
            self._cargar_ejemplos()
        self.programa.cargar_guardado()

    @property
    def plataforma(self) -> str:
        return nombre_plataforma()

    def _cargar_ejemplos(self) -> None:
        ruta = self.configuracion.ruta_ejemplos
        if not os.path.isfile(ruta):
            return
        resultado = self.alimentador.importar_archivo(ruta)
        if resultado.agregadas:
            self.mensajes_inicio.append(
                f"Se cargaron {len(resultado.agregadas)} canciones de ejemplo (recursos/canciones_ejemplo.txt)."
            )

    def nueva_sesion(self, modo: str = "manual") -> SesionKaraoke:
        sesion = SesionKaraoke(self.repositorio, self.programa, modo)
        sesion.iniciar()
        return sesion

    def cargar_programa_por_defecto(self) -> str:
        """Carga el archivo PROGRAMA de la carpeta de datos; devuelve un mensaje."""
        ruta = self.configuracion.ruta_programa
        try:
            items = self.programa.cargar_desde_archivo(ruta)
        except ErrorArchivo as error:
            return str(error)
        return f"PROGRAMA cargado con {len(items)} canciones."

    def despues_de_cambiar_canciones(self) -> None:
        """Mantiene el programa al dia cuando se agregan o borran canciones."""
        self.programa.resolver_pendientes()

    def cerrar(self) -> None:
        self.base.cerrar()
