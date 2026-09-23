"""Representacion de un token reconocido por el analizador lexico."""

from modelos.tipo_token import TipoToken


class Token:
    """Unidad lexica reconocida en un archivo .hor.

    Attributes:
        numero: Posicion del token en la secuencia, comenzando en 1.
        lexema: Texto exacto tal como aparece en el archivo fuente.
        tipo: Clasificacion asignada por el analizador lexico.
        linea: Linea donde inicia el lexema, comenzando en 1.
        columna: Columna donde inicia el lexema, comenzando en 1.
    """

    def __init__(
        self,
        numero: int,
        lexema: str,
        tipo: TipoToken,
        linea: int,
        columna: int,
    ) -> None:
        self.numero = numero
        self.lexema = lexema
        self.tipo = tipo
        self.linea = linea
        self.columna = columna

    def a_fila(self) -> tuple[int, str, str, int, int]:
        """Devuelve el token como fila lista para la tabla de la interfaz.

        Returns:
            Tupla con numero, lexema, tipo, linea y columna.
        """
        return (self.numero, self.lexema, self.tipo.value, self.linea, self.columna)

    def __repr__(self) -> str:
        return (
            f"Token({self.numero}, {self.lexema!r}, {self.tipo.value}, "
            f"linea={self.linea}, columna={self.columna})"
        )