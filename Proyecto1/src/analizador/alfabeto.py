"""Clasificacion de caracteres del alfabeto de HorarioScript.

Todas las funciones operan sobre un unico caracter mediante comparaciones
directas. No se utiliza el modulo re ni metodos de cadena de alto nivel,
conforme a la restriccion del enunciado.
"""

SIMBOLOS: frozenset[str] = frozenset({"{", "}", "[", "]", ":", ",", ";"})
ESPACIOS: frozenset[str] = frozenset({" ", "\t", "\r"})

COMILLA = '"'
GUION = "-"
NUMERAL = "#"
DOS_PUNTOS = ":"
SALTO_LINEA = "\n"


def es_letra(caracter: str) -> bool:
    """Indica si el caracter es una letra del alfabeto ingles, A-Z o a-z."""
    return ("A" <= caracter <= "Z") or ("a" <= caracter <= "z")


def es_digito(caracter: str) -> bool:
    """Indica si el caracter es un digito decimal, 0-9."""
    return "0" <= caracter <= "9"


def es_alfanumerico(caracter: str) -> bool:
    """Indica si el caracter es letra o digito."""
    return es_letra(caracter) or es_digito(caracter)


def es_espacio(caracter: str) -> bool:
    """Indica si el caracter es un blanco que no rompe linea."""
    return caracter in ESPACIOS


def es_salto_linea(caracter: str) -> bool:
    """Indica si el caracter es un salto de linea."""
    return caracter == SALTO_LINEA


def es_simbolo(caracter: str) -> bool:
    """Indica si el caracter es un simbolo estructural del lenguaje."""
    return caracter in SIMBOLOS


def pertenece_al_alfabeto(caracter: str) -> bool:
    """Indica si el caracter pertenece al alfabeto de nivel superior.

    El alfabeto restringido aplica unicamente al estado inicial del AFD.
    Dentro de una cadena o de un comentario se admite cualquier caracter,
    segun la seccion 4.5 del enunciado.
    """
    return (
        es_alfanumerico(caracter)
        or es_simbolo(caracter)
        or es_espacio(caracter)
        or es_salto_linea(caracter)
        or caracter in (COMILLA, GUION, NUMERAL)
    )