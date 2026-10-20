"""Tema visual de la interfaz: paleta de colores y hoja de estilos (QSS).

Se fija una paleta clara para que la aplicacion se vea igual aunque el
sistema operativo este en modo oscuro.
"""

from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QApplication

# Colores base
FONDO = "#F4F6F9"
SUPERFICIE = "#FFFFFF"
BORDE = "#DDE2E8"
TEXTO = "#1F2933"
TEXTO_SECUNDARIO = "#616E7C"
ACENTO = "#2E75B6"
ACENTO_OSCURO = "#245C8F"
ACENTO_SUAVE = "#E3EEF8"

# Colores de estado
EXITO = "#1E7B43"
EXITO_FONDO = "#E3F4EA"
ERROR = "#B42318"
ERROR_FONDO = "#FDECEA"
ERROR_LINEA = "#FDE2DF"
ADVERTENCIA = "#8A5A00"
ADVERTENCIA_FONDO = "#FFF4D6"
LINEA_ACTUAL = "#F1F5FA"

# Colores del arbol de derivacion (los mismos del enunciado, seccion 4.10)
NO_TERMINAL = "#2E75B6"
TERMINAL = "#9A6B00"

HOJA_DE_ESTILOS = f"""
QMainWindow, QDialog {{
    background: {FONDO};
}}
QWidget {{
    color: {TEXTO};
    font-size: 10pt;
}}
QToolBar {{
    background: {SUPERFICIE};
    border: none;
    border-bottom: 1px solid {BORDE};
    padding: 6px 8px;
    spacing: 6px;
}}
QToolBar QToolButton {{
    background: transparent;
    border: 1px solid transparent;
    border-radius: 6px;
    padding: 6px 12px;
}}
QToolBar QToolButton:hover {{
    background: {ACENTO_SUAVE};
    border-color: {ACENTO_SUAVE};
}}
QToolBar QToolButton:disabled {{
    color: #A0A8B2;
}}
QToolBar QToolButton:checked {{
    background: {ACENTO_SUAVE};
    border-color: {ACENTO};
    color: {ACENTO_OSCURO};
}}
QToolButton#botonAnalizar {{
    background: {ACENTO};
    color: white;
    font-weight: bold;
    padding: 6px 18px;
}}
QToolButton#botonAnalizar:hover {{
    background: {ACENTO_OSCURO};
}}
QFrame#panel {{
    background: {SUPERFICIE};
    border: 1px solid {BORDE};
    border-radius: 8px;
}}
QLabel#tituloPanel {{
    font-size: 11pt;
    font-weight: bold;
}}
QLabel#detallePanel {{
    color: {TEXTO_SECUNDARIO};
}}
QLabel#bannerExito {{
    background: {EXITO_FONDO};
    color: {EXITO};
    border-radius: 6px;
    padding: 8px 12px;
    font-weight: bold;
}}
QLabel#bannerError {{
    background: {ERROR_FONDO};
    color: {ERROR};
    border-radius: 6px;
    padding: 8px 12px;
    font-weight: bold;
}}
QLabel#bannerAdvertencia {{
    background: {ADVERTENCIA_FONDO};
    color: {ADVERTENCIA};
    border-radius: 6px;
    padding: 8px 12px;
    font-weight: bold;
}}
QLabel#bannerNeutro {{
    background: {FONDO};
    color: {TEXTO_SECUNDARIO};
    border-radius: 6px;
    padding: 8px 12px;
}}
QPlainTextEdit {{
    background: {SUPERFICIE};
    border: none;
    selection-background-color: #BFD7EE;
    selection-color: {TEXTO};
}}
QTabWidget::pane {{
    border: none;
    border-top: 1px solid {BORDE};
}}
QTabBar::tab {{
    background: transparent;
    color: {TEXTO_SECUNDARIO};
    padding: 8px 14px;
    border-bottom: 2px solid transparent;
}}
QTabBar::tab:selected {{
    color: {ACENTO};
    border-bottom: 2px solid {ACENTO};
    font-weight: bold;
}}
QTabBar::tab:hover {{
    color: {TEXTO};
}}
QTableWidget, QTreeWidget {{
    background: {SUPERFICIE};
    alternate-background-color: #F8FAFC;
    border: none;
    gridline-color: {BORDE};
    selection-background-color: {ACENTO_SUAVE};
    selection-color: {TEXTO};
}}
QHeaderView::section {{
    background: {FONDO};
    color: {TEXTO_SECUNDARIO};
    border: none;
    border-bottom: 1px solid {BORDE};
    border-right: 1px solid {BORDE};
    padding: 6px 8px;
    font-weight: bold;
}}
QStatusBar {{
    background: {SUPERFICIE};
    border-top: 1px solid {BORDE};
    color: {TEXTO_SECUNDARIO};
}}
QSplitter::handle {{
    background: transparent;
}}
QMenuBar {{
    background: {SUPERFICIE};
}}
QMenuBar::item:selected, QMenu::item:selected {{
    background: {ACENTO_SUAVE};
    color: {TEXTO};
}}
QMenu {{
    background: {SUPERFICIE};
    border: 1px solid {BORDE};
}}
"""


def aplicar_tema(aplicacion: QApplication) -> None:
    """Aplica el estilo Fusion, una paleta clara y la hoja de estilos."""
    aplicacion.setStyle("Fusion")

    paleta = QPalette()
    paleta.setColor(QPalette.ColorRole.Window, QColor(FONDO))
    paleta.setColor(QPalette.ColorRole.WindowText, QColor(TEXTO))
    paleta.setColor(QPalette.ColorRole.Base, QColor(SUPERFICIE))
    paleta.setColor(QPalette.ColorRole.AlternateBase, QColor("#F8FAFC"))
    paleta.setColor(QPalette.ColorRole.Text, QColor(TEXTO))
    paleta.setColor(QPalette.ColorRole.Button, QColor(SUPERFICIE))
    paleta.setColor(QPalette.ColorRole.ButtonText, QColor(TEXTO))
    paleta.setColor(QPalette.ColorRole.Highlight, QColor(ACENTO))
    paleta.setColor(QPalette.ColorRole.HighlightedText, QColor("#FFFFFF"))
    paleta.setColor(QPalette.ColorRole.ToolTipBase, QColor(SUPERFICIE))
    paleta.setColor(QPalette.ColorRole.ToolTipText, QColor(TEXTO))
    paleta.setColor(QPalette.ColorRole.PlaceholderText, QColor(TEXTO_SECUNDARIO))
    aplicacion.setPalette(paleta)

    aplicacion.setStyleSheet(HOJA_DE_ESTILOS)
