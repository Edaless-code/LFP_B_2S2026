"""Pruebas unitarias del analizador lexico.

Ejecutar desde la carpeta Proyecto2:
    python -m unittest discover -s tests -v
"""

import os
import sys
import unittest

DIRECTORIO_PROYECTO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(DIRECTORIO_PROYECTO, "src"))

from analizador.analizador_lexico import AnalizadorLexico
from analizador.gestor_errores import GestorErrores
from modelos.error_analisis import TipoError
from modelos.tipo_token import TipoToken as T


def tokenizar(texto: str):
    """Analiza el texto y devuelve (tokens, errores)."""
    gestor = GestorErrores()
    tokens = AnalizadorLexico(texto, gestor).analizar_todo()
    return tokens, gestor.errores


def tipos(tokens) -> list:
    return [token.tipo for token in tokens]


class PruebasArchivoEjemplo(unittest.TestCase):
    """Archivo de la seccion 4.7 del enunciado."""

    @classmethod
    def setUpClass(cls):
        ruta = os.path.join(DIRECTORIO_PROYECTO, "examples", "ejemplo_valido.md")
        with open(ruta, encoding="utf-8") as archivo:
            cls.tokens, cls.errores = tokenizar(archivo.read())

    def test_sin_errores(self):
        self.assertEqual(self.errores, [])

    def test_cantidad_de_tokens(self):
        self.assertEqual(len(self.tokens), 74)

    def test_numeracion_correlativa(self):
        self.assertEqual([t.numero for t in self.tokens], list(range(1, 75)))

    def test_parrafo_con_negrita_cursiva_y_codigo(self):
        linea_3 = [(t.tipo, t.lexema, t.columna) for t in self.tokens if t.linea == 3]
        self.assertEqual(
            linea_3,
            [
                (T.TEXTO, "Este curso combina ", 1),
                (T.NEGRITA, "**", 20),
                (T.TEXTO, "teoría sólida", 22),
                (T.NEGRITA, "**", 35),
                (T.TEXTO, " y ", 37),
                (T.CURSIVA, "*", 40),
                (T.TEXTO, "práctica de código", 41),
                (T.CURSIVA, "*", 59),
                (T.TEXTO, ", con ejemplos en ", 60),
                (T.CODIGO_INLINE, "`", 78),
                (T.TEXTO_LITERAL, "Python", 79),
                (T.CODIGO_INLINE, "`", 85),
                (T.TEXTO, ".", 86),
                (T.SALTO_LINEA, "\n", 87),
            ],
        )

    def test_lista_de_tres_niveles(self):
        lista = [t.tipo for t in self.tokens if 7 <= t.linea <= 14 and t.tipo != T.TEXTO]
        self.assertEqual(
            lista,
            [
                T.VINETA, T.SALTO_LINEA,
                T.INDENT, T.VINETA, T.SALTO_LINEA,
                T.VINETA, T.SALTO_LINEA,
                T.DEDENT, T.VINETA, T.SALTO_LINEA,
                T.INDENT, T.VINETA, T.SALTO_LINEA,
                T.INDENT, T.VINETA, T.SALTO_LINEA,
                T.VINETA, T.SALTO_LINEA,
                T.DEDENT, T.DEDENT, T.VINETA, T.SALTO_LINEA,
            ],
        )

    def test_sangria_de_las_vinetas(self):
        sangrias = [t.sangria for t in self.tokens if t.tipo == T.VINETA]
        self.assertEqual(sangrias, [0, 2, 2, 0, 2, 4, 4, 0])

    def test_citas_anidadas(self):
        citas = [(t.lexema, t.linea) for t in self.tokens if t.tipo == T.CITA]
        self.assertEqual(citas, [(">", 16), (">>", 17)])

    def test_bloque_de_codigo_literal(self):
        bloque = [(t.tipo, t.lexema) for t in self.tokens if 19 <= t.linea <= 22]
        self.assertEqual(
            bloque,
            [
                (T.CERCA_CODIGO, "```"),
                (T.LENGUAJE, "python"),
                (T.SALTO_LINEA, "\n"),
                (T.TEXTO_LITERAL, 'def hola():\n    print("Hola LFP")'),
                (T.CERCA_CODIGO, "```"),
                (T.SALTO_LINEA, "\n"),
            ],
        )

    def test_regla_horizontal_y_fin(self):
        self.assertEqual(
            [(t.tipo, t.linea) for t in self.tokens[-6:]],
            [
                (T.REGLA_HORIZONTAL, 24),
                (T.SALTO_LINEA, 24),
                (T.SALTO_PARRAFO, 25),
                (T.TEXTO, 26),
                (T.SALTO_LINEA, 26),
                (T.FIN_ARCHIVO, 27),
            ],
        )


class PruebasReglasDePrioridad(unittest.TestCase):
    """Reglas de la seccion 4.5 del enunciado."""

    def test_vineta_contra_cursiva(self):
        tokens, errores = tokenizar("* item\n\n*cursiva* texto\n")
        self.assertEqual(errores, [])
        self.assertEqual(
            tipos(tokens),
            [
                T.VINETA, T.TEXTO, T.SALTO_LINEA, T.SALTO_PARRAFO,
                T.CURSIVA, T.TEXTO, T.CURSIVA, T.TEXTO, T.SALTO_LINEA, T.FIN_ARCHIVO,
            ],
        )

    def test_las_tres_vinetas(self):
        tokens, _ = tokenizar("- a\n* b\n+ c\n")
        self.assertEqual([t.lexema for t in tokens if t.tipo == T.VINETA], ["-", "*", "+"])

    def test_negrita_tiene_prioridad_sobre_cursiva(self):
        tokens, errores = tokenizar("**a**\n")
        self.assertEqual(errores, [])
        self.assertEqual(tipos(tokens)[:3], [T.NEGRITA, T.TEXTO, T.NEGRITA])

    def test_tres_asteriscos_anidan_correctamente(self):
        tokens, errores = tokenizar("***a***\n")
        self.assertEqual(errores, [])
        self.assertEqual(
            tipos(tokens)[:5],
            [T.NEGRITA, T.CURSIVA, T.TEXTO, T.CURSIVA, T.NEGRITA],
        )

    def test_cursiva_dentro_de_negrita(self):
        tokens, errores = tokenizar("**negrita *y cursiva***\n")
        self.assertEqual(errores, [])
        self.assertEqual(
            tipos(tokens)[:6],
            [T.NEGRITA, T.TEXTO, T.CURSIVA, T.TEXTO, T.CURSIVA, T.NEGRITA],
        )

    def test_numeral_sin_espacio_es_texto(self):
        tokens, errores = tokenizar("#sinespacio\n")
        self.assertEqual(errores, [])
        self.assertEqual(tipos(tokens), [T.TEXTO, T.SALTO_LINEA, T.FIN_ARCHIVO])

    def test_seis_niveles_de_encabezado(self):
        tokens, errores = tokenizar("###### Titulo\n")
        self.assertEqual(errores, [])
        self.assertEqual((tokens[0].tipo, tokens[0].lexema), (T.NUMERAL, "######"))

    def test_regla_horizontal_contra_vineta(self):
        tokens, _ = tokenizar("---\n\n- item\n\n--- texto\n\n-----   \n")
        self.assertEqual(
            [t.tipo for t in tokens if t.tipo not in (T.SALTO_LINEA, T.SALTO_PARRAFO)],
            [T.REGLA_HORIZONTAL, T.VINETA, T.TEXTO, T.TEXTO, T.REGLA_HORIZONTAL, T.FIN_ARCHIVO],
        )

    def test_simbolos_fuera_de_inicio_de_linea_son_texto(self):
        tokens, errores = tokenizar("texto con # y > y - y +\n")
        self.assertEqual(errores, [])
        self.assertEqual(tipos(tokens), [T.TEXTO, T.SALTO_LINEA, T.FIN_ARCHIVO])

    def test_dos_notaciones_de_cita_anidada(self):
        tokens, _ = tokenizar(">> a\n> > b\n")
        self.assertEqual([t.lexema for t in tokens if t.tipo == T.CITA], [">>", "> >"])

    def test_cita_sin_espacio_no_es_error_lexico(self):
        # CITA_MAL_FORMADA es un error sintactico; el lexico solo entrega los tokens
        tokens, errores = tokenizar(">texto\n")
        self.assertEqual(errores, [])
        self.assertEqual((tokens[1].tipo, tokens[1].columna), (T.TEXTO, 2))

    def test_bloque_de_codigo_no_tokeniza_su_interior(self):
        tokens, errores = tokenizar("```\n**no** # es - markdown\n```\n")
        self.assertEqual(errores, [])
        self.assertEqual(
            tipos(tokens),
            [
                T.CERCA_CODIGO, T.SALTO_LINEA, T.TEXTO_LITERAL,
                T.CERCA_CODIGO, T.SALTO_LINEA, T.FIN_ARCHIVO,
            ],
        )
        self.assertEqual(tokens[2].lexema, "**no** # es - markdown")

    def test_codigo_inline_no_interpreta_asteriscos(self):
        tokens, errores = tokenizar("usa `**kwargs` aqui\n")
        self.assertEqual(errores, [])
        self.assertEqual(
            [(t.tipo, t.lexema) for t in tokens[1:4]],
            [(T.CODIGO_INLINE, "`"), (T.TEXTO_LITERAL, "**kwargs"), (T.CODIGO_INLINE, "`")],
        )


class PruebasIndentacion(unittest.TestCase):
    """Generacion de INDENT y DEDENT."""

    def test_salto_de_dos_niveles_genera_un_solo_indent(self):
        # El parser reporta INDENTACION_INVALIDA usando la sangria de la vineta
        tokens, errores = tokenizar("- a\n    - b\n")
        self.assertEqual(errores, [])
        self.assertEqual(tipos(tokens).count(T.INDENT), 1)
        self.assertEqual([t.sangria for t in tokens if t.tipo == T.VINETA], [0, 4])

    def test_lista_se_cierra_al_cambiar_de_bloque(self):
        tokens, _ = tokenizar("- a\n  - b\nparrafo\n")
        self.assertEqual(
            tipos(tokens),
            [
                T.VINETA, T.TEXTO, T.SALTO_LINEA,
                T.INDENT, T.VINETA, T.TEXTO, T.SALTO_LINEA,
                T.DEDENT, T.TEXTO, T.SALTO_LINEA, T.FIN_ARCHIVO,
            ],
        )

    def test_lista_se_cierra_con_linea_en_blanco_y_fin_de_archivo(self):
        tokens, _ = tokenizar("- a\n  - b\n\n- c\n  - d\n")
        self.assertEqual(tipos(tokens).count(T.INDENT), 2)
        self.assertEqual(tipos(tokens).count(T.DEDENT), 2)
        self.assertEqual(tipos(tokens)[-2:], [T.DEDENT, T.FIN_ARCHIVO])

    def test_tabulacion_equivale_a_un_nivel(self):
        tokens, _ = tokenizar("- a\n\t- b\n")
        self.assertEqual([t.sangria for t in tokens if t.tipo == T.VINETA], [0, 2])
        self.assertIn(T.INDENT, tipos(tokens))

    def test_primer_item_con_sangria_fija_la_base(self):
        tokens, _ = tokenizar("  - a\n  - b\n")
        self.assertNotIn(T.INDENT, tipos(tokens))


class PruebasErroresLexicos(unittest.TestCase):
    """Categorias lexicas de la seccion 4.9 del enunciado."""

    def test_negrita_sin_cerrar(self):
        tokens, errores = tokenizar("texto **sin cerrar\n")
        self.assertEqual(len(errores), 1)
        self.assertEqual(
            (errores[0].tipo, errores[0].linea, errores[0].columna),
            (TipoError.NEGRITA_SIN_CERRAR, 1, 7),
        )
        self.assertEqual(errores[0].descripcion, "Negrita sin cerrar iniciada en línea 1, columna 7")
        self.assertNotIn(T.NEGRITA, tipos(tokens))

    def test_cursiva_sin_cerrar(self):
        _, errores = tokenizar("# Titulo *roto\n")
        self.assertEqual(
            [(e.tipo, e.linea, e.columna) for e in errores],
            [(TipoError.CURSIVA_SIN_CERRAR, 1, 10)],
        )

    def test_codigo_inline_sin_cerrar(self):
        tokens, errores = tokenizar("- item `abierto\n")
        self.assertEqual(
            [(e.tipo, e.linea, e.columna) for e in errores],
            [(TipoError.CODIGO_INLINE_SIN_CERRAR, 1, 8)],
        )
        self.assertNotIn(T.CODIGO_INLINE, tipos(tokens))
        self.assertIn("`abierto", [t.lexema for t in tokens])

    def test_bloque_de_codigo_sin_cerrar(self):
        tokens, errores = tokenizar("Antes\n\n```python\nx = 1\n# no es encabezado\n")
        self.assertEqual(
            [(e.tipo, e.linea, e.descripcion) for e in errores],
            [(TipoError.BLOQUE_CODIGO_SIN_CERRAR, 3, "Bloque de código sin cerrar iniciado en línea 3")],
        )
        self.assertEqual(tokens[-2].tipo, T.TEXTO_LITERAL)
        self.assertEqual(tokens[-2].lexema, "x = 1\n# no es encabezado")

    def test_encabezado_invalido(self):
        tokens, errores = tokenizar("####### Demasiados\n")
        self.assertEqual(
            [(e.tipo, e.linea, e.columna, e.descripcion) for e in errores],
            [(TipoError.ENCABEZADO_INVALIDO, 1, 1, "Encabezado inválido en línea 1: máximo 6 niveles")],
        )
        self.assertEqual(tipos(tokens), [T.TEXTO, T.SALTO_LINEA, T.FIN_ARCHIVO])

    def test_el_analisis_continua_despues_de_cada_error(self):
        texto = "**uno\n\n*dos\n\n`tres\n\n####### cuatro\n\n# Valido\n"
        tokens, errores = tokenizar(texto)
        self.assertEqual(
            [e.tipo for e in errores],
            [
                TipoError.NEGRITA_SIN_CERRAR,
                TipoError.CURSIVA_SIN_CERRAR,
                TipoError.CODIGO_INLINE_SIN_CERRAR,
                TipoError.ENCABEZADO_INVALIDO,
            ],
        )
        self.assertIn(T.NUMERAL, tipos(tokens))

    def test_delimitador_cerrado_en_otra_linea_del_parrafo(self):
        tokens, errores = tokenizar("inicio **negrita\nque continua** fin\n")
        self.assertEqual(errores, [])
        self.assertEqual(tipos(tokens).count(T.NEGRITA), 2)

    def test_cada_linea_de_item_es_un_bloque(self):
        _, errores = tokenizar("- **a\n- b**\n")
        self.assertEqual(
            [(e.tipo, e.linea) for e in errores],
            [(TipoError.NEGRITA_SIN_CERRAR, 1), (TipoError.NEGRITA_SIN_CERRAR, 2)],
        )


class PruebasCasosBorde(unittest.TestCase):

    def test_archivo_vacio(self):
        tokens, errores = tokenizar("")
        self.assertEqual(errores, [])
        self.assertEqual([(t.tipo, t.linea, t.columna) for t in tokens], [(T.FIN_ARCHIVO, 1, 1)])

    def test_sin_salto_de_linea_final(self):
        tokens, _ = tokenizar("# Titulo")
        self.assertEqual(tipos(tokens), [T.NUMERAL, T.TEXTO, T.SALTO_LINEA, T.FIN_ARCHIVO])

    def test_finales_de_linea_de_windows(self):
        tokens, _ = tokenizar("# A\r\n\r\ntexto\r\n")
        self.assertEqual(
            [(t.tipo, t.linea, t.columna) for t in tokens],
            [
                (T.NUMERAL, 1, 1), (T.TEXTO, 1, 3), (T.SALTO_LINEA, 1, 4),
                (T.SALTO_PARRAFO, 2, 1),
                (T.TEXTO, 3, 1), (T.SALTO_LINEA, 3, 6),
                (T.FIN_ARCHIVO, 4, 1),
            ],
        )

    def test_marca_bom(self):
        tokens, _ = tokenizar("﻿# A\n")
        self.assertEqual((tokens[0].tipo, tokens[0].columna), (T.NUMERAL, 1))

    def test_lineas_en_blanco_consecutivas(self):
        tokens, _ = tokenizar("a\n\n  \n\t\nb\n")
        saltos = [t for t in tokens if t.tipo == T.SALTO_PARRAFO]
        self.assertEqual(len(saltos), 1)
        self.assertEqual(saltos[0].lexema, "\n\n\n")

    def test_parrafo_de_varias_lineas(self):
        tokens, _ = tokenizar("linea uno\nlinea dos\n")
        self.assertEqual(tipos(tokens), [T.TEXTO, T.SALTO_LINEA, T.FIN_ARCHIVO])
        self.assertEqual(tokens[0].lexema, "linea uno\nlinea dos")
        self.assertEqual(tokens[1].linea, 2)

    def test_siguiente_token_despues_del_fin(self):
        lexico = AnalizadorLexico("a\n", GestorErrores())
        lexico.analizar_todo()
        self.assertEqual(lexico.siguiente_token().tipo, T.FIN_ARCHIVO)
        self.assertEqual(len(lexico.tokens), 3)

    def test_bloque_de_codigo_vacio(self):
        tokens, errores = tokenizar("```\n```\n")
        self.assertEqual(errores, [])
        self.assertNotIn(T.TEXTO_LITERAL, tipos(tokens))

    def test_no_se_usa_el_modulo_re(self):
        ruta = os.path.join(DIRECTORIO_PROYECTO, "src", "analizador", "analizador_lexico.py")
        with open(ruta, encoding="utf-8") as archivo:
            codigo = archivo.read()
        self.assertNotIn("import re", codigo)
        self.assertNotIn("from re ", codigo)


if __name__ == "__main__":
    unittest.main()
