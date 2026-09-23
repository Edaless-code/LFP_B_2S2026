"""Catalogo de tipos de token del lenguaje HorarioScript.

Define la enumeracion TipoToken, que clasifica cada lexema reconocido por el
analizador lexico. El valor de cada miembro es exactamente el texto que se
muestra en la tabla de tokens de la interfaz grafica y en los reportes.
"""

from enum import Enum


class TipoToken(str, Enum):
    """Tipos de token que reconoce el AFD de HorarioScript.

    Hereda de str para que cada miembro se comporte como una cadena, lo que
    permite mostrarlo en la interfaz sin conversiones explicitas.
    """

    PALABRA_RESERVADA_BLOQUE = "PALABRA_RESERVADA_BLOQUE"
    PALABRA_RESERVADA_ELEMENTO = "PALABRA_RESERVADA_ELEMENTO"
    PALABRA_RESERVADA_RELACION = "PALABRA_RESERVADA_RELACION"
    PALABRA_RESERVADA_ATRIBUTO = "PALABRA_RESERVADA_ATRIBUTO"
    CODIGO = "CODIGO"
    CADENA = "CADENA"
    HORA = "HORA"
    ENTERO = "ENTERO"
    DIA = "DIA"
    CATEGORIA = "CATEGORIA"
    SIMBOLO = "SIMBOLO"
    COMENTARIO_LINEA = "COMENTARIO_LINEA"
    FIN_ARCHIVO = "FIN_ARCHIVO"

    def __str__(self) -> str:
        return self.value