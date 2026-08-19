# Torneo de Sudoku - Numerix Academy (LFP Numerix)

Autor: Edgar Alessandro Chocon Oliva
Carnet: 202212978
Curso: Lenguajes Formales y de Programacion
Universidad de San Carlos de Guatemala - Facultad de Ingenieria

## Descripcion

Sistema de consola desarrollado en Python 3, aplicando Programacion Orientada a
Objetos, que valida tableros de Sudoku enviados por jugadores de un torneo,
califica su desempeno segun las reglas del juego, y genera reportes analiticos
en formato HTML sobre el comportamiento del torneo.

El sistema procesa tres archivos de entrada delimitados por comas
(`sudokus.lfp`, `jugadores.lfp`, `intentos.lfp`), reconstruye los tableros como
matrices de 9x9, valida filas, columnas y cajas de 3x3 segun las reglas del
Sudoku, calcula metricas de desempeno (tiempo promedio, porcentaje de validez,
tasa de exito) y genera tres reportes HTML.

## Requisitos

- Python 3.x (no requiere librerias externas, solo la biblioteca estandar)

## Estructura del proyecto

```
Practica1/
├── main.py                        # Punto de entrada del programa
├── src/
│   ├── models/
│   │   ├── tablero.py             # Clase Tablero
│   │   ├── jugador.py             # Clase Jugador
│   │   └── intento.py             # Clase Intento
│   ├── services/
│   │   ├── cargador_archivos.py   # Lectura de archivos .lfp
│   │   ├── validador_sudoku.py    # Validacion matricial del Sudoku
│   │   └── calculadora_metricas.py# Calculo de los 3 reportes
│   ├── ui/
│   │   └── menu.py                # Menu de consola
│   └── reports/
│       └── generador_html.py      # Generacion de reportes HTML
├── data/
│   ├── sudokus.lfp
│   ├── jugadores.lfp
│   └── intentos.lfp
├── reportes/                      # Reportes HTML generados (salida)
└── docs/
    ├── README.md
    ├── MANUAL_TECNICO.md
    ├── MANUAL_USUARIO.md
    ├── DIAGRAMA_FLUJO.md
    └── INFORME_DESARROLLO.md
```

## Como ejecutar

1. Clona o descarga este repositorio.
2. Verifica que los archivos `sudokus.lfp`, `jugadores.lfp` e `intentos.lfp`
   esten dentro de la carpeta `Practica1/data/`.
3. Desde una terminal, ubicate dentro de la carpeta `Practica1/`:

```bash
cd Practica1
python main.py
```

4. Se mostrara el menu principal:

```
==========================================
         TORNEO DE SUDOKU - NUMERIX
==========================================
1. Cargar archivo de sudokus
2. Cargar archivo de jugadores
3. Cargar archivo de intentos
4. Validar y calificar intentos
5. Generar Reporte: Resumen por Sudoku
6. Generar Reporte: Rendimiento por Jugador
7. Generar Reporte: Top 10 Mejores Tiempos
8. Salir

Seleccione una opcion:
```

## Ejemplo de uso

1. Selecciona `1`, `2` y `3` (en ese orden) para cargar los tres archivos de datos.
2. Selecciona `4` para validar y calificar todos los intentos cargados contra
   las reglas del Sudoku.
3. Selecciona `5`, `6` o `7` para generar cualquiera de los tres reportes. Los
   archivos HTML resultantes se guardan automaticamente en la carpeta
   `Practica1/reportes/` y pueden abrirse con cualquier navegador web.
4. Selecciona `8` para salir del programa.

## Formato de los archivos de entrada

**`sudokus.lfp`**: `id_sudoku,dificultad,tablero`
Donde `tablero` es una cadena de 81 digitos (0 = celda vacia), recorriendo el
tablero fila por fila.

**`jugadores.lfp`**: `carnet,nombre,apellido,nivel`

**`intentos.lfp`**: `carnet,id_sudoku,solucion,tiempo_segundos,fecha`
Donde `solucion` es una cadena de 81 digitos (1-9) con la propuesta de
solucion del jugador, y `fecha` tiene formato `DD-MM-AAAA`.

## Documentacion adicional

- [Manual Tecnico](docs/MANUAL_TECNICO.md)
- [Manual de Usuario](docs/MANUAL_USUARIO.md)
- [Diagrama de Flujo](docs/DIAGRAMA_FLUJO.md)
- [Informe de Desarrollo](docs/INFORME_DESARROLLO.md)
