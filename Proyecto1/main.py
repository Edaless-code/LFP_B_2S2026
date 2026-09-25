"""Punto de entrada de HorarioScript.

Agrega src al path de importacion y lanza la interfaz grafica.

Uso:
    python main.py
"""

import os
import sys

DIRECTORIO_PROYECTO = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(DIRECTORIO_PROYECTO, "src"))

from interfaz.aplicacion import AplicacionHorarioScript


def main() -> None:
    """Crea la ventana principal y entra en el bucle de eventos."""
    aplicacion = AplicacionHorarioScript()
    aplicacion.mainloop()


if __name__ == "__main__":
    main()
