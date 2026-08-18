import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.tablero import Tablero
from models.intento import Intento


class ValidadorSudoku:
    
    def es_grupo_valido(self, grupo):
        """
        Verifica si un grupo (fila, columna o caja) es valido.
        Un grupo es valido si contiene los digitos del 1 al 9, cada uno exactamente una vez.
        """
        return set(grupo) == set(range(1, 10))


    def obtener_columna(self, matriz, indice_col):
        # debe devolver una lista con los 9 valores de esa columna
        return [fila[indice_col] for fila in matriz]

    
    def obtener_caja(self, matriz, caja_fila, caja_col):
        # debe devolver una lista PLANA de 9 valores (no una matriz 3x3)
        resultado = []
        inicio_fila = caja_fila * 3
        inicio_col = caja_col * 3
        for i in range(inicio_fila, inicio_fila + 3):
            for j in range(inicio_col, inicio_col + 3):
                resultado.append(matriz[i][j])
        return resultado

    def pistas_respetadas(self, matriz_original, matriz_solucion):
        for i in range(9):
            for j in range(9):
                valor_original = matriz_original[i][j]
                if valor_original != 0:
                        if matriz_solucion[i][j] != valor_original:
                            return False
        return True

    def calificar_intento(self, matriz_original, matriz_solucion):
        total_validas = 0

        # 9 filas: cada fila de matriz_solucion ya es una lista de 9 valores
        for fila in matriz_solucion:
            if self.es_grupo_valido(fila):
                total_validas += 1

        # 9 columnas
        for col in range(9):
            columna = self.obtener_columna(matriz_solucion, col)
            if self.es_grupo_valido(columna):
                total_validas += 1

        # 9 cajas de 3x3
        for caja_fila in range(3):
            for caja_col in range(3):
                caja = self.obtener_caja(matriz_solucion, caja_fila, caja_col)
                if self.es_grupo_valido(caja):
                    total_validas += 1

        porcentaje = (total_validas / 27) * 100
        pistas_ok = self.pistas_respetadas(matriz_original, matriz_solucion)
        resuelto_correctamente = (porcentaje == 100) and pistas_ok

        return porcentaje, pistas_ok, resuelto_correctamente


    def validar_y_calificar(self, tablero, intento):
        porcentaje, pistas_ok, resuelto = self.calificar_intento(tablero.matriz, intento.matriz)
        intento.porcentaje_validez = porcentaje
        intento.pistas_respetadas = pistas_ok
        intento.resuelto_correctamente = resuelto
   


if __name__ == "__main__":
    v = ValidadorSudoku()

    t = Tablero(1, "Facil", "400900600900300800200800400500100900700500100100700200300600500800200700600400300")
    i = Intento(202011234, 1, "483921657967345821251876493548132976729564138136798245372689514814253769695417382", 342, "15-03-2026")

    v.validar_y_calificar(t, i)

    print(i.porcentaje_validez)         # 100.0
    print(i.pistas_respetadas)          # True
    print(i.resuelto_correctamente)     # True