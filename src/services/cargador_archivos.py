import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from models.tablero import Tablero
from models.jugador import Jugador
from models.intento import Intento
from services.validador_sudoku import ValidadorSudoku

class CargadorArchivos:

    def cargar_sudokus(self, ruta_archivo):
        sudokus = {}   # diccionario: id_sudoku -> objeto Tablero
        with open(ruta_archivo, "r") as archivo:
            lineas = archivo.readlines()
            for linea in lineas:
                linea = linea.strip()   # quita el salto de linea al final
                if linea == "":
                    continue            # ignora lineas vacias
                datos = linea.split(",")
                id_sudoku = datos[0]
                dificultad = datos[1]
                tablero_str = datos[2]
                tablero = Tablero(id_sudoku, dificultad, tablero_str)
                sudokus[tablero.id_sudoku] = tablero
        return sudokus

    def cargar_jugadores(self, ruta_archivo):
        jugadores = {}
        with open(ruta_archivo, "r") as archivo:
            lineas = archivo.readlines()
            for linea in lineas:
                linea = linea.strip()
                if linea == "":
                    continue
                datos = linea.split(",")
                carnet = datos[0]
                nombre = datos[1]
                apellido = datos[2]
                nivel = datos[3]
                jugador = Jugador(carnet, nombre, apellido, nivel)
                jugadores[jugador.carnet] = jugador
        return jugadores


    def cargar_intentos(self, ruta_archivo):
        intentos = []
        with open(ruta_archivo, "r") as archivo:
            lineas = archivo.readlines()
            for linea in lineas:
                linea = linea.strip()
                if linea == "":
                    continue
                datos = linea.split(",")
                carnet = datos[0]
                id_sudoku = datos[1]
                solucion = datos[2]
                tiempo_segundos = datos[3]
                fecha = datos[4]
                intento = Intento(carnet, id_sudoku, solucion, tiempo_segundos, fecha)
                intentos.append(intento)
        return intentos

if __name__ == "__main__":
    c = CargadorArchivos()

    directorio_actual = os.path.dirname(os.path.abspath(__file__))
    directorio_proyecto = os.path.dirname(os.path.dirname(directorio_actual))
    ruta_sudokus = os.path.join(directorio_proyecto, "data", "sudokus.lfp")

    sudokus = c.cargar_sudokus(ruta_sudokus)

    ruta_jugadores = os.path.join(directorio_proyecto, "data", "jugadores.lfp")
    ruta_intentos = os.path.join(directorio_proyecto, "data", "intentos.lfp")

    jugadores = c.cargar_jugadores(ruta_jugadores)
    intentos = c.cargar_intentos(ruta_intentos)

    validador = ValidadorSudoku()
    for intento in intentos:
        tablero = sudokus.get(intento.id_sudoku)
        if tablero is not None:
            validador.validar_y_calificar(tablero, intento)

    for intento in intentos:
        print(intento.carnet, intento.id_sudoku, intento.porcentaje_validez, intento.resuelto_correctamente)