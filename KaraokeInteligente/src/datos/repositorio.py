"""Operaciones sobre las tablas de CANCIONES (altas, consultas, cambios y bajas)."""

from __future__ import annotations

import difflib
from typing import Iterable

from datos.base_datos import BaseDatos
from nucleo.modelos import Cancion, CancionTemporal, ItemPrograma, ResumenCancion
from nucleo.texto import normalizar


class Repositorio:
    def __init__(self, base: BaseDatos) -> None:
        self.base = base
        # Aumenta con cada cambio; el buscador lo usa para saber cuando reconstruir su indice.
        self.revision = 0

    @property
    def _conexion(self):
        return self.base.conexion

    def _cambio(self) -> None:
        self.revision += 1

    # ================================================================ canciones
    def contar_canciones(self) -> int:
        with self.base.candado:
            return self._conexion.execute("SELECT COUNT(*) FROM NOMBRES").fetchone()[0]

    def listar_canciones(self, desplazamiento: int = 0, limite: int | None = None) -> list[ResumenCancion]:
        consulta = (
            "SELECT n.codigo, n.nombre_cancion, n.artista, n.veces_cantada, "
            "(SELECT COUNT(*) FROM LETRAS l WHERE l.codigo = n.codigo) AS total "
            "FROM NOMBRES n ORDER BY n.codigo"
        )
        parametros: tuple = ()
        if limite is not None:
            consulta += " LIMIT ? OFFSET ?"
            parametros = (limite, desplazamiento)
        with self.base.candado:
            filas = self._conexion.execute(consulta, parametros).fetchall()
        return [
            ResumenCancion(f["codigo"], f["nombre_cancion"], f["artista"], f["total"], f["veces_cantada"])
            for f in filas
        ]

    def obtener_cancion(self, codigo: int) -> Cancion | None:
        with self.base.candado:
            fila = self._conexion.execute("SELECT * FROM NOMBRES WHERE codigo = ?", (codigo,)).fetchone()
            if fila is None:
                return None
            lineas = [
                f["linea"]
                for f in self._conexion.execute(
                    "SELECT linea FROM LETRAS WHERE codigo = ? ORDER BY numero_linea, rowid", (codigo,)
                )
            ]
        return Cancion(
            codigo=fila["codigo"],
            nombre=fila["nombre_cancion"],
            lineas=lineas,
            artista=fila["artista"],
            origen=fila["origen"],
            veces_cantada=fila["veces_cantada"],
            fecha_alta=fila["fecha_alta"],
        )

    def codigo_por_nombre(self, nombre: str) -> int | None:
        with self.base.candado:
            fila = self._conexion.execute(
                "SELECT codigo FROM NOMBRES WHERE nombre_normalizado = ? ORDER BY codigo LIMIT 1",
                (normalizar(nombre),),
            ).fetchone()
        return fila[0] if fila else None

    def buscar_por_nombre(self, texto: str, limite: int = 10) -> list[ResumenCancion]:
        """Busca por nombre: primero exacto, luego que contenga el texto y por ultimo parecido."""
        buscado = normalizar(texto)
        if not buscado:
            return []
        todas = self.listar_canciones()
        exactas = [c for c in todas if normalizar(c.nombre) == buscado]
        if exactas:
            return exactas[:limite]
        contienen = [c for c in todas if buscado in normalizar(c.nombre)]
        if contienen:
            return contienen[:limite]
        puntuadas = []
        for cancion in todas:
            puntaje = difflib.SequenceMatcher(None, buscado, normalizar(cancion.nombre)).ratio()
            if puntaje >= 0.6:
                puntuadas.append((puntaje, cancion))
        puntuadas.sort(key=lambda p: -p[0])
        return [c for _, c in puntuadas[:limite]]

    def resolver(self, texto: str) -> list[ResumenCancion]:
        """Interpreta el texto como codigo (si es numero) o como nombre de cancion."""
        texto = texto.strip()
        if not texto:
            return []
        if texto.isdigit():
            cancion = self.obtener_cancion(int(texto))
            if cancion:
                return [
                    ResumenCancion(
                        cancion.codigo, cancion.nombre, cancion.artista, cancion.total_lineas, cancion.veces_cantada
                    )
                ]
        return self.buscar_por_nombre(texto)

    def agregar_cancion(self, nombre: str, lineas: Iterable[str], artista: str = "", origen: str = "e") -> int:
        nombre = " ".join(nombre.split())
        lineas = [" ".join(l.split()) for l in lineas if l and l.strip()]
        if not nombre:
            raise ValueError("El nombre de la cancion no puede estar vacio.")
        if not lineas:
            raise ValueError("La cancion debe tener al menos una linea de letra.")
        with self.base.candado, self._conexion:
            cursor = self._conexion.execute(
                "INSERT INTO NOMBRES (nombre_cancion, nombre_normalizado, artista, origen) VALUES (?, ?, ?, ?)",
                (nombre, normalizar(nombre), artista.strip(), origen),
            )
            codigo = cursor.lastrowid
            self._insertar_lineas(codigo, lineas)
        self._cambio()
        return int(codigo)

    def _insertar_lineas(self, codigo: int, lineas: list[str]) -> None:
        self._conexion.executemany(
            "INSERT INTO LETRAS (codigo, numero_linea, linea, linea_normalizada) VALUES (?, ?, ?, ?)",
            [(codigo, numero, linea, normalizar(linea)) for numero, linea in enumerate(lineas, start=1)],
        )

    def reemplazar_letra(self, codigo: int, lineas: Iterable[str]) -> None:
        lineas = [" ".join(l.split()) for l in lineas if l and l.strip()]
        if not lineas:
            raise ValueError("La cancion debe tener al menos una linea de letra.")
        with self.base.candado, self._conexion:
            self._conexion.execute("DELETE FROM LETRAS WHERE codigo = ?", (codigo,))
            self._insertar_lineas(codigo, lineas)
        self._cambio()

    def renombrar(self, codigo: int, nombre: str, artista: str | None = None) -> None:
        nombre = " ".join(nombre.split())
        if not nombre:
            raise ValueError("El nombre de la cancion no puede estar vacio.")
        with self.base.candado, self._conexion:
            if artista is None:
                self._conexion.execute(
                    "UPDATE NOMBRES SET nombre_cancion = ?, nombre_normalizado = ? WHERE codigo = ?",
                    (nombre, normalizar(nombre), codigo),
                )
            else:
                self._conexion.execute(
                    "UPDATE NOMBRES SET nombre_cancion = ?, nombre_normalizado = ?, artista = ? WHERE codigo = ?",
                    (nombre, normalizar(nombre), artista.strip(), codigo),
                )
        self._cambio()

    def borrar_cancion(self, codigo: int) -> bool:
        with self.base.candado, self._conexion:
            self._conexion.execute("DELETE FROM LETRAS WHERE codigo = ?", (codigo,))
            cursor = self._conexion.execute("DELETE FROM NOMBRES WHERE codigo = ?", (codigo,))
        self._cambio()
        return cursor.rowcount > 0

    def todas_las_lineas(self) -> list[tuple[int, str, int, str]]:
        """(codigo, nombre, indice_linea desde 0, linea) de toda la base, para el indice de busqueda."""
        with self.base.candado:
            filas = self._conexion.execute(
                "SELECT n.codigo, n.nombre_cancion, l.linea FROM LETRAS l "
                "JOIN NOMBRES n ON n.codigo = l.codigo ORDER BY n.codigo, l.numero_linea, l.rowid"
            ).fetchall()
        resultado = []
        ultimo, indice = None, 0
        for fila in filas:
            if fila["codigo"] != ultimo:
                ultimo, indice = fila["codigo"], 0
            resultado.append((fila["codigo"], fila["nombre_cancion"], indice, fila["linea"]))
            indice += 1
        return resultado

    def nombres(self) -> list[tuple[int, str]]:
        with self.base.candado:
            return [
                (f["codigo"], f["nombre_cancion"])
                for f in self._conexion.execute("SELECT codigo, nombre_cancion FROM NOMBRES ORDER BY codigo")
            ]

    def todas_las_canciones(self) -> list[Cancion]:
        canciones = []
        for codigo, _ in self.nombres():
            cancion = self.obtener_cancion(codigo)
            if cancion:
                canciones.append(cancion)
        return canciones

    # ======================================================= canciones capturadas
    def crear_temporal(self, nombre_sugerido: str) -> int:
        with self.base.candado, self._conexion:
            cursor = self._conexion.execute(
                "INSERT INTO NOMBRES_TEMP (nombre_sugerido, estado) VALUES (?, 'capturando')", (nombre_sugerido,)
            )
        return int(cursor.lastrowid)

    def agregar_linea_temporal(self, id_temp: int, linea: str, confianza: float = 0.0) -> None:
        with self.base.candado, self._conexion:
            siguiente = self._conexion.execute(
                "SELECT COALESCE(MAX(numero_linea), 0) + 1 FROM LETRAS_TEMP WHERE id_temp = ?", (id_temp,)
            ).fetchone()[0]
            self._conexion.execute(
                "INSERT INTO LETRAS_TEMP (id_temp, numero_linea, linea, confianza) VALUES (?, ?, ?, ?)",
                (id_temp, siguiente, linea, confianza),
            )

    def cerrar_temporal(self, id_temp: int, nombre_sugerido: str | None = None) -> None:
        """Marca la captura como terminada; si no tiene lineas, la elimina."""
        with self.base.candado, self._conexion:
            total = self._conexion.execute(
                "SELECT COUNT(*) FROM LETRAS_TEMP WHERE id_temp = ?", (id_temp,)
            ).fetchone()[0]
            if total == 0:
                self._conexion.execute("DELETE FROM NOMBRES_TEMP WHERE id_temp = ?", (id_temp,))
                return
            if nombre_sugerido:
                self._conexion.execute(
                    "UPDATE NOMBRES_TEMP SET nombre_sugerido = ?, estado = 'pendiente' WHERE id_temp = ?",
                    (nombre_sugerido, id_temp),
                )
            else:
                self._conexion.execute("UPDATE NOMBRES_TEMP SET estado = 'pendiente' WHERE id_temp = ?", (id_temp,))

    def listar_temporales(self) -> list[CancionTemporal]:
        with self.base.candado:
            filas = self._conexion.execute("SELECT * FROM NOMBRES_TEMP ORDER BY id_temp").fetchall()
        return [self.obtener_temporal(f["id_temp"]) for f in filas]  # type: ignore[misc]

    def obtener_temporal(self, id_temp: int) -> CancionTemporal | None:
        with self.base.candado:
            fila = self._conexion.execute("SELECT * FROM NOMBRES_TEMP WHERE id_temp = ?", (id_temp,)).fetchone()
            if fila is None:
                return None
            lineas = [
                f["linea"]
                for f in self._conexion.execute(
                    "SELECT linea FROM LETRAS_TEMP WHERE id_temp = ? ORDER BY numero_linea", (id_temp,)
                )
            ]
        return CancionTemporal(fila["id_temp"], fila["nombre_sugerido"], lineas, fila["fecha_captura"], fila["estado"])

    def actualizar_temporal(self, id_temp: int, nombre: str, lineas: Iterable[str]) -> None:
        lineas = [" ".join(l.split()) for l in lineas if l and l.strip()]
        with self.base.candado, self._conexion:
            self._conexion.execute(
                "UPDATE NOMBRES_TEMP SET nombre_sugerido = ? WHERE id_temp = ?", (nombre.strip() or "Sin nombre", id_temp)
            )
            self._conexion.execute("DELETE FROM LETRAS_TEMP WHERE id_temp = ?", (id_temp,))
            self._conexion.executemany(
                "INSERT INTO LETRAS_TEMP (id_temp, numero_linea, linea) VALUES (?, ?, ?)",
                [(id_temp, n, l) for n, l in enumerate(lineas, start=1)],
            )

    def promover_temporal(self, id_temp: int, nombre: str, lineas: Iterable[str], artista: str = "") -> int:
        """Pasa una cancion capturada a las tablas permanentes NOMBRES y LETRAS."""
        codigo = self.agregar_cancion(nombre, lineas, artista, origen="a")
        self.descartar_temporal(id_temp)
        return codigo

    def descartar_temporal(self, id_temp: int) -> None:
        with self.base.candado, self._conexion:
            self._conexion.execute("DELETE FROM LETRAS_TEMP WHERE id_temp = ?", (id_temp,))
            self._conexion.execute("DELETE FROM NOMBRES_TEMP WHERE id_temp = ?", (id_temp,))

    def contar_temporales(self) -> int:
        with self.base.candado:
            return self._conexion.execute("SELECT COUNT(*) FROM NOMBRES_TEMP").fetchone()[0]

    # ================================================================== programa
    def guardar_programa(self, items: list[ItemPrograma]) -> None:
        with self.base.candado, self._conexion:
            self._conexion.execute("DELETE FROM PROGRAMA")
            self._conexion.executemany(
                "INSERT INTO PROGRAMA (posicion, texto, codigo, estado) VALUES (?, ?, ?, ?)",
                [(i.posicion, i.texto, i.codigo, i.estado) for i in items],
            )

    def cargar_programa(self) -> list[ItemPrograma]:
        with self.base.candado:
            filas = self._conexion.execute(
                "SELECT p.posicion, p.texto, p.codigo, p.estado, n.nombre_cancion FROM PROGRAMA p "
                "LEFT JOIN NOMBRES n ON n.codigo = p.codigo ORDER BY p.posicion"
            ).fetchall()
        return [
            ItemPrograma(f["posicion"], f["texto"], f["codigo"], f["nombre_cancion"] or "", f["estado"]) for f in filas
        ]

    # ================================================================= historial
    def iniciar_sesion(self, modo: str) -> int:
        with self.base.candado, self._conexion:
            cursor = self._conexion.execute("INSERT INTO SESIONES (modo) VALUES (?)", (modo,))
        return int(cursor.lastrowid)

    def finalizar_sesion(self, id_sesion: int) -> None:
        with self.base.candado, self._conexion:
            self._conexion.execute(
                "UPDATE SESIONES SET fin = datetime('now', 'localtime') WHERE id_sesion = ?", (id_sesion,)
            )

    def registrar_inicio(self, id_sesion: int | None, codigo: int | None, nombre: str, modo: str) -> int:
        with self.base.candado, self._conexion:
            cursor = self._conexion.execute(
                "INSERT INTO HISTORIAL (id_sesion, codigo, nombre_cancion, modo) VALUES (?, ?, ?, ?)",
                (id_sesion, codigo, nombre, modo),
            )
        return int(cursor.lastrowid)

    def registrar_fin(self, id_historial: int, completada: bool) -> None:
        with self.base.candado, self._conexion:
            self._conexion.execute(
                "UPDATE HISTORIAL SET fin = datetime('now', 'localtime'), completada = ? WHERE id = ?",
                (1 if completada else 0, id_historial),
            )
            if completada:
                self._conexion.execute(
                    "UPDATE NOMBRES SET veces_cantada = veces_cantada + 1 WHERE codigo = "
                    "(SELECT codigo FROM HISTORIAL WHERE id = ?)",
                    (id_historial,),
                )

    def estadisticas(self) -> dict:
        with self.base.candado:
            c = self._conexion
            return {
                "canciones": c.execute("SELECT COUNT(*) FROM NOMBRES").fetchone()[0],
                "lineas": c.execute("SELECT COUNT(*) FROM LETRAS").fetchone()[0],
                "sesiones": c.execute("SELECT COUNT(*) FROM SESIONES").fetchone()[0],
                "interpretaciones": c.execute("SELECT COUNT(*) FROM HISTORIAL").fetchone()[0],
                "pendientes": c.execute("SELECT COUNT(*) FROM NOMBRES_TEMP").fetchone()[0],
                "mas_cantadas": [
                    (f[0], f[1], f[2])
                    for f in c.execute(
                        "SELECT codigo, nombre_cancion, veces_cantada FROM NOMBRES WHERE veces_cantada > 0 "
                        "ORDER BY veces_cantada DESC, nombre_cancion LIMIT 10"
                    )
                ],
                "recientes": [
                    (f[0], f[1], f[2], bool(f[3]))
                    for f in c.execute(
                        "SELECT inicio, nombre_cancion, modo, completada FROM HISTORIAL ORDER BY id DESC LIMIT 15"
                    )
                ],
            }
