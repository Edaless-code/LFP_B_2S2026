import sys
import os

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from services.cargador_archivos import CargadorArchivos
from services.validador_sudoku import ValidadorSudoku
from services.calculadora_metricas import CalculadoraMetricas
from reports.generador_html import (
    generar_reporte_sudokus,
    generar_reporte_jugadores,
    generar_reporte_top10,
)
from ui.menu import mostrar_menu


def main():
    directorio_proyecto = os.path.dirname(os.path.abspath(__file__))
    directorio_data = os.path.join(directorio_proyecto, "data")
    directorio_reportes = os.path.join(directorio_proyecto, "reportes")
    os.makedirs(directorio_reportes, exist_ok=True)

    cargador = CargadorArchivos()
    validador = ValidadorSudoku()
    calculadora = CalculadoraMetricas()

    sudokus = {}
    jugadores = {}
    intentos = []

    while True:
        opcion = mostrar_menu()

        if opcion == "1":
            try:
                ruta = os.path.join(directorio_data, "sudokus.lfp")
                sudokus = cargador.cargar_sudokus(ruta)
                print(f"Se cargaron {len(sudokus)} sudokus correctamente.")
            except FileNotFoundError:
                print("Error: no se encontro el archivo data/sudokus.lfp")

        elif opcion == "2":
            try:
                ruta = os.path.join(directorio_data, "jugadores.lfp")
                jugadores = cargador.cargar_jugadores(ruta)
                print(f"Se cargaron {len(jugadores)} jugadores correctamente.")
            except FileNotFoundError:
                print("Error: no se encontro el archivo data/jugadores.lfp")

        elif opcion == "3":
            try:
                ruta = os.path.join(directorio_data, "intentos.lfp")
                intentos = cargador.cargar_intentos(ruta)
                print(f"Se cargaron {len(intentos)} intentos correctamente.")
            except FileNotFoundError:
                print("Error: no se encontro el archivo data/intentos.lfp")

        elif opcion == "4":
            if not sudokus or not intentos:
                print("Debe cargar los sudokus y los intentos antes de validar.")
            else:
                for intento in intentos:
                    tablero = sudokus.get(intento.id_sudoku)
                    if tablero is not None:
                        validador.validar_y_calificar(tablero, intento)
                print("Intentos validados y calificados correctamente.")

        elif opcion == "5":
            if not sudokus or not intentos:
                print("Debe cargar y validar los datos antes de generar el reporte.")
            else:
                resumen = calculadora.resumen_por_sudoku(sudokus, intentos)
                ruta_salida = os.path.join(directorio_reportes, "reporte_sudokus.html")
                generar_reporte_sudokus(resumen, ruta_salida)
                print(f"Reporte generado en: {ruta_salida}")

        elif opcion == "6":
            if not jugadores or not intentos:
                print("Debe cargar y validar los datos antes de generar el reporte.")
            else:
                rendimiento = calculadora.rendimiento_por_jugador(jugadores, intentos)
                ruta_salida = os.path.join(directorio_reportes, "reporte_jugadores.html")
                generar_reporte_jugadores(rendimiento, ruta_salida)
                print(f"Reporte generado en: {ruta_salida}")

        elif opcion == "7":
            if not sudokus or not jugadores or not intentos:
                print("Debe cargar y validar los datos antes de generar el reporte.")
            else:
                top10 = calculadora.top_10_mejores_tiempos(intentos, sudokus, jugadores)
                ruta_salida = os.path.join(directorio_reportes, "reporte_top10.html")
                generar_reporte_top10(top10, ruta_salida)
                print(f"Reporte generado en: {ruta_salida}")

        elif opcion == "8":
            print("Gracias por usar el sistema. Hasta pronto.")
            break

        else:
            print("Opcion invalida, intente de nuevo.")

        print()


if __name__ == "__main__":
    main()