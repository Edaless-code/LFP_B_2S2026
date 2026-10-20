"""Representacion de un error lexico o sintactico y su catalogo de tipos.

Los tipos de error y los mensajes corresponden a la seccion 4.9 del enunciado.
Se agrega TOKEN_INESPERADO para los casos sintacticos que no encajan en
ninguna de las categorias anteriores, de modo que el parser siempre pueda
reportar con precision lo que encontro.
"""

from enum import Enum


class Fase(str, Enum):
    """Fase del analisis en la que se detecta un error."""

    LEXICO = "Léxico"
    SINTACTICO = "Sintáctico"

    def __str__(self) -> str:
        return self.value


class TipoError(str, Enum):
    """Categorias de error que reporta MarkdownCheck."""

    NEGRITA_SIN_CERRAR = "NEGRITA_SIN_CERRAR"
    CURSIVA_SIN_CERRAR = "CURSIVA_SIN_CERRAR"
    CODIGO_INLINE_SIN_CERRAR = "CODIGO_INLINE_SIN_CERRAR"
    BLOQUE_CODIGO_SIN_CERRAR = "BLOQUE_CODIGO_SIN_CERRAR"
    ENCABEZADO_INVALIDO = "ENCABEZADO_INVALIDO"
    INDENTACION_INVALIDA = "INDENTACION_INVALIDA"
    CITA_MAL_FORMADA = "CITA_MAL_FORMADA"
    TOKEN_INESPERADO = "TOKEN_INESPERADO"

    def __str__(self) -> str:
        return self.value


FASE_POR_TIPO: dict[TipoError, Fase] = {
    TipoError.NEGRITA_SIN_CERRAR: Fase.LEXICO,
    TipoError.CURSIVA_SIN_CERRAR: Fase.LEXICO,
    TipoError.CODIGO_INLINE_SIN_CERRAR: Fase.LEXICO,
    TipoError.BLOQUE_CODIGO_SIN_CERRAR: Fase.LEXICO,
    TipoError.ENCABEZADO_INVALIDO: Fase.LEXICO,
    TipoError.INDENTACION_INVALIDA: Fase.SINTACTICO,
    TipoError.CITA_MAL_FORMADA: Fase.SINTACTICO,
    TipoError.TOKEN_INESPERADO: Fase.SINTACTICO,
}

PLANTILLAS_MENSAJE: dict[TipoError, str] = {
    TipoError.NEGRITA_SIN_CERRAR:
        "Negrita sin cerrar iniciada en línea {linea}, columna {columna}",
    TipoError.CURSIVA_SIN_CERRAR:
        "Cursiva sin cerrar iniciada en línea {linea}, columna {columna}",
    TipoError.CODIGO_INLINE_SIN_CERRAR:
        "Código en línea sin cerrar iniciado en línea {linea}, columna {columna}",
    TipoError.BLOQUE_CODIGO_SIN_CERRAR:
        "Bloque de código sin cerrar iniciado en línea {linea}",
    TipoError.ENCABEZADO_INVALIDO:
        "Encabezado inválido en línea {linea}: máximo 6 niveles",
    TipoError.INDENTACION_INVALIDA:
        "Indentación inválida en línea {linea}, columna {columna}",
    TipoError.CITA_MAL_FORMADA:
        "Cita mal formada en línea {linea}, columna {columna}",
    TipoError.TOKEN_INESPERADO:
        "Token inesperado '{lexema}' en línea {linea}, columna {columna}",
}


class ErrorAnalisis:
    """Error detectado durante el analisis lexico o sintactico.

    Attributes:
        numero: Posicion del error en la secuencia, comenzando en 1.
        lexema: Fragmento de texto que provoco el error.
        tipo: Categoria del error.
        linea: Linea donde inicia el lexema invalido, comenzando en 1.
        columna: Columna donde inicia el lexema invalido, comenzando en 1.
        descripcion: Mensaje legible con la posicion exacta.
    """

    def __init__(
        self,
        numero: int,
        lexema: str,
        tipo: TipoError,
        linea: int,
        columna: int,
    ) -> None:
        self.numero = numero
        self.lexema = lexema
        self.tipo = tipo
        self.linea = linea
        self.columna = columna
        self.descripcion = PLANTILLAS_MENSAJE[tipo].format(
            lexema=lexema, linea=linea, columna=columna
        )

    @property
    def fase(self) -> Fase:
        """Fase del analisis a la que pertenece el error."""
        return FASE_POR_TIPO[self.tipo]

    def a_fila(self) -> tuple[int, str, str, str, str, int, int]:
        """Devuelve el error como fila lista para la tabla de la interfaz.

        Returns:
            Tupla con numero, lexema, tipo, fase, descripcion, linea y columna.
        """
        return (
            self.numero,
            self.lexema,
            self.tipo.value,
            self.fase.value,
            self.descripcion,
            self.linea,
            self.columna,
        )

    def __repr__(self) -> str:
        return (
            f"ErrorAnalisis({self.numero}, {self.tipo.value}, "
            f"linea={self.linea}, columna={self.columna})"
        )
