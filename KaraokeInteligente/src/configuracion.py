"""Configuracion del programa y rutas de archivos.

Todos los valores ajustables viven en config.json, que se crea automaticamente
junto a la base de datos la primera vez que se ejecuta el programa. Si se borra,
se vuelve a crear con los valores de VALORES_POR_DEFECTO.

Los valores del enunciado ("cada cancion tiene en promedio 10 lineas" y "cada
linea tiene en promedio 80 caracteres") se cambian aqui:

    lineas_por_pagina      lineas de letra que se muestran por grupo (opcion x)
    canciones_por_pagina   canciones que se muestran por grupo (opcion w)
    max_caracteres_linea   largo maximo de una linea antes de partirla o advertir
    max_lineas_cancion     limite de lineas por cancion al alimentar

SQLite no limita el largo de un campo TEXT, por lo que estos valores no son
restricciones de la base de datos sino de captura y presentacion.
"""

from __future__ import annotations

import json
import os
import threading
from typing import Any

from plataforma import directorio_datos, directorio_programa

NOMBRE_BASE_DATOS = "CANCIONES.db"
NOMBRES_ALTERNATIVOS_BASE_DATOS = ("CANCIONES", "CANCIONES.sqlite", "CANCIONES.sqlite3")
NOMBRE_PROGRAMA = "PROGRAMA.txt"
NOMBRE_CONFIGURACION = "config.json"

VALORES_POR_DEFECTO: dict[str, Any] = {
    # Tamanos de la letra (enunciado: 10 lineas por cancion, 80 caracteres por linea)
    "lineas_por_pagina": 10,
    "canciones_por_pagina": 10,
    "max_caracteres_linea": 80,
    "max_lineas_cancion": 300,
    # "aceptar": guarda la linea larga y la parte solo en pantalla.
    # "partir": la divide en varias lineas al alimentar la base de datos.
    "lineas_largas": "aceptar",
    "cargar_ejemplos_al_crear": True,
    # Reconocimiento de voz
    "motor_voz": "auto",  # auto | whisper | android | simulado
    "modelo_whisper": "base",  # tiny | base | small | medium
    "idioma": "es",
    "idioma_android": "es-MX",
    "preferir_sin_conexion": True,
    "dispositivo_microfono": None,
    "duracion_ventana_seg": 4.0,
    "intervalo_transcripcion_seg": 1.5,
    "limpieza_audio": True,
    # Identificacion y sincronizacion (valores de 0 a 1)
    "umbral_identificacion": 0.55,
    "margen_identificacion": 0.08,
    "umbral_coincidencia_linea": 0.5,
    "avance_al_porcentaje": 0.7,
    "segundos_por_palabra_inicial": 0.45,
    "avance_por_tiempo": True,
    "segundos_silencio_ignorar": 7.0,
    "segundos_silencio_finalizar": 0,  # 0 = nunca finaliza solo
    "muestras_cancion_nueva": 3,
    "capturar_canciones_nuevas": True,
    # Pantalla
    "tamano_letra_karaoke": 34,
    "colores_consola": True,
}

_candado = threading.Lock()


class Configuracion:
    """Lee y guarda config.json; los valores faltantes se completan con los de por defecto."""

    def __init__(self, directorio: str | None = None) -> None:
        self.directorio = directorio or directorio_datos()
        os.makedirs(self.directorio, exist_ok=True)
        self.ruta = os.path.join(self.directorio, NOMBRE_CONFIGURACION)
        self.valores: dict[str, Any] = dict(VALORES_POR_DEFECTO)
        self.cargar()

    # ------------------------------------------------------------------ rutas
    @property
    def ruta_base_datos(self) -> str:
        """CANCIONES.db; si no existe pero hay una base llamada CANCIONES (sin extension,
        .sqlite o .sqlite3) en la misma carpeta, se usa esa."""
        principal = os.path.join(self.directorio, NOMBRE_BASE_DATOS)
        if not os.path.exists(principal):
            for alternativo in NOMBRES_ALTERNATIVOS_BASE_DATOS:
                ruta = os.path.join(self.directorio, alternativo)
                if os.path.isfile(ruta) and os.path.getsize(ruta) > 0:
                    return ruta
        return principal

    @property
    def ruta_programa(self) -> str:
        """PROGRAMA.txt; si no existe pero hay un archivo llamado PROGRAMA (sin extension), se usa ese."""
        principal = os.path.join(self.directorio, NOMBRE_PROGRAMA)
        sin_extension = os.path.join(self.directorio, "PROGRAMA")
        if not os.path.exists(principal) and os.path.isfile(sin_extension):
            return sin_extension
        return principal

    @property
    def ruta_ejemplos(self) -> str:
        return os.path.join(directorio_programa(), "recursos", "canciones_ejemplo.txt")

    @property
    def ruta_programa_ejemplo(self) -> str:
        return os.path.join(directorio_programa(), "PROGRAMA.txt")

    @property
    def directorio_exportacion(self) -> str:
        ruta = os.path.join(self.directorio, "exportaciones")
        os.makedirs(ruta, exist_ok=True)
        return ruta

    @property
    def directorio_modelos(self) -> str:
        return os.path.join(directorio_programa(), "modelos")

    # ---------------------------------------------------------- lectura/escritura
    def cargar(self) -> None:
        if not os.path.exists(self.ruta):
            self.guardar()
            return
        try:
            with open(self.ruta, encoding="utf-8") as archivo:
                leidos = json.load(archivo)
        except (OSError, ValueError):
            # Archivo danado: se conserva una copia y se regeneran los valores.
            try:
                os.replace(self.ruta, self.ruta + ".danado")
            except OSError:
                pass
            self.guardar()
            return
        for clave, valor in leidos.items():
            if clave in VALORES_POR_DEFECTO:
                self.valores[clave] = valor

    def guardar(self) -> None:
        with _candado:
            temporal = self.ruta + ".tmp"
            with open(temporal, "w", encoding="utf-8") as archivo:
                json.dump(self.valores, archivo, indent=2, ensure_ascii=False)
            os.replace(temporal, self.ruta)

    def __getitem__(self, clave: str) -> Any:
        return self.valores.get(clave, VALORES_POR_DEFECTO.get(clave))

    def __setitem__(self, clave: str, valor: Any) -> None:
        self.valores[clave] = valor

    def obtener_entero(self, clave: str, minimo: int = 1) -> int:
        try:
            return max(minimo, int(self[clave]))
        except (TypeError, ValueError):
            return int(VALORES_POR_DEFECTO[clave])

    def obtener_real(self, clave: str) -> float:
        try:
            return float(self[clave])
        except (TypeError, ValueError):
            return float(VALORES_POR_DEFECTO[clave])

    def actualizar(self, cambios: dict[str, Any]) -> list[str]:
        """Aplica cambios validando el tipo de cada valor; devuelve los errores encontrados."""
        errores = []
        for clave, valor in cambios.items():
            if clave not in VALORES_POR_DEFECTO:
                errores.append(f"Opcion desconocida: {clave}")
                continue
            por_defecto = VALORES_POR_DEFECTO[clave]
            try:
                if isinstance(por_defecto, bool):
                    if isinstance(valor, str):
                        valor = valor.strip().lower() in ("1", "si", "sí", "true", "s", "verdadero")
                    else:
                        valor = bool(valor)
                elif isinstance(por_defecto, int):
                    valor = int(valor)
                elif isinstance(por_defecto, float):
                    valor = float(valor)
                elif por_defecto is None:
                    valor = None if valor in ("", None) else valor
                else:
                    valor = str(valor)
            except (TypeError, ValueError):
                errores.append(f"Valor invalido para {clave}: {valor!r}")
                continue
            self.valores[clave] = valor
        self.guardar()
        return errores
