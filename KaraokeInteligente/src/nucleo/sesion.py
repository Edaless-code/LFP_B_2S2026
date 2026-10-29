"""Sesion de karaoke: que cancion se canta, en que linea va y que tecla se presiono.

La misma sesion la usan la consola, la interfaz grafica y el modo automatico
(que llama a los mismos metodos que las teclas).

Teclas del enunciado (se conservan las letras sugeridas):

    c  continuar con la linea siguiente
    f  finalizar el uso (termina la sesion despues de n canciones)
    r  repetir la misma cancion desde el inicio
    i  linea "igual": el cantante repite la linea en la que va
    i  ignorar: suspender el proceso hasta nueva orden (afinando, ejercicios de voz)
    s  seguir, despues de ignorar

Como el enunciado asigna la letra i a dos acciones, se resolvio asi
(suposicion documentada en el manual tecnico):

    - i una vez mientras se canta una linea -> "igual" (la linea se queda en pantalla)
    - i otra vez sobre la misma linea      -> "ignorar" (se suspende hasta presionar s)
    - i cuando no se esta cantando una linea (al inicio, entre canciones o al final)
      -> "ignorar" directamente

Las dos acciones dejan la misma linea en pantalla, asi que la primera i nunca
hace dano aunque la intencion fuera ignorar.

Teclas adicionales: a (linea anterior), n (siguiente cancion del programa),
b (buscar otra cancion) y ? (ayuda).
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from nucleo.modelos import Cancion

SIN_CANCION = "sin_cancion"
CANTANDO = "cantando"
SUSPENDIDA = "suspendida"
CANCION_TERMINADA = "cancion_terminada"
FINALIZADA = "finalizada"

TECLAS_KARAOKE = (
    ("c", "Continuar con la línea siguiente"),
    ("i", "Igual: el cantante repite la línea (una segunda i = ignorar)"),
    ("s", "Seguir después de ignorar"),
    ("r", "Repetir la misma canción desde el inicio"),
    ("f", "Finalizar la sesión de karaoke"),
    ("a", "Regresar a la línea anterior (adicional)"),
    ("n", "Pasar a la siguiente canción del PROGRAMA (adicional)"),
    ("b", "Buscar otra canción (adicional)"),
    ("?", "Mostrar esta ayuda (adicional)"),
)


@dataclass
class Resultado:
    """Lo que paso al ejecutar una accion; la interfaz lo muestra como aviso."""

    accion: str
    mensaje: str = ""
    ok: bool = True


@dataclass
class Interpretacion:
    """Una cancion cantada dentro de la sesion (las repeticiones cuentan aparte)."""

    codigo: int
    nombre: str
    completada: bool = False
    repeticion: int = 0


@dataclass
class ResumenSesion:
    modo: str
    interpretaciones: list[Interpretacion] = field(default_factory=list)
    duracion_segundos: float = 0.0

    @property
    def completadas(self) -> int:
        return sum(1 for i in self.interpretaciones if i.completada)


class SesionKaraoke:
    def __init__(self, repositorio, programa=None, modo: str = "manual", reloj=time.monotonic) -> None:
        self.repositorio = repositorio
        self.programa = programa
        self.modo = modo
        self.reloj = reloj
        self.estado = SIN_CANCION
        self.cancion: Cancion | None = None
        self.ultima_cancion: Cancion | None = None
        self.indice = 0
        self.repeticiones_linea = 0
        self.repeticiones_cancion = 0
        self.interpretaciones: list[Interpretacion] = []
        self.id_sesion: int | None = None
        self._id_historial: int | None = None
        self._estado_antes_de_suspender = SIN_CANCION
        self._ultima_accion = ""
        self._inicio_sesion = reloj()
        self._inicio_linea = reloj()
        self._pausado_desde: float | None = None
        # Segundos que tardo el cantante en cada linea; sirven para medir su ritmo.
        self.duraciones: list[float] = []

    # =============================================================== consulta
    @property
    def activa(self) -> bool:
        return self.estado != FINALIZADA

    @property
    def cantando(self) -> bool:
        return self.estado == CANTANDO

    @property
    def suspendida(self) -> bool:
        return self.estado == SUSPENDIDA

    @property
    def total_lineas(self) -> int:
        return len(self.cancion.lineas) if self.cancion else 0

    @property
    def numero_linea(self) -> int:
        """Numero de la linea actual contando desde 1."""
        return self.indice + 1 if self.cancion else 0

    @property
    def linea_actual(self) -> str:
        if not self.cancion or not self.cancion.lineas:
            return ""
        return self.cancion.lineas[self.indice]

    def lineas_anteriores(self, cantidad: int = 1) -> list[str]:
        if not self.cancion:
            return []
        return self.cancion.lineas[max(0, self.indice - cantidad) : self.indice]

    def lineas_siguientes(self, cantidad: int = 2) -> list[str]:
        if not self.cancion:
            return []
        return self.cancion.lineas[self.indice + 1 : self.indice + 1 + cantidad]

    @property
    def progreso(self) -> float:
        """Avance de la cancion de 0 a 1 (la linea actual cuenta como iniciada)."""
        if not self.total_lineas:
            return 0.0
        return self.indice / self.total_lineas

    @property
    def es_ultima_linea(self) -> bool:
        return bool(self.cancion) and self.indice >= self.total_lineas - 1

    def segundos_por_linea(self) -> float | None:
        """Ritmo del cantante: promedio de las ultimas lineas cantadas."""
        if not self.duraciones:
            return None
        recientes = self.duraciones[-6:]
        return sum(recientes) / len(recientes)

    def segundos_en_linea(self) -> float:
        if self._pausado_desde is not None:
            return self._pausado_desde - self._inicio_linea
        return self.reloj() - self._inicio_linea

    @property
    def canciones_cantadas(self) -> int:
        return sum(1 for i in self.interpretaciones if i.completada)

    # ================================================================ sesion
    def iniciar(self) -> int:
        self.id_sesion = self.repositorio.iniciar_sesion(self.modo)
        self._inicio_sesion = self.reloj()
        return self.id_sesion

    def finalizar(self) -> ResumenSesion:
        if self.estado == FINALIZADA:
            return self.resumen()
        if self.cancion is not None and self.estado in (CANTANDO, SUSPENDIDA):
            self._cerrar_interpretacion(completada=False)
        if self.id_sesion is not None:
            self.repositorio.finalizar_sesion(self.id_sesion)
        self.estado = FINALIZADA
        self._ultima_accion = "f"
        return self.resumen()

    def resumen(self) -> ResumenSesion:
        return ResumenSesion(self.modo, list(self.interpretaciones), self.reloj() - self._inicio_sesion)

    # ============================================================= canciones
    def cargar_cancion(self, codigo: int, linea: int = 0) -> Cancion | None:
        """Empieza (o se sincroniza con) una cancion en la linea indicada (desde 0)."""
        cancion = self.repositorio.obtener_cancion(codigo)
        if cancion is None or not cancion.lineas:
            return None
        if self.cancion is not None and self.estado in (CANTANDO, SUSPENDIDA):
            self._cerrar_interpretacion(completada=False)
        repeticion = 0
        if self.ultima_cancion is not None and self.ultima_cancion.codigo == codigo:
            repeticion = self.repeticiones_cancion + 1
        self.cancion = cancion
        self.ultima_cancion = cancion
        self.repeticiones_cancion = repeticion
        self.indice = max(0, min(linea, len(cancion.lineas) - 1))
        self.repeticiones_linea = 0
        self.duraciones = []
        self._abrir_interpretacion()
        self.estado = CANTANDO
        self._ultima_accion = "cargar"
        self._reiniciar_reloj_linea()
        return cancion

    def _abrir_interpretacion(self) -> None:
        assert self.cancion is not None
        self.interpretaciones.append(
            Interpretacion(self.cancion.codigo, self.cancion.nombre, repeticion=self.repeticiones_cancion)
        )
        self._id_historial = self.repositorio.registrar_inicio(
            self.id_sesion, self.cancion.codigo, self.cancion.nombre, self.modo
        )

    def _cerrar_interpretacion(self, completada: bool) -> None:
        if self.interpretaciones:
            self.interpretaciones[-1].completada = completada
        if self._id_historial is not None:
            self.repositorio.registrar_fin(self._id_historial, completada)
            self._id_historial = None
        if completada and self.programa is not None and self.cancion is not None:
            self.programa.marcar_cantada(self.cancion.codigo)

    def terminar_cancion(self, completada: bool = True) -> Resultado:
        if self.cancion is None:
            return Resultado("terminar", "No hay ninguna canción en curso.", ok=False)
        self._registrar_duracion()
        self._cerrar_interpretacion(completada)
        nombre = self.cancion.nombre
        self.cancion = None
        self.estado = CANCION_TERMINADA
        self._ultima_accion = "terminar"
        if completada:
            return Resultado("terminar", f"Terminó «{nombre}».")
        return Resultado("terminar", f"Se dejó de cantar «{nombre}».")

    # ================================================================ teclas
    def continuar(self) -> Resultado:
        """(c) Muestra la linea siguiente; despues de la ultima, termina la cancion."""
        if self.estado == SUSPENDIDA:
            return Resultado("c", "El proceso está suspendido: presione (s) para seguir.", ok=False)
        if self.estado != CANTANDO or self.cancion is None:
            return Resultado("c", "No hay ninguna canción en curso.", ok=False)
        if self.es_ultima_linea:
            return self.terminar_cancion(completada=True)
        self._registrar_duracion()
        self.indice += 1
        self.repeticiones_linea = 0
        self._ultima_accion = "c"
        self._reiniciar_reloj_linea()
        return Resultado("c")

    def igual(self) -> Resultado:
        """(i) El cantante repite la linea en la que va: se queda en pantalla."""
        if self.estado != CANTANDO:
            return Resultado("igual", "No hay ninguna línea en curso.", ok=False)
        self.repeticiones_linea += 1
        self._ultima_accion = "igual"
        self._reiniciar_reloj_linea()
        veces = self.repeticiones_linea + 1
        return Resultado("igual", f"Línea igual: se canta otra vez (vez {veces}). Otra (i) = ignorar.")

    def ignorar(self) -> Resultado:
        """(i) Suspende el proceso hasta nueva orden (s)."""
        if self.estado == SUSPENDIDA:
            return Resultado("ignorar", "Ya está suspendido: presione (s) para seguir.", ok=False)
        if self.estado == FINALIZADA:
            return Resultado("ignorar", "La sesión ya terminó.", ok=False)
        self._estado_antes_de_suspender = self.estado
        self.estado = SUSPENDIDA
        self._ultima_accion = "ignorar"
        self._pausado_desde = self.reloj()
        return Resultado("ignorar", "Proceso suspendido (el cantante afina o hace ejercicios). Presione (s) para seguir.")

    def tecla_i(self) -> Resultado:
        """La letra i del enunciado: igual la primera vez, ignorar la segunda (ver docstring del modulo)."""
        if self.estado == CANTANDO and self._ultima_accion != "igual":
            return self.igual()
        return self.ignorar()

    def seguir(self) -> Resultado:
        """(s) Reanuda el proceso despues de ignorar."""
        if self.estado != SUSPENDIDA:
            return Resultado("s", "El proceso no está suspendido.", ok=False)
        self.estado = self._estado_antes_de_suspender
        self._ultima_accion = "s"
        if self._pausado_desde is not None:
            # El tiempo en pausa no cuenta para medir el ritmo del cantante.
            self._inicio_linea += self.reloj() - self._pausado_desde
            self._pausado_desde = None
        return Resultado("s", "Se continúa con la letra.")

    def repetir_cancion(self) -> Resultado:
        """(r) Vuelve a empezar la cancion actual (o la ultima que se canto)."""
        if self.estado == SUSPENDIDA:
            return Resultado("r", "El proceso está suspendido: presione (s) para seguir.", ok=False)
        cancion = self.cancion or self.ultima_cancion
        if cancion is None:
            return Resultado("r", "Todavía no se ha cantado ninguna canción.", ok=False)
        self.cargar_cancion(cancion.codigo, 0)
        self._ultima_accion = "r"
        veces = self.repeticiones_cancion + 1
        return Resultado("r", f"Se repite «{cancion.nombre}» desde el inicio (vez {veces}).")

    def retroceder(self) -> Resultado:
        """(a) Regresa a la linea anterior (por si se avanzo antes de tiempo)."""
        if self.estado != CANTANDO or self.cancion is None:
            return Resultado("a", "No hay ninguna canción en curso.", ok=False)
        if self.indice == 0:
            return Resultado("a", "Ya está en la primera línea.", ok=False)
        self.indice -= 1
        self.repeticiones_linea = 0
        self._ultima_accion = "a"
        self._reiniciar_reloj_linea()
        return Resultado("a", "Se regresó a la línea anterior.")

    def ir_a_linea(self, indice: int) -> Resultado:
        """Salta a una linea (desde 0); lo usa el modo automatico para resincronizarse."""
        if self.estado != CANTANDO or self.cancion is None:
            return Resultado("ir", "No hay ninguna canción en curso.", ok=False)
        indice = max(0, min(indice, self.total_lineas - 1))
        if indice != self.indice:
            if indice > self.indice:
                self._registrar_duracion()
            self.indice = indice
            self.repeticiones_linea = 0
            self._reiniciar_reloj_linea()
        self._ultima_accion = "ir"
        return Resultado("ir")

    def siguiente_del_programa(self) -> Resultado:
        """(n) Deja la cancion actual y empieza la siguiente del PROGRAMA."""
        if self.estado == SUSPENDIDA:
            return Resultado("n", "El proceso está suspendido: presione (s) para seguir.", ok=False)
        if self.programa is None or not self.programa.activo:
            return Resultado("n", "No hay un PROGRAMA cargado (opción p del menú principal).", ok=False)
        siguiente = self.programa.siguiente()
        if siguiente is not None and self.cancion is not None and siguiente.codigo == self.cancion.codigo:
            siguiente = self.programa.saltar_siguiente()
        if siguiente is None or siguiente.codigo is None:
            return Resultado("n", "Ya no quedan canciones pendientes en el PROGRAMA.", ok=False)
        self.cargar_cancion(siguiente.codigo, 0)
        return Resultado("n", f"Siguiente del PROGRAMA: «{siguiente.nombre}».")

    def ejecutar_tecla(self, tecla: str) -> Resultado:
        """Traduce una tecla a su accion. Las teclas b y ? las resuelve la interfaz."""
        tecla = (tecla or "").strip().lower()[:1]
        acciones = {
            "c": self.continuar,
            "i": self.tecla_i,
            "s": self.seguir,
            "r": self.repetir_cancion,
            "a": self.retroceder,
            "n": self.siguiente_del_programa,
        }
        if tecla == "f":
            self.finalizar()
            return Resultado("f", "Sesión finalizada.")
        if tecla in acciones:
            return acciones[tecla]()
        return Resultado("desconocida", f"Tecla no válida: {tecla!r}. Presione ? para ver la ayuda.", ok=False)

    # ============================================================= auxiliares
    def _reiniciar_reloj_linea(self) -> None:
        self._inicio_linea = self.reloj()
        self._pausado_desde = self.reloj() if self.estado == SUSPENDIDA else None

    def _registrar_duracion(self) -> None:
        if self.estado == CANTANDO and self.repeticiones_linea == 0:
            duracion = self.segundos_en_linea()
            if 0.5 <= duracion <= 60:
                self.duraciones.append(duracion)
