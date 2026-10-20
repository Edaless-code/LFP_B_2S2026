"""Punto de entrada de MarkdownCheck.

Agrega src al path de importacion y lanza la interfaz grafica.

Uso:
    python main.py
    python main.py examples/ejemplo_valido.md
"""

import os
import sys

DIRECTORIO_PROYECTO = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(DIRECTORIO_PROYECTO, "src"))


def main() -> None:
    """Crea la aplicacion, abre el archivo indicado (si lo hay) y muestra la ventana."""
    try:
        from PyQt6.QtWidgets import QApplication
    except ImportError:
        print("PyQt6 no esta instalado. Instalelo con:  pip install -r requirements.txt")
        sys.exit(1)

    from interfaz.tema import aplicar_tema
    from interfaz.ventana_principal import VentanaPrincipal

    aplicacion = QApplication(sys.argv)
    aplicacion.setApplicationName("MarkdownCheck")
    aplicar_tema(aplicacion)

    ventana = VentanaPrincipal()
    if len(sys.argv) > 1:
        ventana.abrir_ruta(sys.argv[1])
    ventana.show()
    sys.exit(aplicacion.exec())


if __name__ == "__main__":
    main()
