"""Entidades del horario academico reconstruidas a partir de los tokens.

Estas clases no contienen logica de analisis: son contenedores de datos que
el ConstructorHorario llena y que el DetectorChoques y los reportes consumen.
"""

CARACTERES_DE_HORA = 5


def hora_a_minutos(hora: str) -> int:
    """Convierte una hora con formato HH:MM en minutos desde medianoche.

    Normalizar la hora a un unico entero permite comparar y restar bloques
    horarios con aritmetica simple, sin manejar horas y minutos por separado.

    Args:
        hora: Texto con formato HH:MM, ya validado por el analizador lexico.

    Returns:
        Los minutos transcurridos desde las 00:00, o 0 si el texto no tiene
        la forma esperada.
    """
    if len(hora) != CARACTERES_DE_HORA:
        return 0
    return (int(hora[0]) * 600 + int(hora[1]) * 60
            + int(hora[3]) * 10 + int(hora[4]))


def minutos_a_hora(minutos: int) -> str:
    """Convierte minutos desde medianoche en un texto con formato HH:MM."""
    horas = minutos // 60
    resto = minutos % 60
    return f"{horas:02d}:{resto:02d}"


class Curso:
    """Curso declarado en la seccion CURSOS."""

    def __init__(self, nombre: str, codigo: str, creditos: int) -> None:
        self.nombre = nombre
        self.codigo = codigo
        self.creditos = creditos

    def __repr__(self) -> str:
        return f"Curso({self.codigo!r}, {self.nombre!r}, creditos={self.creditos})"


class Catedratico:
    """Catedratico declarado en la seccion CATEDRATICOS."""

    def __init__(self, nombre: str, codigo: str, categoria: str) -> None:
        self.nombre = nombre
        self.codigo = codigo
        self.categoria = categoria

    def __repr__(self) -> str:
        return f"Catedratico({self.codigo!r}, {self.nombre!r}, {self.categoria!r})"


class Aula:
    """Aula declarada en la seccion AULAS."""

    def __init__(self, codigo: str, capacidad: int, edificio: str) -> None:
        self.codigo = codigo
        self.capacidad = capacidad
        self.edificio = edificio

    def __repr__(self) -> str:
        return f"Aula({self.codigo!r}, capacidad={self.capacidad}, {self.edificio!r})"


class Clase:
    """Bloque de clase declarado en la seccion CLASES.

    Attributes:
        codigo_curso: Codigo del curso impartido.
        codigo_catedratico: Codigo del catedratico asignado.
        codigo_aula: Codigo del aula asignada.
        dia: Dia de la semana en mayusculas.
        inicio: Hora de inicio con formato HH:MM.
        fin: Hora de fin con formato HH:MM.
        seccion: Identificador de seccion.
        linea: Linea del archivo donde se declaro, para los reportes.
    """

    def __init__(self, codigo_curso: str, codigo_catedratico: str,
                 codigo_aula: str, dia: str, inicio: str, fin: str,
                 seccion: str, linea: int) -> None:
        self.codigo_curso = codigo_curso
        self.codigo_catedratico = codigo_catedratico
        self.codigo_aula = codigo_aula
        self.dia = dia
        self.inicio = inicio
        self.fin = fin
        self.seccion = seccion
        self.linea = linea

    @property
    def inicio_minutos(self) -> int:
        """Hora de inicio expresada en minutos desde medianoche."""
        return hora_a_minutos(self.inicio)

    @property
    def fin_minutos(self) -> int:
        """Hora de fin expresada en minutos desde medianoche."""
        return hora_a_minutos(self.fin)

    @property
    def duracion_minutos(self) -> int:
        """Duracion del bloque en minutos; cero si las horas son incoherentes."""
        duracion = self.fin_minutos - self.inicio_minutos
        return duracion if duracion > 0 else 0

    def __repr__(self) -> str:
        return (f"Clase({self.codigo_curso!r}, {self.codigo_catedratico!r}, "
                f"{self.codigo_aula!r}, {self.dia} {self.inicio}-{self.fin}, "
                f"seccion={self.seccion!r})")


class Choque:
    """Conflicto detectado entre dos bloques de clase.

    Attributes:
        numero: Correlativo del choque, comenzando en 1.
        tipo: 'CATEDRATICO' o 'AULA', segun el recurso compartido.
        recurso: Codigo del catedratico o del aula en conflicto.
        clase_a: Primer bloque involucrado.
        clase_b: Segundo bloque involucrado.
        descripcion: Mensaje legible del conflicto.
    """

    def __init__(self, numero: int, tipo: str, recurso: str,
                 clase_a: Clase, clase_b: Clase) -> None:
        self.numero = numero
        self.tipo = tipo
        self.recurso = recurso
        self.clase_a = clase_a
        self.clase_b = clase_b
        self.descripcion = (
            f"{tipo} '{recurso}' tiene dos clases traslapadas el {clase_a.dia}: "
            f"{clase_a.codigo_curso} de {clase_a.inicio} a {clase_a.fin} "
            f"y {clase_b.codigo_curso} de {clase_b.inicio} a {clase_b.fin}"
        )

    def a_fila(self):
        """Devuelve el choque como fila lista para la interfaz o un reporte."""
        return (self.numero, self.tipo, self.recurso, self.clase_a.dia,
                f"{self.clase_a.inicio}-{self.clase_a.fin}",
                f"{self.clase_b.inicio}-{self.clase_b.fin}",
                self.descripcion)

    def __repr__(self) -> str:
        return f"Choque({self.numero}, {self.tipo}, {self.recurso!r})"


class Horario:
    """Contenedor de todo lo declarado en un archivo .hor."""

    def __init__(self) -> None:
        self.cursos: dict[str, Curso] = {}
        self.catedraticos: dict[str, Catedratico] = {}
        self.aulas: dict[str, Aula] = {}
        self.clases: list[Clase] = []

    def __repr__(self) -> str:
        return (f"Horario(cursos={len(self.cursos)}, "
                f"catedraticos={len(self.catedraticos)}, "
                f"aulas={len(self.aulas)}, clases={len(self.clases)})")
