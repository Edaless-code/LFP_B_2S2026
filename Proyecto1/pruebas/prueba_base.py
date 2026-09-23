"""Prueba de humo de las estructuras base del analizador lexico."""

import os
import sys

sys.path.append(
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
)

from analizador.alfabeto import es_digito, es_letra, es_simbolo, pertenece_al_alfabeto
from analizador.gestor_errores import GestorErrores
from analizador.palabras_reservadas import clasificar_palabra
from modelos.error_lexico import TipoError
from modelos.tipo_token import TipoToken
from modelos.token import Token


def probar_alfabeto() -> None:
    """Verifica la clasificacion de caracteres."""
    assert es_letra("A") and es_letra("z")
    assert not es_letra("0") and not es_letra("-")
    assert es_digito("0") and es_digito("9")
    assert not es_digito("a")
    assert es_simbolo("{") and es_simbolo(";")
    assert not es_simbolo("-")
    assert pertenece_al_alfabeto("#") and pertenece_al_alfabeto(" ")
    assert not pertenece_al_alfabeto("@")
    assert not pertenece_al_alfabeto("%")
    print("alfabeto: OK")


def probar_palabras_reservadas() -> None:
    """Verifica la clasificacion de secuencias alfanumericas."""
    assert clasificar_palabra("HORARIO") is TipoToken.PALABRA_RESERVADA_BLOQUE
    assert clasificar_palabra("curso") is TipoToken.PALABRA_RESERVADA_ELEMENTO
    assert clasificar_palabra("con") is TipoToken.PALABRA_RESERVADA_RELACION
    assert clasificar_palabra("creditos") is TipoToken.PALABRA_RESERVADA_ATRIBUTO
    assert clasificar_palabra("MARTES") is TipoToken.DIA
    assert clasificar_palabra("TITULAR") is TipoToken.CATEGORIA
    assert clasificar_palabra("LUNEZ") is None
    assert clasificar_palabra("horario") is None, "la busqueda debe ser sensible a mayusculas"
    print("palabras_reservadas: OK")


def probar_token() -> None:
    """Verifica la construccion y la serializacion de un token."""
    token = Token(1, "HORARIO", TipoToken.PALABRA_RESERVADA_BLOQUE, 2, 1)
    assert token.a_fila() == (1, "HORARIO", "PALABRA_RESERVADA_BLOQUE", 2, 1)
    print("token: OK")


def probar_gestor_errores() -> None:
    """Verifica la numeracion correlativa y el aislamiento del estado."""
    gestor = GestorErrores()
    assert not gestor.hay_errores

    primero = gestor.registrar(TipoError.CARACTER_NO_RECONOCIDO, "@", 5, 12)
    segundo = gestor.registrar(TipoError.CADENA_SIN_CERRAR, '"abc', 7, 3)

    assert primero.numero == 1 and segundo.numero == 2
    assert gestor.total == 2 and gestor.hay_errores
    assert primero.descripcion == "Caracter no reconocido: '@' en linea 5, columna 12"

    copia = gestor.errores
    copia.clear()
    assert gestor.total == 2, "la propiedad debe devolver una copia, no la lista interna"

    gestor.limpiar()
    assert gestor.total == 0
    print("gestor_errores: OK")


def main() -> None:
    """Ejecuta todas las pruebas de humo."""
    probar_alfabeto()
    probar_palabras_reservadas()
    probar_token()
    probar_gestor_errores()
    print("\nTodas las pruebas base pasaron.")


if __name__ == "__main__":
    main()