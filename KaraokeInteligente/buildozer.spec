[app]

# Configuracion de compilacion del APK (Android) con Buildozer.
# Se compila en Linux (GitHub Actions o WSL); ver docs/MANUAL_TECNICO.md.

title = Karaoke Inteligente
package.name = karaokeinteligente
package.domain = gt.usac.edgaralessandro

source.dir = .
source.include_exts = py,png,txt,json
source.exclude_dirs = tests,docs,herramientas,android_extra,bin,.buildozer,.venv,venv,modelos,exportaciones,logs,__pycache__
source.exclude_patterns = requirements*.txt,*.db,*.bat,salidas/*

version = 1.0.0

# Solo modulos de la biblioteca estandar + Kivy + pyjnius.
# El reconocimiento de voz en Android usa el SpeechRecognizer nativo del telefono.
requirements = python3,kivy==2.3.1,pyjnius,android,sqlite3

icon.filename = %(source.dir)s/recursos/icono.png
presplash.filename = %(source.dir)s/recursos/presentacion.png
android.presplash_color = #12101C

orientation = landscape, portrait, landscape-reverse, portrait-reverse
fullscreen = 0

android.permissions = android.permission.RECORD_AUDIO, android.permission.INTERNET
android.api = 35
android.minapi = 24
android.accept_sdk_license = True
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True

# Declara la consulta al servicio de reconocimiento de voz (obligatorio desde Android 11).
android.extra_manifest_xml = ./android_extra/manifest_extra.xml

p4a.branch = master

[buildozer]
log_level = 2
warn_on_root = 0
