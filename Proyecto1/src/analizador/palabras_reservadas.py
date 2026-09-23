"""Diccionarios de palabras reservadas, dias y categorias de HorarioScript.

La busqueda es sensible a mayusculas y minusculas: las palabras de bloque,
los dias y las categorias se escriben en mayusculas, mientras que las de
elemento, relacion y atributo se escriben en minusculas.
"""

from modelos.tipo_token import TipoToken

RESERVADAS_BLOQUE: frozenset[str] = frozenset({
    "HORARIO", "CURSOS", "CATEDRATICOS", "AULAS", "CLASES",
})

RESERVADAS_ELEMENTO: frozenset[str] = frozenset({
    "curso", "catedratico", "aula", "clase",
})

RESERVADAS_RELACION: frozenset[str] = frozenset({
    "con", "en",
})

RESERVADAS_ATRIBUTO: frozenset[str] = frozenset({
    "codigo", "creditos", "categoria", "capacidad",
    "edificio", "dia", "inicio", "fin", "seccion",
})

DIAS: frozenset[str] = frozenset({
    "LUNES", "MARTES", "MIERCOLES", "JUEVES", "VIERNES", "SABADO",
})

CATEGORIAS: frozenset[str] = frozenset({
    "TITULAR", "INTERINO", "AUXILIAR",
})

ATRIBUTO_DIA = "dia"
ATRIBUTO_CATEGORIA = "categoria"


def _construir_tabla() -> dict[str, TipoToken]:
    """Une los seis conjuntos en una sola tabla de busqueda."""
    tabla: dict[str, TipoToken] = {}
    for grupo, tipo in (
        (RESERVADAS_BLOQUE, TipoToken.PALABRA_RESERVADA_BLOQUE),
        (RESERVADAS_ELEMENTO, TipoToken.PALABRA_RESERVADA_ELEMENTO),
        (RESERVADAS_RELACION, TipoToken.PALABRA_RESERVADA_RELACION),
        (RESERVADAS_ATRIBUTO, TipoToken.PALABRA_RESERVADA_ATRIBUTO),
        (DIAS, TipoToken.DIA),
        (CATEGORIAS, TipoToken.CATEGORIA),
    ):
        for palabra in grupo:
            tabla[palabra] = tipo
    return tabla


TABLA_PALABRAS: dict[str, TipoToken] = _construir_tabla()


def clasificar_palabra(lexema: str) -> TipoToken | None:
    """Clasifica una secuencia alfanumerica ya consumida por el AFD.

    Args:
        lexema: Texto completo de la secuencia alfanumerica.

    Returns:
        El TipoToken correspondiente, o None si el lexema no pertenece a
        ninguna de las seis tablas del lenguaje.
    """
    return TABLA_PALABRAS.get(lexema)