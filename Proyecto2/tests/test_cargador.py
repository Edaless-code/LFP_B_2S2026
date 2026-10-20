"""Pruebas unitarias del cargador de archivos.

Ejecutar desde la carpeta Proyecto2:
    python -m unittest discover -s tests -v
"""

import os
import sys
import tempfile
import unittest

DIRECTORIO_PROYECTO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(DIRECTORIO_PROYECTO, "src"))

from servicios.cargador_archivos import CargadorArchivos, ErrorCarga


class PruebasCargador(unittest.TestCase):

    def setUp(self):
        self.directorio = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.directorio.cleanup()

    def ruta(self, nombre: str) -> str:
        return os.path.join(self.directorio.name, nombre)

    def test_carga_utf8(self):
        with open(self.ruta("a.md"), "w", encoding="utf-8") as archivo:
            archivo.write("# Análisis léxico\n")
        self.assertEqual(CargadorArchivos.cargar(self.ruta("a.md")), "# Análisis léxico\n")

    def test_carga_codificacion_de_windows(self):
        with open(self.ruta("b.md"), "wb") as archivo:
            archivo.write("Gramática".encode("cp1252"))
        self.assertEqual(CargadorArchivos.cargar(self.ruta("b.md")), "Gramática")

    def test_archivo_inexistente(self):
        with self.assertRaises(ErrorCarga):
            CargadorArchivos.cargar(self.ruta("no_existe.md"))

    def test_extension_invalida(self):
        with open(self.ruta("c.txt"), "w", encoding="utf-8") as archivo:
            archivo.write("texto")
        with self.assertRaises(ErrorCarga):
            CargadorArchivos.cargar(self.ruta("c.txt"))

    def test_directorio_no_es_archivo(self):
        os.mkdir(self.ruta("carpeta.md"))
        with self.assertRaises(ErrorCarga):
            CargadorArchivos.cargar(self.ruta("carpeta.md"))

    def test_guardar_y_volver_a_cargar(self):
        CargadorArchivos.guardar(self.ruta("d.md"), "- uno\n  - dos\n")
        self.assertEqual(CargadorArchivos.cargar(self.ruta("d.md")), "- uno\n  - dos\n")


if __name__ == "__main__":
    unittest.main()
