"""Creacion y preparacion de la base de datos SQLite "CANCIONES".

Al iniciar se detecta si el archivo CANCIONES.db existe:
- si no existe, se crea con todas las tablas;
- si existe, se verifica su integridad, se crean las tablas que falten y se
  agregan las columnas nuevas (por ejemplo, si la base fue creada solo con los
  campos minimos del enunciado).
"""

from __future__ import annotations

import os
import sqlite3
import threading

from nucleo.texto import normalizar

VERSION_ESQUEMA = 1

# Tabla -> sentencia de creacion. NOMBRES y LETRAS son las del enunciado; el
# resto son tablas agregadas (documentadas en el manual tecnico).
TABLAS = {
    "NOMBRES": """
        CREATE TABLE IF NOT EXISTS NOMBRES (
            codigo              INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_cancion      TEXT    NOT NULL,
            nombre_normalizado  TEXT    NOT NULL DEFAULT '',
            artista             TEXT    NOT NULL DEFAULT '',
            origen              TEXT    NOT NULL DEFAULT 'e',
            fecha_alta          TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
            veces_cantada       INTEGER NOT NULL DEFAULT 0
        )""",
    "LETRAS": """
        CREATE TABLE IF NOT EXISTS LETRAS (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo              INTEGER NOT NULL REFERENCES NOMBRES(codigo) ON DELETE CASCADE,
            numero_linea        INTEGER NOT NULL DEFAULT 0,
            linea               TEXT    NOT NULL,
            linea_normalizada   TEXT    NOT NULL DEFAULT ''
        )""",
    "NOMBRES_TEMP": """
        CREATE TABLE IF NOT EXISTS NOMBRES_TEMP (
            id_temp             INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_sugerido     TEXT    NOT NULL,
            fecha_captura       TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
            estado              TEXT    NOT NULL DEFAULT 'pendiente'
        )""",
    "LETRAS_TEMP": """
        CREATE TABLE IF NOT EXISTS LETRAS_TEMP (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            id_temp             INTEGER NOT NULL REFERENCES NOMBRES_TEMP(id_temp) ON DELETE CASCADE,
            numero_linea        INTEGER NOT NULL,
            linea               TEXT    NOT NULL,
            confianza           REAL    NOT NULL DEFAULT 0
        )""",
    "PROGRAMA": """
        CREATE TABLE IF NOT EXISTS PROGRAMA (
            posicion            INTEGER PRIMARY KEY,
            texto               TEXT    NOT NULL,
            codigo              INTEGER REFERENCES NOMBRES(codigo) ON DELETE SET NULL,
            estado              TEXT    NOT NULL DEFAULT 'pendiente'
        )""",
    "SESIONES": """
        CREATE TABLE IF NOT EXISTS SESIONES (
            id_sesion           INTEGER PRIMARY KEY AUTOINCREMENT,
            modo                TEXT    NOT NULL,
            inicio              TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
            fin                 TEXT
        )""",
    "HISTORIAL": """
        CREATE TABLE IF NOT EXISTS HISTORIAL (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            id_sesion           INTEGER REFERENCES SESIONES(id_sesion) ON DELETE CASCADE,
            codigo              INTEGER,
            nombre_cancion      TEXT    NOT NULL,
            modo                TEXT    NOT NULL,
            inicio              TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
            fin                 TEXT,
            completada          INTEGER NOT NULL DEFAULT 0
        )""",
    "INFO_BD": """
        CREATE TABLE IF NOT EXISTS INFO_BD (
            clave               TEXT PRIMARY KEY,
            valor               TEXT
        )""",
}

INDICES = (
    "CREATE INDEX IF NOT EXISTS ix_letras_codigo ON LETRAS(codigo, numero_linea)",
    "CREATE INDEX IF NOT EXISTS ix_nombres_normalizado ON NOMBRES(nombre_normalizado)",
    "CREATE INDEX IF NOT EXISTS ix_letras_temp ON LETRAS_TEMP(id_temp, numero_linea)",
)

# Columnas que se agregan si la tabla ya existia sin ellas.
COLUMNAS_EXTRA = {
    "NOMBRES": (
        ("nombre_normalizado", "TEXT NOT NULL DEFAULT ''"),
        ("artista", "TEXT NOT NULL DEFAULT ''"),
        ("origen", "TEXT NOT NULL DEFAULT 'e'"),
        ("fecha_alta", "TEXT NOT NULL DEFAULT ''"),
        ("veces_cantada", "INTEGER NOT NULL DEFAULT 0"),
    ),
    "LETRAS": (
        ("numero_linea", "INTEGER NOT NULL DEFAULT 0"),
        ("linea_normalizada", "TEXT NOT NULL DEFAULT ''"),
    ),
}


class BaseDatos:
    """Conexion unica a CANCIONES.db compartida por la aplicacion."""

    def __init__(self, ruta: str) -> None:
        self.ruta = ruta
        self.candado = threading.RLock()
        self.existia = os.path.exists(ruta) and os.path.getsize(ruta) > 0
        self.mensajes: list[str] = []
        self.tablas_creadas: list[str] = []
        self.conexion = self._abrir()
        self._preparar()

    # ------------------------------------------------------------------ apertura
    def _conectar(self) -> sqlite3.Connection:
        directorio = os.path.dirname(self.ruta)
        if directorio:
            os.makedirs(directorio, exist_ok=True)
        conexion = sqlite3.connect(self.ruta, check_same_thread=False)
        conexion.row_factory = sqlite3.Row
        conexion.execute("PRAGMA foreign_keys = ON")
        return conexion

    def _abrir(self) -> sqlite3.Connection:
        try:
            conexion = self._conectar()
            if self.existia:
                resultado = conexion.execute("PRAGMA quick_check").fetchone()[0]
                if resultado != "ok":
                    raise sqlite3.DatabaseError(resultado)
            return conexion
        except sqlite3.DatabaseError as error:
            # El archivo existe pero no es una base valida: se respalda y se crea otra.
            respaldo = self.ruta + ".danada"
            try:
                conexion.close()  # type: ignore[possibly-undefined]
            except Exception:
                pass
            os.replace(self.ruta, respaldo)
            self.mensajes.append(
                f"La base de datos estaba danada ({error}); se respaldo como {os.path.basename(respaldo)} "
                "y se creo una nueva."
            )
            self.existia = False
            return self._conectar()

    def _preparar(self) -> None:
        with self.candado, self.conexion:
            existentes = {
                fila[0]
                for fila in self.conexion.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
            }
            for tabla, sentencia in TABLAS.items():
                if tabla not in existentes:
                    self.tablas_creadas.append(tabla)
                self.conexion.execute(sentencia)
            self._agregar_columnas_faltantes()
            for sentencia in INDICES:
                self.conexion.execute(sentencia)
            self.conexion.execute(
                "INSERT OR REPLACE INTO INFO_BD (clave, valor) VALUES ('version_esquema', ?)",
                (str(VERSION_ESQUEMA),),
            )
        if not self.existia:
            self.mensajes.append(f"No existia la base de datos CANCIONES: se creo con {len(TABLAS)} tablas.")
        elif self.tablas_creadas:
            self.mensajes.append(
                "Base de datos CANCIONES encontrada; se agregaron las tablas: " + ", ".join(self.tablas_creadas)
            )
        else:
            self.mensajes.append("Base de datos CANCIONES encontrada y lista para usarse.")

    def _agregar_columnas_faltantes(self) -> None:
        for tabla, columnas in COLUMNAS_EXTRA.items():
            actuales = {fila[1] for fila in self.conexion.execute(f"PRAGMA table_info({tabla})")}
            agregadas = []
            for nombre, definicion in columnas:
                if nombre not in actuales:
                    self.conexion.execute(f"ALTER TABLE {tabla} ADD COLUMN {nombre} {definicion}")
                    agregadas.append(nombre)
            if agregadas:
                self.mensajes.append(f"Se agregaron a {tabla} las columnas: {', '.join(agregadas)}")
        # Completa los valores derivados de bases creadas por otros programas.
        for fila in self.conexion.execute(
            "SELECT codigo, nombre_cancion FROM NOMBRES WHERE nombre_normalizado = ''"
        ).fetchall():
            self.conexion.execute(
                "UPDATE NOMBRES SET nombre_normalizado = ? WHERE codigo = ?",
                (normalizar(fila["nombre_cancion"]), fila["codigo"]),
            )
        for fila in self.conexion.execute(
            "SELECT rowid, linea FROM LETRAS WHERE linea_normalizada = ''"
        ).fetchall():
            self.conexion.execute(
                "UPDATE LETRAS SET linea_normalizada = ? WHERE rowid = ?", (normalizar(fila["linea"]), fila[0])
            )
        sin_numero = self.conexion.execute(
            "SELECT DISTINCT codigo FROM LETRAS WHERE numero_linea = 0"
        ).fetchall()
        for fila in sin_numero:
            filas = self.conexion.execute(
                "SELECT rowid FROM LETRAS WHERE codigo = ? ORDER BY numero_linea, rowid", (fila[0],)
            ).fetchall()
            for numero, linea in enumerate(filas, start=1):
                self.conexion.execute("UPDATE LETRAS SET numero_linea = ? WHERE rowid = ?", (numero, linea[0]))

    # ------------------------------------------------------------------ utilidades
    def estado(self) -> str:
        return " ".join(self.mensajes)

    def cerrar(self) -> None:
        with self.candado:
            self.conexion.close()
