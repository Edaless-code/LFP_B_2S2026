"""Deteccion de la plataforma (Windows, Linux o Android) y rutas dependientes de ella."""

from __future__ import annotations

import os
import sys


def es_android() -> bool:
    return "ANDROID_ARGUMENT" in os.environ or "ANDROID_PRIVATE" in os.environ or hasattr(sys, "getandroidapilevel")


def es_windows() -> bool:
    return os.name == "nt"


def nombre_plataforma() -> str:
    if es_android():
        return "Android"
    if es_windows():
        return "Windows"
    return sys.platform.capitalize()


def directorio_programa() -> str:
    """Carpeta donde esta main.py (y los recursos que acompanan al programa)."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def directorio_datos() -> str:
    """Carpeta donde se guardan CANCIONES.db, PROGRAMA.txt y config.json.

    En Windows es la misma carpeta del programa. En Android es el almacenamiento
    privado de la aplicacion, que se conserva al actualizar el APK.
    La variable de entorno KARAOKE_DATOS permite cambiarla (se usa en las pruebas).
    """
    personalizado = os.environ.get("KARAOKE_DATOS")
    if personalizado:
        return personalizado
    if es_android():
        privado = os.environ.get("ANDROID_PRIVATE")
        if privado:
            return os.path.join(privado, "karaoke")
    return directorio_programa()
