class Intento:
    def __init__(self, carnet, id_sudoku, solucion_str, tiempo_segundos, fecha):
        self.carnet = int(carnet)
        self.id_sudoku = int(id_sudoku)
        self.solucion_str = solucion_str
        self.tiempo_segundos = int(tiempo_segundos)
        self.fecha = fecha
        self.matriz = self._construir_matriz()
        self.porcentaje_validez = None
        self.pistas_respetadas = None
        self.resuelto_correctamente = None

    def _construir_matriz(self):
        matriz = []
        for i in range(9):
            fila = []
            for j in range(9):
                valor = int(self.solucion_str[i * 9 + j])
                fila.append(valor)
            matriz.append(fila)
        return matriz

if __name__ == "__main__":
    i = Intento(202011234, 1, "483921657967345821251876493548132976729564138136798245372689514814253769695417382"[:81], 342, "15-03-2026")
    print(i.matriz[0])
    print(i.porcentaje_validez)
