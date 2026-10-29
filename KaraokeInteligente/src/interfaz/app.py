"""Aplicacion Kivy (version provisional para validar la compilacion del APK)."""

from kivy.app import App
from kivy.uix.label import Label


class KaraokeApp(App):
    title = "Karaoke Inteligente"

    def build(self):
        return Label(text="Karaoke Inteligente\n(compilacion de prueba)", halign="center", font_size="28sp")
