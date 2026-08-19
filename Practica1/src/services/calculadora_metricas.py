import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.cargador_archivos import CargadorArchivos
from services.validador_sudoku import ValidadorSudoku

class CalculadoraMetricas:


    def resumen_por_sudoku(self, sudokus, intentos):
        resumen = []
        for id_sudoku, tablero in sudokus.items():
            intentos_de_este = [i for i in intentos if i.id_sudoku == id_sudoku]
            cantidad = len(intentos_de_este)

            if cantidad == 0:
                tiempo_promedio = 0
                tasa_exito = 0
            else:
                tiempo_promedio = round(sum(i.tiempo_segundos for i in intentos_de_este) / cantidad, 2)
                exitosos = sum(1 for i in intentos_de_este if i.resuelto_correctamente)
                tasa_exito = round((exitosos / cantidad) * 100, 2)

                pass

            resumen.append({
                "id_sudoku": id_sudoku,
                "dificultad": tablero.dificultad,
                "cantidad_intentos": cantidad,
                "tiempo_promedio": tiempo_promedio,
                "tasa_exito": tasa_exito,
            })
        return resumen


    def rendimiento_por_jugador(self, jugadores, intentos):
        resumen = []
        for carnet, jugador in jugadores.items():
            intentos_de_este = [i for i in intentos if i.carnet == carnet]
            tableros_intentados = set(i.id_sudoku for i in intentos_de_este)
            cantidad_tableros = len(tableros_intentados)

            if len(intentos_de_este) == 0:
                validez_promedio = 0
                tiempo_promedio = 0
                resueltos_perfectos = 0
            else:

                validez_promedio = round(sum(i.porcentaje_validez for i in intentos_de_este) / len(intentos_de_este), 2)
                tiempo_promedio = round(sum(i.tiempo_segundos for i in intentos_de_este) / len(intentos_de_este), 2)
                resueltos_perfectos = sum(1 for i in intentos_de_este if i.resuelto_correctamente)


            resumen.append({
                "carnet": carnet,
                "nombre_completo": jugador.nombre_completo(),
                "nivel": jugador.nivel,
                "cantidad_tableros": cantidad_tableros,
                "validez_promedio": validez_promedio,
                "tiempo_promedio": tiempo_promedio,
                "resueltos_perfectos": resueltos_perfectos,
            })
        return resumen

    def top_10_mejores_tiempos(self, intentos, sudokus, jugadores):
        exitosos = [i for i in intentos if i.resuelto_correctamente]
        exitosos_ordenados = sorted(exitosos, key=lambda i: i.tiempo_segundos)
        top10 = exitosos_ordenados[:10]

        resultado = []
        for posicion, intento in enumerate(top10, start=1):
            jugador = jugadores.get(intento.carnet)
            tablero = sudokus.get(intento.id_sudoku)
            resultado.append({
                "posicion": posicion,
                "carnet": intento.carnet,
                "nombre_completo": jugador.nombre_completo(),
                "id_sudoku": intento.id_sudoku,
                "dificultad": tablero.dificultad,
                "tiempo_segundos": intento.tiempo_segundos,
            })
        return resultado


if __name__ == "__main__":
    directorio_actual = os.path.dirname(os.path.abspath(__file__))
    directorio_proyecto = os.path.dirname(os.path.dirname(directorio_actual))

    c = CargadorArchivos()
    sudokus = c.cargar_sudokus(os.path.join(directorio_proyecto, "data", "sudokus.lfp"))
    intentos = c.cargar_intentos(os.path.join(directorio_proyecto, "data", "intentos.lfp"))

    validador = ValidadorSudoku()
    for intento in intentos:
        tablero = sudokus.get(intento.id_sudoku)
        if tablero is not None:
            validador.validar_y_calificar(tablero, intento)

    cm = CalculadoraMetricas()
    resumen = cm.resumen_por_sudoku(sudokus, intentos)
    for fila in resumen:
        print(fila)

    jugadores = c.cargar_jugadores(os.path.join(directorio_proyecto, "data", "jugadores.lfp"))   
    rendimiento = cm.rendimiento_por_jugador(jugadores, intentos)
    for fila in rendimiento:
        print(fila)  

        top10 = cm.top_10_mejores_tiempos(intentos, sudokus, jugadores)
    for fila in top10:
        print(fila)