import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from models.tablero import Tablero
from models.jugador import Jugador
from models.intento import Intento
from services.validador_sudoku import ValidadorSudoku

class CargadorArchivos:

    def cargar_sudokus(self, ruta_archivo):
        sudokus = {}
        with open(ruta_archivo, "r") as archivo:
            lineas = archivo.readlines()
            for numero_linea, linea in enumerate(lineas, start=1):
                linea = linea.strip()
                if linea == "":
                    continue
                try:
                    datos = linea.split(",")
                    id_sudoku = datos[0]
                    dificultad = datos[1]
                    tablero_str = datos[2]
                    if len(tablero_str) != 81:
                        raise ValueError(f"el tablero debe tener 81 caracteres, tiene {len(tablero_str)}")
                    tablero = Tablero(id_sudoku, dificultad, tablero_str)
                    sudokus[tablero.id_sudoku] = tablero
                except (ValueError, IndexError) as error:
                    print(f"Linea {numero_linea} invalida en sudokus.lfp, se omite: {error}")
        return sudokus


    def cargar_jugadores(self, ruta_archivo):
        jugadores = {}
        with open(ruta_archivo, "r") as archivo:
            lineas = archivo.readlines()
            for numero_linea, linea in enumerate(lineas, start=1):
                linea = linea.strip()
                if linea == "":
                    continue
                try:
                    datos = linea.split(",")
                    carnet = datos[0]
                    nombre = datos[1]
                    apellido = datos[2]
                    nivel = datos[3]
                    jugador = Jugador(carnet, nombre, apellido, nivel)
                    jugadores[jugador.carnet] = jugador
                except (ValueError, IndexError) as error:
                    print(f"Linea {numero_linea} invalida en jugadores.lfp, se omite: {error}")
        return jugadores


    def cargar_intentos(self, ruta_archivo):
        intentos = []
        with open(ruta_archivo, "r") as archivo:
            lineas = archivo.readlines()
            for numero_linea, linea in enumerate(lineas, start=1):
                linea = linea.strip()
                if linea == "":
                    continue
                try:
                    datos = linea.split(",")
                    carnet = datos[0]
                    id_sudoku = datos[1]
                    solucion = datos[2]
                    tiempo_segundos = datos[3]
                    fecha = datos[4]
                    if len(solucion) != 81:
                        raise ValueError(f"la solucion debe tener 81 caracteres, tiene {len(solucion)}")
                    intento = Intento(carnet, id_sudoku, solucion, tiempo_segundos, fecha)
                    intentos.append(intento)
                except (ValueError, IndexError) as error:
                    print(f"Linea {numero_linea} invalida en intentos.lfp, se omite: {error}")
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