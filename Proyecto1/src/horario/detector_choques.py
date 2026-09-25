"""Deteccion de choques de horario entre bloques de clase.

Un choque ocurre cuando dos bloques comparten dia, se traslapan en el tiempo
y ademas comparten catedratico o aula. Ver manual tecnico, seccion 6.
"""

from modelos.entidades import Choque, Clase, Horario

TIPO_CATEDRATICO = "CATEDRATICO"
TIPO_AULA = "AULA"


def hay_traslape(inicio_a: int, fin_a: int, inicio_b: int, fin_b: int) -> bool:
    """Indica si dos bloques horarios se traslapan en el tiempo.

    Los intervalos se tratan como semiabiertos [inicio, fin): un bloque que
    termina a las 08:40 no choca con otro que empieza a las 08:40.

    Args:
        inicio_a: Minuto de inicio del primer bloque.
        fin_a: Minuto de fin del primer bloque.
        inicio_b: Minuto de inicio del segundo bloque.
        fin_b: Minuto de fin del segundo bloque.

    Returns:
        True si los bloques comparten al menos un minuto.
    """
    return not (fin_a <= inicio_b or fin_b <= inicio_a)


class DetectorChoques:
    """Compara todos los pares de clases y reporta los conflictos."""

    def __init__(self, horario: Horario) -> None:
        """Inicializa el detector.

        Args:
            horario: Horario ya construido a partir de los tokens.
        """
        self._horario = horario
        self._choques: list[Choque] = []

    def detectar(self) -> list[Choque]:
        """Recorre todos los pares de clases y acumula los choques.

        La comparacion es por pares, de orden cuadratico. Para un horario
        academico, con decenas de bloques, el costo es despreciable y el
        algoritmo se mantiene trivial de verificar a mano.

        Returns:
            Lista de choques detectados, numerados desde 1.
        """
        self._choques = []
        clases = self._horario.clases

        for indice_a in range(len(clases)):
            for indice_b in range(indice_a + 1, len(clases)):
                self._comparar(clases[indice_a], clases[indice_b])

        return list(self._choques)

    def _comparar(self, clase_a: Clase, clase_b: Clase) -> None:
        """Evalua un par de clases y registra los choques que correspondan."""
        if clase_a.dia == "" or clase_a.dia != clase_b.dia:
            return

        if not hay_traslape(clase_a.inicio_minutos, clase_a.fin_minutos,
                            clase_b.inicio_minutos, clase_b.fin_minutos):
            return

        # Un mismo par puede producir dos choques distintos: el catedratico
        # no puede estar en dos lugares, y el aula no puede alojar dos clases.
        if clase_a.codigo_catedratico != "" and \
                clase_a.codigo_catedratico == clase_b.codigo_catedratico:
            self._registrar(TIPO_CATEDRATICO, clase_a.codigo_catedratico,
                            clase_a, clase_b)

        if clase_a.codigo_aula != "" and clase_a.codigo_aula == clase_b.codigo_aula:
            self._registrar(TIPO_AULA, clase_a.codigo_aula, clase_a, clase_b)

    def _registrar(self, tipo: str, recurso: str,
                   clase_a: Clase, clase_b: Clase) -> None:
        """Agrega un choque con su numero correlativo."""
        self._choques.append(
            Choque(len(self._choques) + 1, tipo, recurso, clase_a, clase_b)
        )

    def clases_en_choque(self) -> set:
        """Devuelve el conjunto de clases involucradas en algun choque.

        El Reporte 1 usa este conjunto para pintar de rojo las celdas
        afectadas del horario semanal.

        Returns:
            Conjunto con los identificadores de objeto de las clases en conflicto.
        """
        involucradas = set()
        for choque in self._choques:
            involucradas.add(id(choque.clase_a))
            involucradas.add(id(choque.clase_b))
        return involucradas
