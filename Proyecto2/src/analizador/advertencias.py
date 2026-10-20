"""Advertencias de anidamiento excesivo (alcance opcional).

No son errores: el documento es valido, pero sus listas o citas superan la
profundidad maxima que el usuario configuro en la interfaz.
"""

from modelos.nodo_ast import NodoAST

TIPO_LISTA = "lista"
TIPO_CITA = "cita"


class AdvertenciaAnidamiento:
    """Lista o cita que supera la profundidad maxima configurada.

    Attributes:
        tipo: TIPO_LISTA o TIPO_CITA.
        nivel: Nivel de anidamiento alcanzado.
        linea, columna: Posicion del marcador que abre ese nivel.
    """

    def __init__(self, tipo: str, nivel: int, linea: int, columna: int) -> None:
        self.tipo = tipo
        self.nivel = nivel
        self.linea = linea
        self.columna = columna

    @property
    def descripcion(self) -> str:
        return f"{self.tipo} de {self.nivel} niveles en la línea {self.linea}"


def _primer_token(nodo: NodoAST):
    """Primer token del subarbol en preorden."""
    if nodo.es_terminal:
        return nodo.token
    for hijo in nodo.hijos:
        token = _primer_token(hijo)
        if token is not None:
            return token
    return None


def buscar_anidamiento_excesivo(raiz: NodoAST, maximo: int) -> list[AdvertenciaAnidamiento]:
    """Recorre el arbol y devuelve las listas y citas que superan el maximo.

    Se reporta una advertencia por cada lista o cita que cruza el limite,
    con su nivel maximo alcanzado; los niveles mas profundos dentro de ella
    no generan advertencias adicionales.

    Args:
        raiz: Raiz <documento> del arbol de derivacion.
        maximo: Profundidad maxima permitida (1 o mas).
    """
    advertencias: list[AdvertenciaAnidamiento] = []

    def profundidad(nodo: NodoAST, simbolo: str) -> int:
        propio = 1 if nodo.simbolo == simbolo else 0
        return propio + max((profundidad(hijo, simbolo) for hijo in nodo.hijos), default=0)

    def recorrer(nodo: NodoAST, nivel_lista: int, nivel_cita: int) -> None:
        if nodo.simbolo == "<lista>":
            nivel_lista += 1
            if nivel_lista == maximo + 1:
                token = _primer_token(nodo)
                nivel = nivel_lista - 1 + profundidad(nodo, "<lista>")
                advertencias.append(AdvertenciaAnidamiento(TIPO_LISTA, nivel, token.linea, token.columna))
        elif nodo.simbolo == "<cita>":
            nivel_cita += 1
            if nivel_cita == maximo + 1:
                token = _primer_token(nodo)
                nivel = nivel_cita - 1 + profundidad(nodo, "<cita>")
                advertencias.append(AdvertenciaAnidamiento(TIPO_CITA, nivel, token.linea, token.columna))
        for hijo in nodo.hijos:
            recorrer(hijo, nivel_lista, nivel_cita)

    recorrer(raiz, 0, 0)
    return advertencias
