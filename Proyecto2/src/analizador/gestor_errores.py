"""Acumulacion de errores lexicos y sintacticos."""

from modelos.error_analisis import ErrorAnalisis, TipoError


class GestorErrores:
    """Acumula los errores detectados durante el analisis.

    Ni el analizador lexico ni el sintactico se detienen ante un error: lo
    registran en esta clase y continuan hasta el final del archivo. Al
    terminar, esta clase entrega la lista completa para la interfaz grafica.

    Como el parser solicita los tokens a demanda, los errores de ambas fases
    se registran intercalados; ordenar_por_posicion() los deja en el orden en
    que aparecen en el documento.
    """

    def __init__(self) -> None:
        self._errores: list[ErrorAnalisis] = []

    def registrar(
        self,
        tipo: TipoError,
        lexema: str,
        linea: int,
        columna: int,
    ) -> ErrorAnalisis:
        """Registra un error y le asigna su numero correlativo.

        Args:
            tipo: Categoria del error detectado.
            lexema: Fragmento de texto que lo provoco.
            linea: Linea donde inicia el lexema invalido.
            columna: Columna donde inicia el lexema invalido.

        Returns:
            El ErrorAnalisis creado, ya incorporado a la lista.
        """
        error = ErrorAnalisis(
            numero=len(self._errores) + 1,
            lexema=lexema,
            tipo=tipo,
            linea=linea,
            columna=columna,
        )
        self._errores.append(error)
        return error

    def contiene(self, tipo: TipoError, linea: int) -> bool:
        """Indica si ya se registro un error de ese tipo en esa linea.

        El parser lo usa para no reportar dos veces la misma causa, por
        ejemplo un bloque de codigo sin cerrar que el lexico ya reporto.
        """
        for error in self._errores:
            if error.tipo == tipo and error.linea == linea:
                return True
        return False

    def ordenar_por_posicion(self) -> None:
        """Ordena los errores por linea y columna y los vuelve a numerar."""
        self._errores.sort(key=lambda error: (error.linea, error.columna))
        for indice, error in enumerate(self._errores, start=1):
            error.numero = indice

    @property
    def errores(self) -> list[ErrorAnalisis]:
        """Copia de la lista de errores acumulados."""
        return list(self._errores)

    @property
    def hay_errores(self) -> bool:
        """Indica si se registro al menos un error."""
        return len(self._errores) > 0

    @property
    def total(self) -> int:
        """Cantidad de errores acumulados."""
        return len(self._errores)

    def limpiar(self) -> None:
        """Vacia la lista de errores antes de un nuevo analisis."""
        self._errores.clear()
