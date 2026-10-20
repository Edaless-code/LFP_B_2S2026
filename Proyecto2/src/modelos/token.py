"""Representacion de un token reconocido por el analizador lexico."""

from modelos.tipo_token import TipoToken


class Token:
    """Unidad lexica reconocida en un archivo .md.

    Attributes:
        numero: Posicion del token en la secuencia, comenzando en 1.
        lexema: Texto exacto tal como aparece en el archivo fuente. Es una
            cadena vacia para los tokens virtuales (INDENT, DEDENT, FIN_ARCHIVO).
        tipo: Clasificacion asignada por el analizador lexico.
        linea: Linea donde inicia el lexema, comenzando en 1.
        columna: Columna donde inicia el lexema, comenzando en 1.
        sangria: Ancho de la indentacion que precede a una VIÑETA, contando
            cada tabulacion como 2 espacios. El parser lo usa para validar el
            anidamiento; en los demas tokens vale 0.
    """

    def __init__(
        self,
        numero: int,
        lexema: str,
        tipo: TipoToken,
        linea: int,
        columna: int,
        sangria: int = 0,
    ) -> None:
        self.numero = numero
        self.lexema = lexema
        self.tipo = tipo
        self.linea = linea
        self.columna = columna
        self.sangria = sangria

    @property
    def lexema_visible(self) -> str:
        """Lexema preparado para mostrarse en una tabla.

        Los tokens virtuales no tienen texto y los saltos de linea son
        caracteres invisibles, por lo que se sustituyen por una notacion legible.
        """
        if self.tipo.es_virtual:
            return "(virtual)"
        if self.tipo in (TipoToken.SALTO_LINEA, TipoToken.SALTO_PARRAFO):
            return "\\n" * max(1, self.lexema.count("\n"))
        return self.lexema.replace("\n", "\\n")

    def a_fila(self) -> tuple[int, str, str, int, int]:
        """Devuelve el token como fila lista para la tabla de la interfaz.

        Returns:
            Tupla con numero, lexema, tipo, linea y columna.
        """
        return (self.numero, self.lexema_visible, self.tipo.value, self.linea, self.columna)

    def __repr__(self) -> str:
        return (
            f"Token({self.numero}, {self.lexema!r}, {self.tipo.value}, "
            f"linea={self.linea}, columna={self.columna})"
        )
