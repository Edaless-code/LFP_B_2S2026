"""Editor de texto con numeros de linea y resaltado de lineas con error."""

from PyQt6.QtCore import QRect, QSize, Qt
from PyQt6.QtGui import QColor, QFontDatabase, QPainter, QPaintEvent, QResizeEvent, QTextCursor, QTextFormat
from PyQt6.QtWidgets import QPlainTextEdit, QTextEdit, QWidget

from interfaz import tema

MARGEN_NUMEROS = 12
ESPACIOS_POR_TABULACION = 4


class _AreaNumeros(QWidget):
    """Franja lateral donde el editor dibuja los numeros de linea."""

    def __init__(self, editor: "EditorCodigo") -> None:
        super().__init__(editor)
        self._editor = editor

    def sizeHint(self) -> QSize:
        return QSize(self._editor.ancho_numeros(), 0)

    def paintEvent(self, evento: QPaintEvent) -> None:
        self._editor.pintar_numeros(evento)


class EditorCodigo(QPlainTextEdit):
    """QPlainTextEdit con numeros de linea, linea actual y lineas con error.

    Los numeros de linea permiten ubicar rapidamente las posiciones que
    reportan la tabla de tokens y la tabla de errores.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._area_numeros = _AreaNumeros(self)
        self._lineas_error: set[int] = set()

        fuente = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
        fuente.setPointSize(11)
        self.setFont(fuente)
        self.setTabStopDistance(self.fontMetrics().horizontalAdvance(" ") * ESPACIOS_POR_TABULACION)
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.document().setDocumentMargin(8)

        self.blockCountChanged.connect(self._actualizar_margen)
        self.updateRequest.connect(self._actualizar_area)
        self.cursorPositionChanged.connect(self._actualizar_resaltado)

        self._actualizar_margen()
        self._actualizar_resaltado()

    # ------------------------------------------------------------------
    # Numeros de linea
    # ------------------------------------------------------------------

    def ancho_numeros(self) -> int:
        """Ancho de la franja de numeros segun la cantidad de digitos."""
        digitos = max(3, len(str(max(1, self.blockCount()))))
        return MARGEN_NUMEROS * 2 + self.fontMetrics().horizontalAdvance("9") * digitos

    def _actualizar_margen(self) -> None:
        self.setViewportMargins(self.ancho_numeros(), 0, 0, 0)

    def _actualizar_area(self, rectangulo: QRect, desplazamiento_y: int) -> None:
        if desplazamiento_y:
            self._area_numeros.scroll(0, desplazamiento_y)
        else:
            self._area_numeros.update(0, rectangulo.y(), self._area_numeros.width(), rectangulo.height())
        if rectangulo.contains(self.viewport().rect()):
            self._actualizar_margen()

    def resizeEvent(self, evento: QResizeEvent) -> None:
        super().resizeEvent(evento)
        contenido = self.contentsRect()
        self._area_numeros.setGeometry(
            QRect(contenido.left(), contenido.top(), self.ancho_numeros(), contenido.height())
        )

    def pintar_numeros(self, evento: QPaintEvent) -> None:
        """Dibuja el numero de cada bloque visible; las lineas con error en rojo."""
        pintor = QPainter(self._area_numeros)
        pintor.fillRect(evento.rect(), QColor(tema.FONDO))

        bloque = self.firstVisibleBlock()
        numero = bloque.blockNumber()
        superior = round(self.blockBoundingGeometry(bloque).translated(self.contentOffset()).top())
        inferior = superior + round(self.blockBoundingRect(bloque).height())
        actual = self.textCursor().blockNumber()

        while bloque.isValid() and superior <= evento.rect().bottom():
            if bloque.isVisible() and inferior >= evento.rect().top():
                if numero + 1 in self._lineas_error:
                    pintor.setPen(QColor(tema.ERROR))
                elif numero == actual:
                    pintor.setPen(QColor(tema.TEXTO))
                else:
                    pintor.setPen(QColor("#9AA5B1"))
                pintor.drawText(
                    0,
                    superior,
                    self._area_numeros.width() - MARGEN_NUMEROS,
                    self.fontMetrics().height(),
                    Qt.AlignmentFlag.AlignRight,
                    str(numero + 1),
                )
            bloque = bloque.next()
            superior = inferior
            inferior = superior + round(self.blockBoundingRect(bloque).height())
            numero += 1
        pintor.end()

    # ------------------------------------------------------------------
    # Resaltado
    # ------------------------------------------------------------------

    def marcar_lineas_error(self, lineas: set[int]) -> None:
        """Resalta las lineas (numeradas desde 1) que contienen errores."""
        self._lineas_error = set(lineas)
        self._actualizar_resaltado()
        self._area_numeros.update()

    def _actualizar_resaltado(self) -> None:
        """Combina el fondo de la linea actual con el de las lineas con error."""
        selecciones = []
        for linea in sorted(self._lineas_error):
            bloque = self.document().findBlockByNumber(linea - 1)
            if not bloque.isValid():
                continue
            seleccion = QTextEdit.ExtraSelection()
            seleccion.format.setBackground(QColor(tema.ERROR_LINEA))
            seleccion.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
            seleccion.cursor = QTextCursor(bloque)
            selecciones.append(seleccion)

        # Con el editor vacio no se resalta la linea, para no tapar el texto de ayuda
        if not self.document().isEmpty() and self.textCursor().blockNumber() + 1 not in self._lineas_error:
            seleccion = QTextEdit.ExtraSelection()
            seleccion.format.setBackground(QColor(tema.LINEA_ACTUAL))
            seleccion.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
            seleccion.cursor = self.textCursor()
            seleccion.cursor.clearSelection()
            selecciones.append(seleccion)

        self.setExtraSelections(selecciones)

    # ------------------------------------------------------------------
    # Navegacion
    # ------------------------------------------------------------------

    def ir_a(self, linea: int, columna: int) -> None:
        """Mueve el cursor a una posicion (ambas numeradas desde 1) y la centra."""
        bloque = self.document().findBlockByNumber(max(0, linea - 1))
        if not bloque.isValid():
            bloque = self.document().lastBlock()
        cursor = QTextCursor(bloque)
        desplazamiento = min(max(0, columna - 1), max(0, bloque.length() - 1))
        cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.MoveAnchor, desplazamiento)
        self.setTextCursor(cursor)
        self.centerCursor()
        self.setFocus()

    def posicion_cursor(self) -> tuple[int, int]:
        """Linea y columna del cursor, numeradas desde 1."""
        cursor = self.textCursor()
        return cursor.blockNumber() + 1, cursor.positionInBlock() + 1
