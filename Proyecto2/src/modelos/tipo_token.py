"""Catalogo de tipos de token del subconjunto de Markdown soportado.

Define la enumeracion TipoToken, que clasifica cada lexema reconocido por el
analizador lexico (seccion 4.5 del enunciado). El valor de cada miembro es el
texto que se muestra en la tabla de tokens de la interfaz grafica.
"""

from enum import Enum


class TipoToken(str, Enum):
    """Tipos de token que reconoce el AFD de MarkdownCheck.

    Hereda de str para que cada miembro se comporte como una cadena, lo que
    permite mostrarlo en la interfaz sin conversiones explicitas.

    Ademas de los tokens de la seccion 4.5 se definen cuatro tokens de apoyo,
    justificados en el manual tecnico:
        LENGUAJE: identificador opcional despues del ``` de apertura
            (por ejemplo, python), usado para la clase language-xxx.
        TEXTO_LITERAL: contenido de un bloque de codigo o de un codigo en
            linea, que se toma tal cual sin tokenizar su interior.
        SALTO_LINEA: fin de una linea no vacia; delimita el contenido en
            linea de encabezados, items de lista y citas.
        FIN_ARCHIVO: marca el final de la entrada para el parser.

    Tokens del alcance opcional (seccion 4.2 del enunciado):
        ENUMERADOR: marcador de lista ordenada ("1.").
        CASILLA: casilla de una lista de tareas ("[ ]" o "[x]").
        TACHADO: delimitador de texto tachado ("~~").
        CORCHETE_ABRE, IMAGEN_ABRE, CORCHETE_CIERRA, URL: partes de un
            enlace [texto](url) o de una imagen ![alt](url).
    """

    # Marcadores de bloque (solo validos al inicio de linea)
    NUMERAL = "NUMERAL"
    VINETA = "VIÑETA"
    ENUMERADOR = "ENUMERADOR"
    CASILLA = "CASILLA"
    CITA = "CITA"
    CERCA_CODIGO = "CERCA_CODIGO"
    REGLA_HORIZONTAL = "REGLA_HORIZONTAL"

    # Tokens virtuales de anidamiento de listas
    INDENT = "INDENT"
    DEDENT = "DEDENT"

    # Delimitadores en linea
    NEGRITA = "NEGRITA"
    CURSIVA = "CURSIVA"
    CODIGO_INLINE = "CODIGO_INLINE"
    TACHADO = "TACHADO"

    # Enlaces e imagenes
    CORCHETE_ABRE = "CORCHETE_ABRE"
    IMAGEN_ABRE = "IMAGEN_ABRE"
    CORCHETE_CIERRA = "CORCHETE_CIERRA"
    URL = "URL"

    # Contenido
    TEXTO = "TEXTO"
    TEXTO_LITERAL = "TEXTO_LITERAL"
    LENGUAJE = "LENGUAJE"

    # Separadores de estructura
    SALTO_LINEA = "SALTO_LINEA"
    SALTO_PARRAFO = "SALTO_PARRAFO"
    FIN_ARCHIVO = "FIN_ARCHIVO"

    @property
    def es_virtual(self) -> bool:
        """Indica si el token no tiene lexema visible en el archivo fuente."""
        return self in (TipoToken.INDENT, TipoToken.DEDENT, TipoToken.FIN_ARCHIVO)

    def __str__(self) -> str:
        return self.value
