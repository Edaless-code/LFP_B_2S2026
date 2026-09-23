"""Acumulacion de errores lexicos con recuperacion en modo panico."""

from modelos.error_lexico import ErrorLexico, TipoError


class GestorErrores:
    """Acumula los errores detectados durante el analisis lexico.

    El analizador no se detiene ante un error: lo registra en esta clase y
    continua leyendo el archivo hasta el final. Al terminar, esta clase
    entrega la lista completa para mostrarla en la interfaz grafica y en el
    reporte HTML de errores.
    """

    def __init__(self) -> None:
        self._errores: list[ErrorLexico] = []

    def registrar(
        self,
        tipo: TipoError,
        lexema: str,
        linea: int,
        columna: int,
    ) -> ErrorLexico:
        """Registra un error y le asigna su numero correlativo.

        Args:
            tipo: Categoria del error detectado.
            lexema: Fragmento de texto que lo provoco.
            linea: Linea donde inicia el lexema invalido.
            columna: Columna donde inicia el lexema invalido.

        Returns:
            El ErrorLexico creado, ya incorporado a la lista.
        """
        error = ErrorLexico(
            numero=len(self._errores) + 1,
            lexema=lexema,
            tipo=tipo,
            linea=linea,
            columna=columna,
        )
        self._errores.append(error)
        return error

    @property
    def errores(self) -> list[ErrorLexico]:
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