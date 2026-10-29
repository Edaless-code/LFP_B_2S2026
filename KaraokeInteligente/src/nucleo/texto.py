"""Normalizacion y comparacion de texto (sin dependencias externas).

La busqueda de canciones compara lo que se teclea o se transcribe con la letra
guardada. Para que "Corazón" y "corazon," se consideren iguales, todo se pasa
a minusculas, sin tildes y sin signos de puntuacion.
"""

from __future__ import annotations

import difflib
import unicodedata

# Vocalizaciones y muletillas que no aportan para identificar una cancion.
RELLENOS = {
    "ah", "aah", "ahh", "eh", "ehh", "oh", "ooh", "ohh", "uh", "uhh", "mm", "mmm", "hmm",
    "lala", "lalala", "nana", "nanana", "yeah", "uoh", "uooh", "woh", "wo",
    "uuh", "uu", "aa", "ee", "oo",
}

# Frases que Whisper "inventa" cuando escucha musica o silencio (alucinaciones conocidas).
ALUCINACIONES = (
    "subtitulos realizados por la comunidad de amara",
    "subtitulos por la comunidad de amara",
    "amara org",
    "gracias por ver",
    "suscribete",
    "suscribanse",
    "subtitulado por",
    "transcripcion por",
    "musica de fondo",
    "musica",
    "aplausos",
)


def quitar_tildes(texto: str) -> str:
    descompuesto = unicodedata.normalize("NFD", texto)
    return "".join(c for c in descompuesto if unicodedata.category(c) != "Mn")


def normalizar(texto: str) -> str:
    """Minusculas, sin tildes, sin puntuacion y con un solo espacio entre palabras."""
    texto = quitar_tildes(texto.lower())
    limpio = []
    for caracter in texto:
        if caracter.isalnum():
            limpio.append(caracter)
        elif caracter == "'":
            continue  # pa' -> pa
        else:
            limpio.append(" ")
    return " ".join("".join(limpio).split())


def palabras(texto: str) -> list[str]:
    return normalizar(texto).split()


def es_relleno(palabra: str) -> bool:
    if palabra in RELLENOS:
        return True
    # "laaaa", "ooooh", "nananana"
    if len(set(palabra)) <= 2 and len(palabra) >= 3:
        return True
    return False


def palabras_significativas(texto: str) -> list[str]:
    """Palabras normalizadas sin vocalizaciones ni repeticiones inmediatas.

    Una palabra corta repetida tres o mas veces seguidas ("la la la", "na na na")
    se considera vocalizacion y se descarta completa.
    """
    lista = [p for p in palabras(texto) if not es_relleno(p)]
    resultado: list[str] = []
    i = 0
    while i < len(lista):
        j = i
        while j + 1 < len(lista) and lista[j + 1] == lista[i]:
            j += 1
        repeticiones = j - i + 1
        if not (repeticiones >= 3 and len(lista[i]) <= 3):
            resultado.append(lista[i])
        i = j + 1
    return resultado


def limpiar_transcripcion(texto: str) -> str:
    """Quita alucinaciones tipicas del reconocedor y deja solo palabras utiles."""
    normal = normalizar(texto)
    for frase in ALUCINACIONES:
        if frase in normal:
            normal = normal.replace(frase, " ")
    return " ".join(palabras_significativas(normal))


def similitud_palabras(a: str, b: str) -> float:
    """Similitud entre dos palabras normalizadas (1.0 = iguales)."""
    if a == b:
        return 1.0
    if not a or not b:
        return 0.0
    largo_a, largo_b = len(a), len(b)
    if abs(largo_a - largo_b) > max(2, min(largo_a, largo_b) // 2):
        return 0.0
    comparador = difflib.SequenceMatcher(None, a, b, autojunk=False)
    if comparador.real_quick_ratio() < 0.6 or comparador.quick_ratio() < 0.6:
        return 0.0
    return comparador.ratio()


def similitud_textos(a: str, b: str) -> float:
    """Similitud de dos textos completos, tolerante a errores de escritura."""
    na, nb = normalizar(a), normalizar(b)
    if not na or not nb:
        return 0.0
    return difflib.SequenceMatcher(None, na, nb, autojunk=False).ratio()


def partir_linea(linea: str, maximo: int) -> list[str]:
    """Divide una linea larga en partes de hasta `maximo` caracteres sin cortar palabras."""
    linea = " ".join(linea.split())
    if maximo <= 0 or len(linea) <= maximo:
        return [linea] if linea else []
    partes: list[str] = []
    actual = ""
    for palabra in linea.split(" "):
        while len(palabra) > maximo:
            if actual:
                partes.append(actual)
                actual = ""
            partes.append(palabra[:maximo])
            palabra = palabra[maximo:]
        candidato = f"{actual} {palabra}".strip()
        if len(candidato) <= maximo:
            actual = candidato
        else:
            partes.append(actual)
            actual = palabra
    if actual:
        partes.append(actual)
    return partes
