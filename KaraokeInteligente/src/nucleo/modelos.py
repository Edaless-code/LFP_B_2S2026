"""Estructuras de datos compartidas por todos los modulos."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Cancion:
    codigo: int
    nombre: str
    lineas: list[str]
    artista: str = ""
    origen: str = "e"
    veces_cantada: int = 0
    fecha_alta: str = ""

    @property
    def total_lineas(self) -> int:
        return len(self.lineas)

    def titulo(self) -> str:
        return f"{self.nombre} - {self.artista}" if self.artista else self.nombre


@dataclass
class ResumenCancion:
    codigo: int
    nombre: str
    artista: str
    total_lineas: int
    veces_cantada: int = 0

    def titulo(self) -> str:
        return f"{self.nombre} - {self.artista}" if self.artista else self.nombre


@dataclass
class CancionTemporal:
    """Cancion capturada por el modo automatico, pendiente de revision."""

    id_temp: int
    nombre_sugerido: str
    lineas: list[str]
    fecha_captura: str = ""
    estado: str = "pendiente"


@dataclass
class Coincidencia:
    """Resultado de buscar un fragmento de letra en la base de datos."""

    codigo: int
    nombre: str
    puntaje: float
    linea_inicio: int
    linea_fin: int
    texto_linea: str = ""
    # Que tan avanzada esta la linea final (0 = inicio, 1 = ultima palabra)
    progreso_en_linea: float = 0.0
    por_titulo: bool = False

    @property
    def porcentaje(self) -> int:
        return int(round(self.puntaje * 100))


@dataclass
class ItemPrograma:
    posicion: int
    texto: str
    codigo: int | None = None
    nombre: str = ""
    estado: str = "pendiente"  # pendiente | cantada | saltada | no_encontrada

    @property
    def encontrada(self) -> bool:
        return self.codigo is not None


@dataclass
class ResultadoImportacion:
    agregadas: list[tuple[int, str]] = field(default_factory=list)
    omitidas: list[str] = field(default_factory=list)
    reemplazadas: list[tuple[int, str]] = field(default_factory=list)
    advertencias: list[str] = field(default_factory=list)
    errores: list[str] = field(default_factory=list)

    def resumen(self) -> str:
        partes = [f"{len(self.agregadas)} agregada(s)"]
        if self.reemplazadas:
            partes.append(f"{len(self.reemplazadas)} reemplazada(s)")
        if self.omitidas:
            partes.append(f"{len(self.omitidas)} omitida(s) por existir")
        if self.errores:
            partes.append(f"{len(self.errores)} con error")
        return ", ".join(partes)
