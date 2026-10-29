"""Programa tentativo del cantante (archivo PROGRAMA).

El programa es una guia, no una obligacion:
- "siguiente" es la primera cancion pendiente de la lista;
- si se canta una cancion que esta mas adelante, las pendientes anteriores se
  marcan como saltadas y el programa continua despues de la cantada;
- repetir una cancion no altera el programa;
- se puede abandonar en cualquier momento (simplemente se busca otra cancion).

El estado de cada cancion se guarda en la tabla PROGRAMA para conservarlo si el
programa se cierra a mitad de la sesion.

Formato del archivo PROGRAMA: un nombre de cancion (o un codigo) por renglon, en
el orden en que se piensan cantar. Se aceptan numeros de orden ("1.", "2)",
"3 -") y comentarios que empiezan con "#".
"""

from __future__ import annotations

from nucleo.alimentador import leer_archivo_texto
from nucleo.modelos import ItemPrograma

BONO_SIGUIENTE = 0.12
BONO_POSTERIOR = 0.05


class ProgramaCantante:
    def __init__(self, repositorio) -> None:
        self.repositorio = repositorio
        self.items: list[ItemPrograma] = []

    # ================================================================ carga
    def cargar_guardado(self) -> None:
        self.items = self.repositorio.cargar_programa()
        self.resolver_pendientes()

    def cargar_desde_texto(self, texto: str) -> list[ItemPrograma]:
        return self.cargar_nombres(interpretar_programa(texto))

    def cargar_desde_archivo(self, ruta: str) -> list[ItemPrograma]:
        return self.cargar_desde_texto(leer_archivo_texto(ruta))

    def cargar_nombres(self, nombres: list[str]) -> list[ItemPrograma]:
        self.items = []
        for posicion, texto in enumerate(nombres, start=1):
            item = ItemPrograma(posicion=posicion, texto=texto)
            self._resolver(item)
            self.items.append(item)
        self._guardar()
        return self.items

    def guardar_archivo(self, ruta: str, nombres: list[str]) -> list[ItemPrograma]:
        """Escribe el archivo PROGRAMA con los nombres tecleados y lo carga."""
        escribir_programa(ruta, nombres)
        return self.cargar_nombres(nombres)

    def quitar(self) -> None:
        self.items = []
        self._guardar()

    def reiniciar(self) -> None:
        for item in self.items:
            if item.estado in ("cantada", "saltada"):
                item.estado = "pendiente"
        self.resolver_pendientes()
        self._guardar()

    def _resolver(self, item: ItemPrograma) -> None:
        encontradas = self.repositorio.resolver(item.texto)
        if encontradas:
            item.codigo = encontradas[0].codigo
            item.nombre = encontradas[0].nombre
            if item.estado == "no_encontrada":
                item.estado = "pendiente"
        else:
            item.codigo = None
            item.nombre = ""
            item.estado = "no_encontrada"

    def resolver_pendientes(self) -> None:
        """Vuelve a buscar las canciones (por ejemplo, despues de agregar o borrar canciones)."""
        cambio = False
        for item in self.items:
            antes = (item.codigo, item.estado)
            if item.codigo is None or item.estado == "no_encontrada":
                self._resolver(item)
            elif self.repositorio.obtener_cancion(item.codigo) is None:
                self._resolver(item)
            cambio = cambio or antes != (item.codigo, item.estado)
        if cambio:
            self._guardar()

    def _guardar(self) -> None:
        self.repositorio.guardar_programa(self.items)

    # ============================================================== consulta
    @property
    def activo(self) -> bool:
        return any(i.encontrada for i in self.items)

    def siguiente(self) -> ItemPrograma | None:
        for item in self.items:
            if item.estado == "pendiente" and item.encontrada:
                return item
        return None

    def posteriores(self, cantidad: int = 3) -> list[ItemPrograma]:
        pendientes = [i for i in self.items if i.estado == "pendiente" and i.encontrada]
        return pendientes[:cantidad]

    def bonificaciones(self) -> dict[int, float]:
        """Ventaja en la busqueda para las canciones que tocan segun el programa."""
        bonos: dict[int, float] = {}
        for numero, item in enumerate(self.posteriores(3)):
            if item.codigo is not None and item.codigo not in bonos:
                bonos[item.codigo] = BONO_SIGUIENTE if numero == 0 else BONO_POSTERIOR
        return bonos

    def contar(self) -> dict[str, int]:
        conteo = {"total": len(self.items), "pendiente": 0, "cantada": 0, "saltada": 0, "no_encontrada": 0}
        for item in self.items:
            conteo[item.estado] = conteo.get(item.estado, 0) + 1
        return conteo

    def resumen(self) -> str:
        if not self.items:
            return "sin programa"
        conteo = self.contar()
        texto = f"{conteo['cantada']} de {conteo['total']} cantadas"
        if conteo["saltada"]:
            texto += f", {conteo['saltada']} saltadas"
        if conteo["no_encontrada"]:
            texto += f", {conteo['no_encontrada']} no encontradas"
        return texto

    # =============================================================== cambios
    def marcar_cantada(self, codigo: int) -> ItemPrograma | None:
        """Marca la cancion como cantada; las pendientes anteriores quedan como saltadas."""
        objetivo = None
        for item in self.items:
            if item.codigo == codigo and item.estado == "pendiente":
                objetivo = item
                break
        if objetivo is None:
            return None  # no esta en el programa o es una repeticion
        for item in self.items:
            if item is objetivo:
                break
            if item.estado == "pendiente":
                item.estado = "saltada"
        objetivo.estado = "cantada"
        self._guardar()
        return objetivo

    def saltar_siguiente(self) -> ItemPrograma | None:
        """Marca como saltada la siguiente pendiente y devuelve la nueva siguiente."""
        actual = self.siguiente()
        if actual is not None:
            actual.estado = "saltada"
            self._guardar()
        return self.siguiente()


def interpretar_programa(texto: str) -> list[str]:
    """Nombres (o codigos) del archivo PROGRAMA, en orden."""
    nombres = []
    for renglon in texto.replace("\ufeff", "").splitlines():
        limpio = renglon.strip()
        if limpio and not limpio.startswith("#"):
            nombres.append(_quitar_numero_de_orden(limpio))
    return [n for n in nombres if n]


def _quitar_numero_de_orden(renglon: str) -> str:
    """'1. Cielito lindo' -> 'Cielito lindo'. Un numero solo se conserva (es un codigo)."""
    i = 0
    while i < len(renglon) and renglon[i].isdigit():
        i += 1
    if 0 < i < len(renglon):
        resto = renglon[i:].lstrip()
        if resto[:1] in (".", ")", "-", ":") and resto[1:].strip():
            return resto[1:].strip()
    return renglon


def escribir_programa(ruta: str, nombres: list[str]) -> None:
    with open(ruta, "w", encoding="utf-8") as archivo:
        archivo.write("# Programa tentativo del cantante: una canción por renglón, en orden.\n")
        for nombre in nombres:
            archivo.write(nombre.strip() + "\n")
