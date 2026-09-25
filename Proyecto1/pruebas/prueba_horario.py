"""Pruebas de la reconstruccion del horario y de la deteccion de choques."""

import os
import sys

sys.path.append(
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
)

from analizador.analizador_lexico import AnalizadorLexico
from analizador.gestor_errores import GestorErrores
from horario.constructor_horario import ConstructorHorario
from horario.detector_choques import TIPO_AULA, TIPO_CATEDRATICO, DetectorChoques, hay_traslape
from modelos.entidades import hora_a_minutos, minutos_a_hora

HORARIO_BASE = """
HORARIO {
  CURSOS {
    curso: "Lenguajes Formales" [codigo: "LFP-0796", creditos: 4],
    curso: "Bases de Datos 2" [codigo: "BD2-0812", creditos: 5],
  };
  CATEDRATICOS {
    catedratico: "Otto Rodriguez" [codigo: "DOC-001", categoria: TITULAR],
    catedratico: "Vivian Campos" [codigo: "DOC-002", categoria: INTERINO],
  };
  AULAS {
    aula: "A-101" [capacidad: 40, edificio: "T-3"],
    aula: "LAB-3" [capacidad: 25, edificio: "T-5"],
  };
  CLASES {
%s
  };
};
"""


def construir(clases_texto: str):
    """Analiza un horario y devuelve el horario construido y sus choques."""
    gestor = GestorErrores()
    tokens = AnalizadorLexico(HORARIO_BASE % clases_texto, gestor).analizar_todo()
    assert not gestor.hay_errores, gestor.errores
    horario = ConstructorHorario(tokens).construir()
    detector = DetectorChoques(horario)
    return horario, detector.detectar()


def probar_conversion_de_hora() -> None:
    """Verifica la normalizacion de HH:MM a minutos y de vuelta."""
    assert hora_a_minutos("00:00") == 0
    assert hora_a_minutos("07:00") == 420
    assert hora_a_minutos("08:40") == 520
    assert hora_a_minutos("21:00") == 1260
    assert hora_a_minutos("") == 0
    assert minutos_a_hora(420) == "07:00"
    assert minutos_a_hora(520) == "08:40"
    print("conversion de hora: OK")


def probar_traslape() -> None:
    """Verifica el predicado de traslape en sus casos limite."""
    assert hay_traslape(420, 520, 480, 560), "traslape parcial"
    assert hay_traslape(420, 520, 420, 520), "bloques identicos"
    assert hay_traslape(420, 620, 480, 520), "uno contenido en el otro"
    assert hay_traslape(480, 520, 420, 620), "el contenido es el primero"
    assert not hay_traslape(420, 520, 520, 620), "adyacentes: fin == inicio"
    assert not hay_traslape(520, 620, 420, 520), "adyacentes al reves"
    assert not hay_traslape(420, 520, 600, 700), "separados"
    print("traslape: OK")


def probar_construccion() -> None:
    """Verifica que las cuatro secciones se reconstruyan correctamente."""
    horario, _ = construir(
        '    clase: "LFP-0796" con "DOC-001" en "A-101" '
        '[dia: LUNES, inicio: 07:00, fin: 08:40, seccion: "N"],'
    )
    assert len(horario.cursos) == 2, horario.cursos
    assert horario.cursos["LFP-0796"].nombre == "Lenguajes Formales"
    assert horario.cursos["BD2-0812"].creditos == 5
    assert horario.catedraticos["DOC-001"].categoria == "TITULAR"
    assert horario.aulas["A-101"].capacidad == 40
    assert horario.aulas["A-101"].edificio == "T-3"
    assert len(horario.clases) == 1

    clase = horario.clases[0]
    assert clase.codigo_curso == "LFP-0796"
    assert clase.codigo_catedratico == "DOC-001"
    assert clase.codigo_aula == "A-101"
    assert clase.dia == "LUNES" and clase.seccion == "N"
    assert clase.duracion_minutos == 100
    print("construccion: OK")


def probar_sin_choques() -> None:
    """Un horario correcto no debe producir falsos positivos."""
    _, choques = construir(
        '    clase: "LFP-0796" con "DOC-001" en "A-101" [dia: LUNES, inicio: 07:00, fin: 08:40, seccion: "N"],\n'
        '    clase: "BD2-0812" con "DOC-001" en "A-101" [dia: LUNES, inicio: 08:40, fin: 10:20, seccion: "N"],\n'
        '    clase: "BD2-0812" con "DOC-002" en "LAB-3" [dia: MARTES, inicio: 07:00, fin: 08:40, seccion: "A"],'
    )
    assert len(choques) == 0, [c.descripcion for c in choques]
    print("sin choques: OK")


def probar_choque_de_catedratico() -> None:
    """Mismo catedratico, mismo dia, aulas distintas, horas traslapadas."""
    _, choques = construir(
        '    clase: "LFP-0796" con "DOC-001" en "A-101" [dia: LUNES, inicio: 07:00, fin: 08:40, seccion: "N"],\n'
        '    clase: "BD2-0812" con "DOC-001" en "LAB-3" [dia: LUNES, inicio: 08:00, fin: 09:00, seccion: "A"],'
    )
    assert len(choques) == 1, [c.descripcion for c in choques]
    assert choques[0].tipo == TIPO_CATEDRATICO
    assert choques[0].recurso == "DOC-001"
    print("choque de catedratico: OK")


def probar_choque_de_aula() -> None:
    """Misma aula, mismo dia, catedraticos distintos, horas traslapadas."""
    _, choques = construir(
        '    clase: "LFP-0796" con "DOC-001" en "A-101" [dia: MARTES, inicio: 10:00, fin: 12:00, seccion: "N"],\n'
        '    clase: "BD2-0812" con "DOC-002" en "A-101" [dia: MARTES, inicio: 11:00, fin: 13:00, seccion: "A"],'
    )
    assert len(choques) == 1, [c.descripcion for c in choques]
    assert choques[0].tipo == TIPO_AULA
    assert choques[0].recurso == "A-101"
    print("choque de aula: OK")


def probar_choque_doble() -> None:
    """Mismo catedratico y misma aula: son dos conflictos distintos."""
    _, choques = construir(
        '    clase: "LFP-0796" con "DOC-001" en "A-101" [dia: MIERCOLES, inicio: 07:00, fin: 08:40, seccion: "N"],\n'
        '    clase: "BD2-0812" con "DOC-001" en "A-101" [dia: MIERCOLES, inicio: 07:00, fin: 08:40, seccion: "A"],'
    )
    assert len(choques) == 2, [c.descripcion for c in choques]
    tipos = {c.tipo for c in choques}
    assert tipos == {TIPO_CATEDRATICO, TIPO_AULA}, tipos
    assert choques[0].numero == 1 and choques[1].numero == 2
    print("choque doble: OK")


def probar_dias_distintos() -> None:
    """Mismas horas y mismos recursos, pero en dias diferentes: no hay choque."""
    _, choques = construir(
        '    clase: "LFP-0796" con "DOC-001" en "A-101" [dia: LUNES, inicio: 07:00, fin: 08:40, seccion: "N"],\n'
        '    clase: "BD2-0812" con "DOC-001" en "A-101" [dia: JUEVES, inicio: 07:00, fin: 08:40, seccion: "N"],'
    )
    assert len(choques) == 0, [c.descripcion for c in choques]
    print("dias distintos: OK")


def main() -> None:
    """Ejecuta todas las pruebas del horario."""
    probar_conversion_de_hora()
    probar_traslape()
    probar_construccion()
    probar_sin_choques()
    probar_choque_de_catedratico()
    probar_choque_de_aula()
    probar_choque_doble()
    probar_dias_distintos()
    print("\nTodas las pruebas del horario pasaron.")


if __name__ == "__main__":
    main()
