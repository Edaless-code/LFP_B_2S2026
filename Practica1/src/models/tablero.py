class Tablero:
    def __init__(self, id_sudoku, dificultad, tablero_str):
        self.id_sudoku = int(id_sudoku)
        self.dificultad = dificultad
        self.tablero_str = tablero_str
        self.matriz = self._construir_matriz() 

    def _construir_matriz(self):
        matriz = []
        for i in range(9):
            fila = []
            for j in range(9):
                valor = int(self.tablero_str[i * 9 + j])
                fila.append(valor)
            matriz.append(fila)
        return matriz

if __name__ == "__main__":
    t = Tablero(1, "Facil", "003020600900305001001806400008102900700000008006708200002609500800203009005010800")
    for fila in t.matriz:
        print(fila)