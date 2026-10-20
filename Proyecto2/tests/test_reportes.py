"""Pruebas unitarias de los reportes HTML y del archivo arbol.dot.

Ejecutar desde la carpeta Proyecto2:
    python -m unittest discover -s tests -v
"""

import os
import sys
import tempfile
import unittest

DIRECTORIO_PROYECTO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(DIRECTORIO_PROYECTO, "src"))

from analizador.analizador_lexico import AnalizadorLexico
from analizador.analizador_sintactico import AnalizadorSintactico
from analizador.gestor_errores import GestorErrores
from reportes.estilos import ARCHIVO_DOCUMENTO, ARCHIVO_DOT, ARCHIVO_ERRORES, ARCHIVO_ESTADISTICAS, ARCHIVO_INDICE
from reportes.generador_dot import generar_dot
from reportes.generador_html import GeneradorHTML, extraer_encabezados
from reportes.generador_reportes import GeneradorReportes
from reportes.reporte_estadisticas import calcular_estadisticas
from reportes.reporte_indice import generar_reporte_indice


def arbol(texto: str):
    gestor = GestorErrores()
    raiz = AnalizadorSintactico(AnalizadorLexico(texto, gestor), gestor).analizar()
    return raiz, gestor.errores


def html(texto: str) -> str:
    return GeneradorHTML(arbol(texto)[0]).generar_cuerpo()


def leer_ejemplo() -> str:
    with open(os.path.join(DIRECTORIO_PROYECTO, "examples", "ejemplo_valido.md"), encoding="utf-8") as archivo:
        return archivo.read()


def contar_nodos(nodo) -> int:
    return 1 + sum(contar_nodos(hijo) for hijo in nodo.hijos)


class PruebasReporteDocumento(unittest.TestCase):
    """Reporte 1: HTML generado a partir del arbol."""

    def test_archivo_de_ejemplo(self):
        self.assertEqual(
            html(leer_ejemplo()),
            '<h1 id="proyecto-de-lenguajes-formales">Proyecto de Lenguajes Formales</h1>\n'
            "<p>Este curso combina <strong>teoría sólida</strong> y <em>práctica de código</em>, "
            "con ejemplos en <code>Python</code>.</p>\n"
            '<h2 id="contenido-del-curso">Contenido del curso</h2>\n'
            "<ul>\n"
            "<li>Análisis léxico\n<ul>\n<li>Autómatas finitos</li>\n<li>Expresiones regulares</li>\n</ul>\n</li>\n"
            "<li>Análisis sintáctico\n<ul>\n<li>Gramáticas libres de contexto\n<ul>\n"
            "<li>Recursión por la izquierda</li>\n<li>Recursión por la derecha</li>\n</ul>\n</li>\n</ul>\n</li>\n"
            "<li>Generación de código</li>\n"
            "</ul>\n"
            "<blockquote>\n<p>El análisis sintáctico es donde la teoría se encuentra con la práctica.</p>\n"
            "<blockquote>\n<p>Y donde más se aprende, según los estudiantes.</p>\n</blockquote>\n</blockquote>\n"
            '<pre><code class="language-python">def hola():\n    print("Hola LFP")</code></pre>\n'
            "<hr>\n"
            "<p>Fin del documento.</p>\n",
        )

    def test_seis_niveles_de_encabezado(self):
        resultado = html("# a\n## b\n### c\n#### d\n##### e\n###### f\n")
        for nivel in range(1, 7):
            self.assertIn(f"<h{nivel} ", resultado)

    def test_cursiva_dentro_de_negrita_y_viceversa(self):
        self.assertIn("<strong>negrita <em>y cursiva</em></strong>", html("**negrita *y cursiva***\n"))
        self.assertIn("<em>a <strong>b</strong> c</em>", html("*a **b** c*\n"))

    def test_codigo_en_linea_no_interpreta_markdown(self):
        self.assertIn("<code>**kwargs</code>", html("usa `**kwargs`\n"))

    def test_bloque_de_codigo_sin_lenguaje(self):
        self.assertIn("<pre><code>x = 1</code></pre>", html("```\nx = 1\n```\n"))

    def test_caracteres_especiales_se_escapan(self):
        resultado = html("a <b> & c\n\n```\n<script>alert(1)</script>\n```\n")
        self.assertIn("a &lt;b&gt; &amp; c", resultado)
        self.assertIn("&lt;script&gt;", resultado)
        self.assertNotIn("<script>", resultado)

    def test_reporte_completo_es_pagina_independiente(self):
        pagina = GeneradorHTML(arbol("# Hola\n")[0]).generar_reporte("prueba.md")
        self.assertTrue(pagina.startswith("<!DOCTYPE html>"))
        self.assertIn("<style>", pagina)
        self.assertIn("Análisis completado sin errores", pagina)


class PruebasAnclas(unittest.TestCase):

    def test_anclas_unicas_y_legibles(self):
        encabezados = extraer_encabezados(arbol("# Análisis léxico\n## Análisis léxico\n## **Negrita** y `código`\n")[0])
        self.assertEqual(
            [(e.nivel, e.texto, e.ancla) for e in encabezados],
            [
                (1, "Análisis léxico", "análisis-léxico"),
                (2, "Análisis léxico", "análisis-léxico-2"),
                (2, "Negrita y código", "negrita-y-código"),
            ],
        )

    def test_ids_del_reporte_1_coinciden_con_el_indice(self):
        raiz, _ = arbol(leer_ejemplo())
        generador = GeneradorHTML(raiz)
        documento = generador.generar_cuerpo()
        indice = generar_reporte_indice(generador.encabezados, "ejemplo_valido.md")
        for encabezado in generador.encabezados:
            self.assertIn(f'id="{encabezado.ancla}"', documento)
            self.assertIn(f'href="{ARCHIVO_DOCUMENTO}#{encabezado.ancla}"', indice)


class PruebasEstadisticas(unittest.TestCase):
    """Reporte 2: valores del ejemplo del enunciado (seccion 4.8)."""

    def test_archivo_de_ejemplo(self):
        e = calcular_estadisticas(arbol(leer_ejemplo())[0])
        self.assertEqual(e.palabras, 67)
        self.assertEqual(e.parrafos, 2)
        self.assertEqual(e.encabezados, 2)
        self.assertEqual(e.encabezados_por_nivel, [1, 1, 0, 0, 0, 0])
        self.assertEqual((e.listas, e.items_lista, e.profundidad_listas), (1, 8, 3))
        self.assertEqual((e.citas, e.lineas_cita, e.profundidad_citas), (1, 2, 2))
        self.assertEqual(e.bloques_codigo, 1)
        self.assertEqual((e.negritas, e.cursivas, e.codigos_inline, e.reglas), (1, 1, 1, 1))

    def test_documento_vacio(self):
        e = calcular_estadisticas(arbol("")[0])
        self.assertEqual((e.palabras, e.parrafos, e.encabezados, e.profundidad_listas), (0, 0, 0, 0))

    def test_listas_separadas_se_cuentan_por_separado(self):
        e = calcular_estadisticas(arbol("- a\n  - b\n\n- c\n")[0])
        self.assertEqual((e.listas, e.items_lista, e.profundidad_listas), (2, 3, 2))


class PruebasIndice(unittest.TestCase):
    """Reporte 3."""

    def test_documento_sin_encabezados(self):
        raiz, _ = arbol("Solo un parrafo.\n")
        indice = generar_reporte_indice(extraer_encabezados(raiz), "sin.md")
        self.assertIn("no contiene encabezados", indice)

    def test_sangria_segun_nivel(self):
        raiz, _ = arbol("# A\n### C\n")
        indice = generar_reporte_indice(extraer_encabezados(raiz), "x.md")
        self.assertIn("margin-left: 0px", indice)
        self.assertIn("margin-left: 44px", indice)


class PruebasArbolDot(unittest.TestCase):

    def test_estructura_del_archivo_dot(self):
        raiz, _ = arbol(leer_ejemplo())
        dot = generar_dot(raiz)
        total = contar_nodos(raiz)
        self.assertTrue(dot.startswith("digraph ArbolDerivacion {"))
        self.assertEqual(dot.count("[label="), total)
        self.assertEqual(dot.count(" -> "), total - 1)
        self.assertIn('n0 [label="<documento>", fillcolor="#2E75B6"', dot)

    def test_terminales_y_no_terminales_con_colores_distintos(self):
        dot = generar_dot(arbol("# Hola\n")[0])
        self.assertIn('[label="<encabezado>", fillcolor="#D6EAF8"]', dot)
        self.assertIn('[label="TEXTO\\nHola", fillcolor="#F9E79F"]', dot)

    def test_comillas_y_saltos_se_escapan(self):
        dot = generar_dot(arbol('Dijo "hola"\n')[0])
        self.assertIn('Dijo \\"hola\\"', dot)
        self.assertIn('[label="SALTO_LINEA\\n\\\\n"', dot)


class PruebasGeneradorReportes(unittest.TestCase):

    def setUp(self):
        self.temporal = tempfile.TemporaryDirectory()
        self.generador = GeneradorReportes(self.temporal.name)

    def tearDown(self):
        self.temporal.cleanup()

    def test_analisis_sin_errores_genera_los_reportes(self):
        salidas = self.generador.generar(arbol(leer_ejemplo())[0], "ejemplo_valido.md")
        self.assertEqual(salidas.directorio, os.path.join(self.temporal.name, "ejemplo_valido"))
        for archivo in (ARCHIVO_DOCUMENTO, ARCHIVO_ESTADISTICAS, ARCHIVO_INDICE, ARCHIVO_DOT):
            self.assertTrue(os.path.isfile(os.path.join(salidas.directorio, archivo)), archivo)
        self.assertIsNone(salidas.errores)

    def test_analisis_con_errores_solo_genera_el_reporte_de_errores(self):
        self.generador.generar(arbol("# Bien\n")[0], "caso.md")
        _, errores = arbol("**sin cerrar\n")
        salidas = self.generador.generar_errores(errores, "caso.md")
        self.assertEqual(os.listdir(salidas.directorio), [ARCHIVO_ERRORES])
        with open(salidas.errores, encoding="utf-8") as archivo:
            self.assertIn("NEGRITA_SIN_CERRAR", archivo.read())


if __name__ == "__main__":
    unittest.main()
