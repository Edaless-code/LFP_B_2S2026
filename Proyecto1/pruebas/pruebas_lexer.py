import os
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from analizador.analizador_lexico import AnalizadorLexico
from analizador.gestor_errores import GestorErrores
from modelos.error_lexico import TipoError
from modelos.tipo_token import TipoToken


def analizar(texto: str):
    gestor = GestorErrores()
    analizador = AnalizadorLexico(texto, gestor)
    return analizador.analizar_todo(), gestor


def probar_tokens_basicos() -> None:
    tokens, gestor = analizar('HORARIO {\ncurso: "LFP-0796", creditos: 4\n}')
    assert not gestor.hay_errores, gestor.errores
    esperado = [
        ("HORARIO", TipoToken.PALABRA_RESERVADA_BLOQUE, 1, 1),
        ("{", TipoToken.SIMBOLO, 1, 9),
        ("curso", TipoToken.PALABRA_RESERVADA_ELEMENTO, 2, 1),
        (":", TipoToken.SIMBOLO, 2, 6),
        ('"LFP-0796"', TipoToken.CODIGO, 2, 8),
        (",", TipoToken.SIMBOLO, 2, 18),
        ("creditos", TipoToken.PALABRA_RESERVADA_ATRIBUTO, 2, 20),
        (":", TipoToken.SIMBOLO, 2, 28),
        ("4", TipoToken.ENTERO, 2, 30),
        ("}", TipoToken.SIMBOLO, 3, 1),
    ]
    obtenido = [(t.lexema, t.tipo, t.linea, t.columna) for t in tokens]
    assert obtenido == esperado, f"\nesperado: {esperado}\nobtenido: {obtenido}"
    print("tokens basicos: OK")


def probar_horas() -> None:
    tokens, gestor = analizar("07:00 18:40 06:00 21:00")
    assert not gestor.hay_errores, gestor.errores
    assert all(t.tipo is TipoToken.HORA for t in tokens)
    assert len(tokens) == 4

    tokens, gestor = analizar("40 4 2026 999")
    assert not gestor.hay_errores, gestor.errores
    assert all(t.tipo is TipoToken.ENTERO for t in tokens), [t.tipo for t in tokens]

    for entrada in ("7:00", "100:00", "25:00", "07:60", "05:59", "21:30"):
        tokens, gestor = analizar(entrada)
        assert gestor.total == 1, f"{entrada}: se esperaba 1 error, hubo {gestor.total} -> {gestor.errores}"
        assert gestor.errores[0].tipo is TipoError.HORA_FUERA_DE_RANGO, entrada
    print("horas: OK")


def probar_errores() -> None:
    tokens, gestor = analizar('curso: "Matematica 100% @"')
    assert not gestor.hay_errores, gestor.errores

    _, gestor = analizar("@ % ~")
    assert gestor.total == 3, gestor.errores
    assert gestor.errores[0].tipo is TipoError.CARACTER_NO_RECONOCIDO
    assert gestor.errores[0].columna == 1
    assert gestor.errores[2].columna == 5

    _, gestor = analizar('edificio: "sin cerrar\nsiguiente')
    assert gestor.errores[0].tipo is TipoError.CADENA_SIN_CERRAR, gestor.errores
    assert gestor.errores[0].linea == 1 and gestor.errores[0].columna == 11, gestor.errores[0]

    _, gestor = analizar("dia: LUNEZ")
    assert gestor.errores[0].tipo is TipoError.DIA_NO_RECONOCIDO, gestor.errores

    _, gestor = analizar("categoria: TITULA")
    assert gestor.errores[0].tipo is TipoError.CATEGORIA_NO_RECONOCIDA, gestor.errores

    _, gestor = analizar("A-B10")
    assert gestor.errores[0].tipo is TipoError.CODIGO_MAL_FORMADO, gestor.errores
    assert gestor.errores[0].lexema == "A-B10", gestor.errores[0].lexema

    _, gestor = analizar("# suelto")
    assert gestor.errores[0].tipo is TipoError.CARACTER_NO_RECONOCIDO, gestor.errores

    tokens, gestor = analizar("@ HORARIO @ CURSOS")
    assert gestor.total == 2, gestor.errores
    assert len(tokens) == 2, tokens
    print("errores: OK")


def probar_comentarios() -> None:
    tokens, gestor = analizar("## Ciclo 2026-1 @ 100%\nHORARIO")
    assert not gestor.hay_errores, gestor.errores
    assert tokens[0].tipo is TipoToken.COMENTARIO_LINEA
    assert tokens[0].lexema == "## Ciclo 2026-1 @ 100%", tokens[0].lexema
    assert tokens[1].linea == 2 and tokens[1].columna == 1
    print("comentarios: OK")


def main() -> None:
    probar_tokens_basicos()
    probar_horas()
    probar_errores()
    probar_comentarios()
    print("\nTodas las pruebas del analizador pasaron.")


if __name__ == "__main__":
    main()
