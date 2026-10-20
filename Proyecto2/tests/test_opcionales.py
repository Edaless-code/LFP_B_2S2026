"""Pruebas unitarias del alcance opcional.

Listas ordenadas, listas de tareas, tachado, enlaces, imagenes, resaltado de
sintaxis y advertencias de anidamiento.

Ejecutar desde la carpeta Proyecto2:
    python -m unittest discover -s tests -v
"""

import os
import sys
import unittest

DIRECTORIO_PROYECTO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(DIRECTORIO_PROYECTO, "src"))

from analizador.advertencias import TIPO_CITA, TIPO_LISTA, buscar_anidamiento_excesivo
from analizador.analizador_lexico import AnalizadorLexico
from analizador.analizador_sintactico import AnalizadorSintactico
from analizador.gestor_errores import GestorErrores
from modelos.error_analisis import TipoError
from modelos.tipo_token import TipoToken as T
from reportes.generador_html import GeneradorHTML, URL_HIGHLIGHT
from reportes.reporte_estadisticas import calcular_estadisticas


def tokenizar(texto: str):
    gestor = GestorErrores()
    tokens = AnalizadorLexico(texto, gestor).analizar_todo()
    return [(t.tipo, t.lexema) for t in tokens if t.tipo not in (T.SALTO_LINEA, T.FIN_ARCHIVO)], gestor.errores


def analizar(texto: str):
    gestor = GestorErrores()
    raiz = AnalizadorSintactico(AnalizadorLexico(texto, gestor), gestor).analizar()
    return raiz, gestor.errores


def html(texto: str) -> str:
    raiz, errores = analizar(texto)
    assert errores == [], errores
    return GeneradorHTML(raiz).generar_cuerpo()


class PruebasListasOrdenadas(unittest.TestCase):

    def test_tokens(self):
        tokens, errores = tokenizar("1. uno\n10. diez\n")
        self.assertEqual(errores, [])
        self.assertEqual(tokens, [(T.ENUMERADOR, "1."), (T.TEXTO, "uno"), (T.ENUMERADOR, "10."), (T.TEXTO, "diez")])

    def test_numero_sin_espacio_o_a_mitad_de_linea_es_texto(self):
        tokens, _ = tokenizar("1.sinespacio\n\nEn 2024. fue\n")
        self.assertNotIn(T.ENUMERADOR, [tipo for tipo, _ in tokens])

    def test_html_ol_con_numero_inicial(self):
        self.assertEqual(html("1. a\n2. b\n"), "<ol>\n<li>a</li>\n<li>b</li>\n</ol>\n")
        self.assertIn('<ol start="5">', html("5. a\n6. b\n"))

    def test_lista_ordenada_anidada_en_no_ordenada(self):
        self.assertEqual(
            html("- a\n  1. b\n  2. c\n- d\n"),
            "<ul>\n<li>a\n<ol>\n<li>b</li>\n<li>c</li>\n</ol>\n</li>\n<li>d</li>\n</ul>\n",
        )

    def test_cambio_de_marcador_inicia_otra_lista(self):
        raiz, errores = analizar("- a\n1. b\n")
        self.assertEqual(errores, [])
        self.assertEqual(len([b for b in raiz.hijos if b.simbolo == "<bloque>"]), 2)

    def test_sublista_con_dos_tipos_de_marcador(self):
        resultado = html("- a\n  - b\n  1. c\n")
        self.assertIn("<ul>\n<li>b</li>\n</ul>\n<ol>\n<li>c</li>\n</ol>", resultado)

    def test_la_indentacion_se_valida_igual(self):
        _, errores = analizar("1. a\n     2. b\n")
        self.assertEqual([e.tipo for e in errores], [TipoError.INDENTACION_INVALIDA])


class PruebasListasDeTareas(unittest.TestCase):

    def test_tokens(self):
        tokens, _ = tokenizar("- [ ] pendiente\n- [x] hecha\n- [X] tambien\n")
        casillas = [lexema for tipo, lexema in tokens if tipo == T.CASILLA]
        self.assertEqual(casillas, ["[ ]", "[x]", "[X]"])

    def test_casilla_sin_espacio_es_texto(self):
        tokens, _ = tokenizar("- [x]pegado\n")
        self.assertNotIn(T.CASILLA, [tipo for tipo, _ in tokens])

    def test_html(self):
        resultado = html("- [ ] uno\n- [x] dos\n")
        self.assertIn('<li class="tarea"><input type="checkbox" disabled>uno</li>', resultado)
        self.assertIn('<li class="tarea"><input type="checkbox" disabled checked>dos</li>', resultado)

    def test_estadisticas(self):
        estadisticas = calcular_estadisticas(analizar("- [ ] a\n- [x] b\n- [x] c\n- d\n")[0])
        self.assertEqual((estadisticas.tareas, estadisticas.tareas_completadas), (3, 2))


class PruebasTachado(unittest.TestCase):

    def test_html_y_combinaciones(self):
        self.assertIn("<del>viejo</del>", html("~~viejo~~\n"))
        self.assertIn("<del>a <strong>b</strong></del>", html("~~a **b**~~\n"))

    def test_una_virgulilla_es_texto(self):
        tokens, errores = tokenizar("aprox ~5 km\n")
        self.assertEqual((tokens, errores), ([(T.TEXTO, "aprox ~5 km")], []))

    def test_tachado_sin_cerrar(self):
        _, errores = analizar("texto ~~abierto\n")
        self.assertEqual(
            [(e.tipo, e.linea, e.columna, e.descripcion) for e in errores],
            [(TipoError.TACHADO_SIN_CERRAR, 1, 7, "Tachado sin cerrar iniciado en línea 1, columna 7")],
        )


class PruebasEnlacesEImagenes(unittest.TestCase):

    def test_tokens_de_enlace(self):
        tokens, _ = tokenizar("[guia](https://a.com)\n")
        self.assertEqual(
            tokens,
            [(T.CORCHETE_ABRE, "["), (T.TEXTO, "guia"), (T.CORCHETE_CIERRA, "]"), (T.URL, "(https://a.com)")],
        )

    def test_tokens_de_imagen(self):
        tokens, _ = tokenizar("![logo](img/logo.png)\n")
        self.assertEqual(
            tokens,
            [(T.IMAGEN_ABRE, "!["), (T.TEXTO, "logo"), (T.CORCHETE_CIERRA, "]"), (T.URL, "(img/logo.png)")],
        )

    def test_corchetes_sin_patron_completo_son_texto(self):
        for texto in ("[solo corchetes]\n", "[a] (b)\n", "[a](con espacio)\n", "[a]()\n", "!importante\n"):
            tokens, errores = tokenizar(texto)
            self.assertEqual(([tipo for tipo, _ in tokens], errores), ([T.TEXTO], []), texto)

    def test_html_de_enlace_con_formato(self):
        self.assertEqual(
            html("Ver [la **guia**](https://a.com/?x=1&y=2).\n"),
            '<p>Ver <a href="https://a.com/?x=1&amp;y=2">la <strong>guia</strong></a>.</p>\n',
        )

    def test_html_de_imagen(self):
        self.assertIn('<img src="logo.png" alt="Logo &quot;MC&quot;">', html('![Logo "MC"](logo.png)\n'))

    def test_enlace_dentro_de_negrita_y_de_item(self):
        self.assertIn('<strong>ver <a href="u">aqui</a></strong>', html("**ver [aqui](u)**\n"))
        self.assertIn('<li><a href="u">item</a></li>', html("- [item](u)\n"))

    def test_enfasis_que_cruza_el_enlace_se_reporta(self):
        _, errores = analizar("*[a*](u)\n")
        self.assertEqual([e.tipo for e in errores], [TipoError.CURSIVA_SIN_CERRAR] * 2)

    def test_rutas_relativas_se_ajustan_a_la_carpeta_del_reporte(self):
        raiz, _ = analizar("![a](img/a.png) [b](https://b.com) [c](#seccion) [d](/abs/d.md)\n")
        resultado = GeneradorHTML(raiz, "../../examples").generar_cuerpo()
        self.assertIn('src="../../examples/img/a.png"', resultado)
        self.assertIn('href="https://b.com"', resultado)
        self.assertIn('href="#seccion"', resultado)
        self.assertIn('href="/abs/d.md"', resultado)

    def test_estadisticas(self):
        estadisticas = calcular_estadisticas(analizar("[a](u) y [b](v) y ![c](w)\n")[0])
        self.assertEqual((estadisticas.enlaces, estadisticas.imagenes), (2, 1))


class PruebasResaltadoDeSintaxis(unittest.TestCase):

    def test_se_incluye_solo_con_bloques_de_codigo(self):
        con_codigo = GeneradorHTML(analizar("```python\nx = 1\n```\n")[0]).generar_reporte("a.md")
        sin_codigo = GeneradorHTML(analizar("# Hola\n")[0]).generar_reporte("b.md")
        self.assertIn(f"{URL_HIGHLIGHT}/highlight.min.js", con_codigo)
        self.assertIn("hljs.highlightAll()", con_codigo)
        self.assertNotIn(URL_HIGHLIGHT, sin_codigo)


class PruebasAdvertenciasDeAnidamiento(unittest.TestCase):

    def test_lista_que_supera_el_maximo(self):
        raiz, _ = analizar("- 1\n  - 2\n    - 3\n      - 4\n")
        self.assertEqual(buscar_anidamiento_excesivo(raiz, 4), [])
        advertencias = buscar_anidamiento_excesivo(raiz, 2)
        self.assertEqual(
            [(a.tipo, a.nivel, a.linea, a.columna) for a in advertencias],
            [(TIPO_LISTA, 4, 3, 5)],
        )
        self.assertEqual(advertencias[0].descripcion, "lista de 4 niveles en la línea 3")

    def test_cita_que_supera_el_maximo(self):
        raiz, _ = analizar("> a\n>> b\n>>> c\n")
        advertencias = buscar_anidamiento_excesivo(raiz, 2)
        self.assertEqual([(a.tipo, a.nivel, a.linea) for a in advertencias], [(TIPO_CITA, 3, 3)])

    def test_archivo_de_ejemplo_dentro_del_limite_por_defecto(self):
        with open(os.path.join(DIRECTORIO_PROYECTO, "examples", "ejemplo_valido.md"), encoding="utf-8") as archivo:
            raiz, _ = analizar(archivo.read())
        self.assertEqual(buscar_anidamiento_excesivo(raiz, 3), [])


if __name__ == "__main__":
    unittest.main()
