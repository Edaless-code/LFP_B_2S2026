"""Prueba de extremo a extremo: carga, analisis, choques y reportes HTML."""

import os
import sys

DIRECTORIO_PROYECTO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(DIRECTORIO_PROYECTO, "src"))

from analizador.analizador_lexico import AnalizadorLexico
from analizador.gestor_errores import GestorErrores
from horario.constructor_horario import ConstructorHorario
from horario.detector_choques import DetectorChoques
from reportes.generador_reportes import GeneradorReportes
from servicios.cargador_archivos import CargadorArchivos, ErrorDeCarga

DIRECTORIO_ENTRADAS = os.path.join(DIRECTORIO_PROYECTO, "entradas")
DIRECTORIO_SALIDAS = os.path.join(DIRECTORIO_PROYECTO, "salidas")


def procesar(nombre: str):
    """Ejecuta el flujo completo sobre un archivo de entrada."""
    ruta = os.path.join(DIRECTORIO_ENTRADAS, f"{nombre}.hor")
    texto = CargadorArchivos.cargar(ruta)

    gestor = GestorErrores()
    tokens = AnalizadorLexico(texto, gestor).analizar_todo()

    horario = ConstructorHorario(tokens).construir()
    detector = DetectorChoques(horario)
    choques = detector.detectar()

    generador = GeneradorReportes(os.path.join(DIRECTORIO_SALIDAS, nombre))
    rutas = generador.generar_todos(
        horario, choques, detector.clases_en_choque(), gestor.errores
    )
    return tokens, gestor, horario, choques, rutas


def probar_validacion_de_carga() -> None:
    """La carga debe rechazar rutas inexistentes y extensiones incorrectas."""
    for ruta in ("no_existe.hor", os.path.join(DIRECTORIO_ENTRADAS, "x.txt")):
        try:
            CargadorArchivos.cargar(ruta)
        except ErrorDeCarga:
            continue
        raise AssertionError(f"se esperaba ErrorDeCarga para {ruta}")
    assert CargadorArchivos.validar_extension("a/b/horario.HOR")
    assert not CargadorArchivos.validar_extension("horario.txt")
    print("validacion de carga: OK")


def probar_archivo_valido() -> None:
    """El archivo valido no debe producir errores ni choques."""
    tokens, gestor, horario, choques, rutas = procesar("horario_valido")
    assert gestor.total == 0, [e.descripcion for e in gestor.errores]
    assert len(choques) == 0, [c.descripcion for c in choques]
    assert len(horario.cursos) == 3 and len(horario.catedraticos) == 3
    assert len(horario.aulas) == 3 and len(horario.clases) == 6
    assert len(rutas) == 4
    for ruta in rutas.values():
        assert os.path.exists(ruta), ruta
    print(f"archivo valido: OK ({len(tokens)} tokens)")


def probar_archivo_con_choques() -> None:
    """El archivo con conflictos debe reportar un choque de cada tipo."""
    _, gestor, _, choques, _ = procesar("horario_choques")
    assert gestor.total == 0, [e.descripcion for e in gestor.errores]
    assert len(choques) == 2, [c.descripcion for c in choques]
    tipos = {c.tipo for c in choques}
    assert tipos == {"CATEDRATICO", "AULA"}, tipos
    print("archivo con choques: OK (2 choques)")


def probar_archivo_con_errores() -> None:
    """El archivo con errores debe cubrir las siete categorias."""
    _, gestor, _, _, rutas = procesar("horario_errores")
    categorias = {error.tipo.value for error in gestor.errores}
    esperadas = {
        "CARACTER_NO_RECONOCIDO", "CADENA_SIN_CERRAR", "HORA_FUERA_DE_RANGO",
        "DIA_NO_RECONOCIDO", "CODIGO_MAL_FORMADO", "CATEGORIA_NO_RECONOCIDA",
        "PALABRA_NO_RECONOCIDA",
    }
    assert categorias == esperadas, categorias
    assert gestor.total == 8, gestor.total
    assert os.path.exists(rutas["errores"])
    print(f"archivo con errores: OK ({gestor.total} errores, 7 categorias)")


def main() -> None:
    """Ejecuta el flujo completo sobre los tres archivos de ejemplo."""
    probar_validacion_de_carga()
    probar_archivo_valido()
    probar_archivo_con_choques()
    probar_archivo_con_errores()
    print(f"\nReportes generados en: {DIRECTORIO_SALIDAS}")
    print("Todas las pruebas de reportes pasaron.")


if __name__ == "__main__":
    main()
