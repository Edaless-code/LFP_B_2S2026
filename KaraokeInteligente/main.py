"""Punto de entrada de Karaoke Inteligente.

Agrega src al path de importacion y lanza la interfaz grafica (Kivy) o la
version de consola.

Uso:
    python main.py              interfaz grafica (Windows y Android)
    python main.py --consola    version de texto (respaldo, mismas opciones)
"""

import os
import sys

DIRECTORIO_PROYECTO = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(DIRECTORIO_PROYECTO, "src"))

# Kivy interpreta los argumentos de la linea de comandos si no se desactiva.
os.environ.setdefault("KIVY_NO_ARGS", "1")


def ejecutar_consola() -> None:
    from consola.app_consola import AppConsola

    AppConsola().ejecutar()


def ejecutar_interfaz() -> None:
    try:
        import kivy  # noqa: F401
    except ImportError:
        print("Kivy no esta instalado; se abre la version de consola.")
        print("Para la interfaz grafica ejecute instalar.bat (o pip install -r requirements.txt).")
        ejecutar_consola()
        return
    from interfaz.app import KaraokeApp

    KaraokeApp().run()


def main() -> None:
    if "--consola" in sys.argv[1:]:
        ejecutar_consola()
    else:
        ejecutar_interfaz()


if __name__ == "__main__":
    main()
