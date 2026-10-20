"""Pruebas unitarias del analizador sintactico y del arbol de derivacion.

Ejecutar desde la carpeta Proyecto2:
    python -m unittest discover -s tests -v
"""

import os
import sys
import unittest

DIRECTORIO_PROYECTO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(DIRECTORIO_PROYECTO, "src"))

from analizador.analizador_lexico import AnalizadorLexico
from analizador.analizador_sintactico import AnalizadorSintactico
from analizador.gestor_errores import GestorErrores
from modelos.error_analisis import Fase, TipoError

OMITIDOS = {"SALTO_LINEA", "SALTO_PARRAFO", "FIN_ARCHIVO"}


def analizar(texto: str):
    """Ejecuta el analisis completo y devuelve (raiz, errores, lexico)."""
    gestor = GestorErrores()
    lexico = AnalizadorLexico(texto, gestor)
    raiz = AnalizadorSintactico(lexico, gestor).analizar()
    return raiz, gestor.errores, lexico


def forma(nodo) -> str:
    """Representacion compacta del arbol, sin saltos de linea ni separadores.

    Los no terminales se escriben con su nombre y sus hijos entre parentesis;
    los terminales con su tipo. Ejemplo: parrafo(en_linea(TEXTO)).
    """
    if nodo.es_terminal:
        return nodo.simbolo
    hijos = [forma(hijo) for hijo in nodo.hijos if hijo.simbolo not in OMITIDOS]
    hijos = [hijo for hijo in hijos if hijo != "bloque(separador())"]
    nombre = nodo.simbolo[1:-1]
    return f"{nombre}({','.join(hijos)})"


def buscar(nodo, simbolo: str) -> list:
    """Todos los nodos con ese simbolo, en preorden."""
    encontrados = [nodo] if nodo.simbolo == simbolo else []
    for hijo in nodo.hijos:
        encontrados.extend(buscar(hijo, simbolo))
    return encontrados


def profundidad(nodo, simbolo: str) -> int:
    """Maxima cantidad de nodos con ese simbolo anidados en una misma rama."""
    propio = 1 if nodo.simbolo == simbolo else 0
    return propio + max((profundidad(hijo, simbolo) for hijo in nodo.hijos), default=0)


class PruebasArchivoEjemplo(unittest.TestCase):
    """Archivo de la seccion 4.7 del enunciado."""

    @classmethod
    def setUpClass(cls):
        ruta = os.path.join(DIRECTORIO_PROYECTO, "examples", "ejemplo_valido.md")
        with open(ruta, encoding="utf-8") as archivo:
            cls.raiz, cls.errores, cls.lexico = analizar(archivo.read())

    def test_sin_errores(self):
        self.assertEqual(self.errores, [])

    def test_raiz_es_documento(self):
        self.assertEqual(self.raiz.simbolo, "<documento>")
        self.assertEqual(self.raiz.hijos[-1].simbolo, "FIN_ARCHIVO")

    def test_secuencia_de_bloques(self):
        bloques = [
            bloque.hijos[0].simbolo
            for bloque in self.raiz.hijos
            if bloque.simbolo == "<bloque>" and bloque.hijos[0].simbolo != "<separador>"
        ]
        self.assertEqual(
            bloques,
            [
                "<encabezado>", "<parrafo>", "<encabezado>", "<lista>",
                "<cita>", "<bloque_codigo>", "<regla_horizontal>", "<parrafo>",
            ],
        )

    def test_lista_con_tres_niveles(self):
        self.assertEqual(profundidad(self.raiz, "<lista>"), 3)
        self.assertEqual(len(buscar(self.raiz, "<item_lista>")), 8)

    def test_cita_con_dos_niveles(self):
        self.assertEqual(profundidad(self.raiz, "<cita>"), 2)

    def test_parrafo_combina_elementos_en_linea(self):
        parrafo = buscar(self.raiz, "<parrafo>")[0]
        self.assertEqual(
            forma(parrafo),
            "parrafo(en_linea(TEXTO,negrita(NEGRITA,en_linea(TEXTO),NEGRITA),TEXTO,"
            "cursiva(CURSIVA,en_linea(TEXTO),CURSIVA),TEXTO,"
            "codigo_inline(CODIGO_INLINE,TEXTO_LITERAL,CODIGO_INLINE),TEXTO))",
        )

    def test_todos_los_tokens_quedan_en_el_arbol(self):
        hojas = []

        def recolectar(nodo):
            if nodo.es_terminal:
                hojas.append(nodo.token)
            for hijo in nodo.hijos:
                recolectar(hijo)

        recolectar(self.raiz)
        self.assertEqual(hojas, self.lexico.tokens)


class PruebasEstructura(unittest.TestCase):

    def test_documento_vacio(self):
        raiz, errores, _ = analizar("")
        self.assertEqual(errores, [])
        self.assertEqual(forma(raiz), "documento()")

    def test_encabezado(self):
        raiz, _, _ = analizar("## Titulo\n")
        self.assertEqual(forma(raiz), "documento(bloque(encabezado(NUMERAL,en_linea(TEXTO))))")

    def test_sublista_dentro_de_item(self):
        raiz, errores, _ = analizar("- a\n  - b\n- c\n")
        self.assertEqual(errores, [])
        self.assertEqual(
            forma(raiz),
            "documento(bloque(lista("
            "item_lista(VIÑETA,en_linea(TEXTO),sublista(INDENT,lista(item_lista(VIÑETA,en_linea(TEXTO))),DEDENT)),"
            "item_lista(VIÑETA,en_linea(TEXTO)))))",
        )

    def test_cuatro_niveles_de_lista(self):
        raiz, errores, _ = analizar("- 1\n  - 2\n    - 3\n      - 4\n")
        self.assertEqual(errores, [])
        self.assertEqual(profundidad(raiz, "<lista>"), 4)

    def test_cita_que_sube_y_baja_de_nivel(self):
        raiz, errores, _ = analizar("> a\n>> b\n> c\n")
        self.assertEqual(errores, [])
        self.assertEqual(
            forma(raiz),
            "documento(bloque(cita("
            "linea_cita(CITA,en_linea(TEXTO)),"
            "cita(linea_cita(CITA,en_linea(TEXTO))),"
            "linea_cita(CITA,en_linea(TEXTO)))))",
        )

    def test_notacion_con_espacio_equivale_a_doble_mayor(self):
        con_espacio, _, _ = analizar("> a\n> > b\n")
        sin_espacio, _, _ = analizar("> a\n>> b\n")
        self.assertEqual(forma(con_espacio), forma(sin_espacio))

    def test_cita_que_empieza_en_nivel_tres(self):
        raiz, _, _ = analizar(">>> x\n")
        self.assertEqual(profundidad(raiz, "<cita>"), 3)

    def test_negrita_dentro_de_cursiva(self):
        raiz, errores, _ = analizar("*a **b** c*\n")
        self.assertEqual(errores, [])
        self.assertEqual(
            forma(raiz),
            "documento(bloque(parrafo(en_linea(cursiva(CURSIVA,en_linea("
            "TEXTO,negrita(NEGRITA,en_linea(TEXTO),NEGRITA),TEXTO),CURSIVA)))))",
        )

    def test_cursiva_dentro_de_negrita_con_tres_asteriscos(self):
        raiz, errores, _ = analizar("***a***\n")
        self.assertEqual(errores, [])
        self.assertEqual(
            forma(raiz),
            "documento(bloque(parrafo(en_linea(negrita(NEGRITA,en_linea("
            "cursiva(CURSIVA,en_linea(TEXTO),CURSIVA)),NEGRITA)))))",
        )

    def test_elementos_en_linea_dentro_de_item_y_cita(self):
        raiz, errores, _ = analizar("- **a** y `b`\n\n> *c*\n")
        self.assertEqual(errores, [])
        self.assertEqual(len(buscar(raiz, "<negrita>")), 1)
        self.assertEqual(len(buscar(raiz, "<codigo_inline>")), 1)
        self.assertEqual(len(buscar(raiz, "<cursiva>")), 1)

    def test_bloque_de_codigo_sin_lenguaje(self):
        raiz, errores, _ = analizar("```\nx\n```\n")
        self.assertEqual(errores, [])
        self.assertEqual(
            forma(raiz),
            "documento(bloque(bloque_codigo(CERCA_CODIGO,TEXTO_LITERAL,CERCA_CODIGO)))",
        )

    def test_el_parser_pide_tokens_bajo_demanda(self):
        gestor = GestorErrores()
        lexico = AnalizadorLexico("# a\n\nb\n", gestor)
        AnalizadorSintactico(lexico, gestor)
        self.assertEqual(len(lexico.tokens), 1)


class PruebasErroresSintacticos(unittest.TestCase):
    """Categorias sintacticas de la seccion 4.9 del enunciado."""

    def test_indentacion_que_salta_un_nivel(self):
        raiz, errores, _ = analizar("- a\n    - b\n- c\n")
        self.assertEqual(
            [(e.tipo, e.fase, e.linea, e.columna) for e in errores],
            [(TipoError.INDENTACION_INVALIDA, Fase.SINTACTICO, 2, 5)],
        )
        self.assertEqual(errores[0].descripcion, "Indentación inválida en línea 2, columna 5")
        self.assertEqual(len(buscar(raiz, "<item_lista>")), 3)

    def test_indentacion_inconsistente_al_regresar(self):
        _, errores, _ = analizar("- a\n  - b\n - c\n")
        self.assertEqual(
            [(e.tipo, e.linea, e.columna) for e in errores],
            [(TipoError.INDENTACION_INVALIDA, 3, 2)],
        )

    def test_items_hermanos_con_distinta_sangria(self):
        _, errores, _ = analizar("  - a\n- b\n")
        self.assertEqual([(e.tipo, e.linea) for e in errores], [(TipoError.INDENTACION_INVALIDA, 2)])

    def test_cita_mal_formada(self):
        raiz, errores, _ = analizar(">texto\n")
        self.assertEqual(
            [(e.tipo, e.fase, e.linea, e.columna, e.descripcion) for e in errores],
            [(TipoError.CITA_MAL_FORMADA, Fase.SINTACTICO, 1, 1, "Cita mal formada en línea 1, columna 1")],
        )
        self.assertEqual(len(buscar(raiz, "<linea_cita>")), 1)

    def test_cita_doble_mal_formada_reporta_el_ultimo_mayor(self):
        _, errores, _ = analizar(">>texto\n")
        self.assertEqual([(e.tipo, e.columna) for e in errores], [(TipoError.CITA_MAL_FORMADA, 2)])

    def test_citas_bien_formadas(self):
        _, errores, _ = analizar("> a\n>> b\n> > c\n>\n")
        self.assertEqual(errores, [])

    def test_bloque_sin_cerrar_se_reporta_una_sola_vez(self):
        raiz, errores, _ = analizar("```python\nx = 1\n")
        self.assertEqual([e.tipo for e in errores], [TipoError.BLOQUE_CODIGO_SIN_CERRAR])
        self.assertEqual(len(buscar(raiz, "<bloque_codigo>")), 1)

    def test_delimitador_sin_cerrar_no_genera_error_sintactico(self):
        _, errores, _ = analizar("texto **sin cerrar\n")
        self.assertEqual([e.fase for e in errores], [Fase.LEXICO])

    def test_todos_los_errores_en_una_sola_pasada_y_ordenados(self):
        texto = (
            "####### Encabezado\n"
            "\n"
            "Texto **sin cierre\n"
            "\n"
            "- a\n"
            "    - salto\n"
            "\n"
            ">sin espacio\n"
            "\n"
            "# Sigue *abierta\n"
            "\n"
            "```\n"
            "nunca cierra\n"
        )
        _, errores, _ = analizar(texto)
        self.assertEqual(
            [(e.numero, e.tipo, e.linea) for e in errores],
            [
                (1, TipoError.ENCABEZADO_INVALIDO, 1),
                (2, TipoError.NEGRITA_SIN_CERRAR, 3),
                (3, TipoError.INDENTACION_INVALIDA, 6),
                (4, TipoError.CITA_MAL_FORMADA, 8),
                (5, TipoError.CURSIVA_SIN_CERRAR, 10),
                (6, TipoError.BLOQUE_CODIGO_SIN_CERRAR, 12),
            ],
        )


if __name__ == "__main__":
    unittest.main()
