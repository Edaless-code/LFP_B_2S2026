"""Genera el icono y la pantalla de presentacion del APK.

Herramienta de desarrollo (requiere Pillow). No forma parte del programa.

Uso:
    python herramientas/generar_iconos.py
"""

import os

from PIL import Image, ImageDraw, ImageFont

DIRECTORIO = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "recursos")
FONDO = (18, 16, 28)
ACENTO = (255, 196, 0)
SECUNDARIO = (156, 110, 255)


def dibujar_microfono(dibujo: ImageDraw.ImageDraw, cx: int, cy: int, escala: float) -> None:
    """Dibuja un microfono estilizado centrado en (cx, cy)."""
    ancho = int(120 * escala)
    alto = int(200 * escala)
    dibujo.rounded_rectangle(
        (cx - ancho // 2, cy - alto, cx + ancho // 2, cy), radius=ancho // 2, fill=ACENTO
    )
    for i in range(1, 4):
        y = cy - alto + int(i * alto / 4.5)
        dibujo.line((cx - ancho // 2 + 12, y, cx + ancho // 2 - 12, y), fill=FONDO, width=max(2, int(8 * escala)))
    grosor = max(3, int(16 * escala))
    dibujo.arc(
        (cx - ancho, cy - alto // 2 - int(40 * escala), cx + ancho, cy + int(60 * escala)),
        start=0, end=180, fill=SECUNDARIO, width=grosor,
    )
    dibujo.line((cx, cy + int(60 * escala), cx, cy + int(120 * escala)), fill=SECUNDARIO, width=grosor)
    dibujo.line(
        (cx - int(70 * escala), cy + int(120 * escala), cx + int(70 * escala), cy + int(120 * escala)),
        fill=SECUNDARIO, width=grosor,
    )


def generar_icono() -> None:
    imagen = Image.new("RGB", (512, 512), FONDO)
    dibujo = ImageDraw.Draw(imagen)
    dibujo.rounded_rectangle((16, 16, 496, 496), radius=96, outline=SECUNDARIO, width=10)
    dibujar_microfono(dibujo, 256, 300, 1.0)
    imagen.save(os.path.join(DIRECTORIO, "icono.png"))


def generar_presentacion() -> None:
    imagen = Image.new("RGB", (1024, 1024), FONDO)
    dibujo = ImageDraw.Draw(imagen)
    dibujar_microfono(dibujo, 512, 520, 1.3)
    try:
        fuente = ImageFont.truetype("DejaVuSans-Bold.ttf", 72)
    except OSError:
        fuente = ImageFont.load_default()
    texto = "Karaoke Inteligente"
    caja = dibujo.textbbox((0, 0), texto, font=fuente)
    dibujo.text(((1024 - (caja[2] - caja[0])) // 2, 760), texto, fill=ACENTO, font=fuente)
    imagen.save(os.path.join(DIRECTORIO, "presentacion.png"))


if __name__ == "__main__":
    os.makedirs(DIRECTORIO, exist_ok=True)
    generar_icono()
    generar_presentacion()
    print("Imagenes generadas en", DIRECTORIO)
