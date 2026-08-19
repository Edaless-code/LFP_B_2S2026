class Jugador:
    def __init__(self, carnet, nombre, apellido, nivel):
        self.carnet = int(carnet)
        self.nombre = nombre
        self.apellido = apellido
        self.nivel = nivel
    
    def nombre_completo(self):
        return f"{self.nombre} {self.apellido}"

if __name__ == "__main__":
    j = Jugador(202011234, "Ana", "Oliva", "Intermedio")
    print(j.nombre_completo())
