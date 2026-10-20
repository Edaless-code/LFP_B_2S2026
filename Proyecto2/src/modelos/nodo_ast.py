"""Nodo del arbol de derivacion construido por el analizador sintactico."""

from __future__ import annotations

from modelos.token import Token


class NodoAST:
    """Nodo del arbol de derivacion (AST).

    Un nodo no terminal representa una produccion de la gramatica, por ejemplo
    <documento> o <item_lista>, y sus hijos son los simbolos de esa produccion
    en orden. Un nodo terminal es una hoja que envuelve el token reconocido.

    A partir de este arbol se generan el HTML de salida, las estadisticas, el
    indice y el archivo arbol.dot.

    Attributes:
        simbolo: Nombre del simbolo. Los no terminales se escriben entre
            angulos (<parrafo>) y los terminales con el tipo de token (TEXTO).
        token: Token asociado si el nodo es terminal; None si es no terminal.
        hijos: Nodos hijos en el orden en que aparecen en la produccion.
    """

    def __init__(self, simbolo: str, token: Token | None = None) -> None:
        self.simbolo = simbolo
        self.token = token
        self.hijos: list[NodoAST] = []

    @classmethod
    def no_terminal(cls, nombre: str) -> NodoAST:
        """Crea un nodo no terminal a partir del nombre de la produccion.

        Args:
            nombre: Nombre sin angulos, por ejemplo "parrafo".
        """
        return cls(f"<{nombre}>")

    @classmethod
    def terminal(cls, token: Token) -> NodoAST:
        """Crea una hoja a partir de un token reconocido."""
        return cls(token.tipo.value, token)

    @property
    def es_terminal(self) -> bool:
        """Indica si el nodo es una hoja que representa un token."""
        return self.token is not None

    @property
    def lexema(self) -> str:
        """Lexema del token asociado, o cadena vacia si es no terminal."""
        return self.token.lexema if self.token is not None else ""

    def agregar_hijo(self, hijo: NodoAST) -> NodoAST:
        """Agrega un hijo al final de la lista y lo devuelve.

        Devolver el hijo permite construir el arbol de forma encadenada desde
        las funciones del parser.
        """
        self.hijos.append(hijo)
        return hijo

    def __repr__(self) -> str:
        if self.es_terminal:
            return f"NodoAST({self.simbolo}, {self.lexema!r})"
        return f"NodoAST({self.simbolo}, hijos={len(self.hijos)})"
