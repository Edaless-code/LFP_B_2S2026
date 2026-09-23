"""Representacion de un error lexico y su catalogo de tipos."""

from enum import Enum


class TipoError(str, Enum):
    """Categorias de error lexico que reporta el analizador."""

    CARACTER_NO_RECONOCIDO = "CARACTER_NO_RECONOCIDO"
    CADENA_SIN_CERRAR = "CADENA_SIN_CERRAR"
    HORA_FUERA_DE_RANGO = "HORA_FUERA_DE_RANGO"
    DIA_NO_RECONOCIDO = "DIA_NO_RECONOCIDO"
    CODIGO_MAL_FORMADO = "CODIGO_MAL_FORMADO"
    CATEGORIA_NO_RECONOCIDA = "CATEGORIA_NO_RECONOCIDA"
    PALABRA_NO_RECONOCIDA = "PALABRA_NO_RECONOCIDA"

    def __str__(self) -> str:
        return self.value


PLANTILLAS_MENSAJE: dict[TipoError, str] = {
    TipoError.CARACTER_NO_RECONOCIDO:
        "Caracter no reconocido: '{lexema}' en linea {linea}, columna {columna}",
    TipoError.CADENA_SIN_CERRAR:
        "Cadena sin cerrar iniciada en linea {linea}, columna {columna}",
    TipoError.HORA_FUERA_DE_RANGO:
        "Hora fuera de rango: '{lexema}' en linea {linea}, columna {columna}",
    TipoError.DIA_NO_RECONOCIDO:
        "Dia no reconocido: '{lexema}' en linea {linea}, columna {columna}",
    TipoError.CODIGO_MAL_FORMADO:
        "Codigo mal formado: '{lexema}' en linea {linea}, columna {columna}",
    TipoError.CATEGORIA_NO_RECONOCIDA:
        "Categoria no reconocida: '{lexema}' en linea {linea}, columna {columna}",
    TipoError.PALABRA_NO_RECONOCIDA:
        "Palabra no reconocida: '{lexema}' en linea {linea}, columna {columna}",
}


class ErrorLexico:
    """Error detectado durante el analisis lexico.

    Attributes:
        numero: Posicion del error en la secuencia, comenzando en 1.
        lexema: Fragmento de texto que provoco el error.
        tipo: Categoria del error.
        descripcion: Mensaje legible con la posicion exacta.
        linea: Linea donde inicia el lexema invalido, comenzando en 1.
        columna: Columna donde inicia el lexema invalido, comenzando en 1.
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

    def a_fila(self) -> tuple[int, str, str, str, int, int]:
        """Devuelve el error como fila lista para la tabla de la interfaz.

        Returns:
            Tupla con numero, lexema, tipo, descripcion, linea y columna.
        """
        return (
            self.numero,
            self.lexema,
            self.tipo.value,
            self.descripcion,
            self.linea,
            self.columna,
        )

    def __repr__(self) -> str:
        return f"ErrorLexico({self.numero}, {self.tipo.value}, {self.descripcion!r})"