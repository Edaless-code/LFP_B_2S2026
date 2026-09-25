# Casos de Prueba - HorarioScript

**Autor:** Edgar Alessandro Chocon Oliva
**Carnet:** 202212978
**Curso:** Lenguajes Formales y de Programacion - Seccion B+
**Fecha de ejecucion:** 25 de septiembre de 2026

---

## Entorno de ejecucion

| Elemento | Valor |
|---|---|
| Sistema operativo | Windows 11 |
| Version de Python | 3.12.4 |
| Interfaz grafica | Tkinter, biblioteca estandar |
| Dependencias externas | Ninguna |

Los resultados obtenidos provienen de la ejecucion real de las suites
`pruebas/pruebas_lexer.py`, `pruebas/prueba_horario.py` y
`pruebas/prueba_reportes.py`, y de la aplicacion grafica.

---

## Caso 1 - Archivo valido con las cuatro secciones

**Objetivo:** verificar el reconocimiento completo de un archivo correcto.

**Entrada:** `entradas/horario_valido.hor`, con 3 cursos, 3 catedraticos,
3 aulas y 6 clases.

**Resultado esperado**

- 0 errores lexicos
- 0 choques de horario
- Todas las entidades reconstruidas
- Los cuatro reportes HTML generados

**Resultado obtenido**

```
tokens = 289    errores = 0    choques = 0
cursos = 3   catedraticos = 3   aulas = 3   clases = 6
reportes generados = 4
```

**Estado: APROBADO**

---

## Caso 2 - Caracter no reconocido

**Objetivo:** detectar un caracter ajeno al alfabeto del lenguaje.

**Entrada:** linea 17 de `entradas/horario_errores.hor`

```
aula: "A-101" [capacidad: 40 @, edificio: "T-3"],
```

**Resultado esperado**

- Un error `CARACTER_NO_RECONOCIDO` en la linea 17, columna 34
- El analisis continua y reconoce los tokens posteriores

**Resultado obtenido**

```
[CARACTER_NO_RECONOCIDO]  '@'   linea 17, columna 34
Caracter no reconocido: '@' en linea 17, columna 34
```

Los tokens `,`, `edificio`, `:`, `"T-3"`, `]` posteriores se reconocieron
con normalidad.

**Estado: APROBADO**

---

## Caso 3 - Hora fuera de rango

**Objetivo:** validar tanto el formato `HH:MM` como el rango institucional
06:00 a 21:00.

**Entradas y resultados**

| Entrada | Motivo del rechazo | Donde falla | Obtenido |
|---|---|---|---|
| `7:00` | Un solo digito de hora | Dentro del AFD, estado q4 | `HORA_FUERA_DE_RANGO` linea 21, col 69 |
| `100:00` | Tres digitos de hora | Dentro del AFD, estado q6 | `HORA_FUERA_DE_RANGO` |
| `25:00` | Hora mayor que 21 | Validacion posterior al AFD | `HORA_FUERA_DE_RANGO` |
| `07:60` | Minutos mayores que 59 | Validacion posterior al AFD | `HORA_FUERA_DE_RANGO` |
| `05:59` | Un minuto antes del limite | Validacion posterior al AFD | `HORA_FUERA_DE_RANGO` linea 1, col 9 |
| `21:01` | Un minuto despues del limite | Validacion posterior al AFD | `HORA_FUERA_DE_RANGO` linea 1, col 9 |
| `06:00` | **Valida**, limite inferior | No falla | Token `HORA` |
| `21:00` | **Valida**, limite superior | No falla | Token `HORA` |

**Observacion relevante para la defensa:** los dos primeros casos mueren
*dentro* del automata por una transicion invalida; los siguientes lo recorren
completo hasta el estado de aceptacion q9 y fallan *despues*, en la validacion
semantica del rango. Ambos mecanismos reportan la misma categoria de error.

**Estado: APROBADO**

---

## Caso 4 - Dia no reconocido

**Objetivo:** detectar un valor invalido en el atributo `dia`.

**Entrada:** linea 21 de `entradas/horario_errores.hor`

```
clase: "LFP-0796" con "DOC-001" en "A-101" [dia: LUNEZ, inicio: 7:00, ...
```

**Resultado esperado:** un error `DIA_NO_RECONOCIDO` para el lexema `LUNEZ`.

**Resultado obtenido**

```
[DIA_NO_RECONOCIDO]  'LUNEZ'   linea 21, columna 54
Dia no reconocido: 'LUNEZ' en linea 21, columna 54
```

La categoria correcta se determina porque el analizador recuerda el ultimo
atributo emitido, que en este punto era `dia`. Sin ese contexto minimo, la
palabra solo podria reportarse como desconocida.

**Estado: APROBADO**

---

## Caso 5 - Codigo mal formado

**Objetivo:** rechazar una secuencia que no cumple el patron de codigo.

**Entrada:** linea 9 de `entradas/horario_errores.hor`

```
curso: "Curso Malo" [codigo: 9-0812, creditos: 5],
```

**Resultado esperado:** un solo error `CODIGO_MAL_FORMADO` con el lexema
completo `9-0812`, no tres errores fragmentados.

**Resultado obtenido**

```
[CODIGO_MAL_FORMADO]  '9-0812'   linea 9, columna 34
Codigo mal formado: '9-0812' en linea 9, columna 34
```

El patron exige que todo codigo comience con letra. Al detectar el guion tras
digitos, el analizador consume el resto de la secuencia para reportar un unico
error en lugar de fragmentarlo.

**Estado: APROBADO**

---

## Caso 6 - Numeral suelto y cadena sin cerrar

**Objetivo:** verificar los dos casos de delimitador incompleto.

### 6a - Numeral suelto

Un comentario de linea **no puede quedar sin cerrar**, porque termina en el
salto de linea o en el fin de archivo. El caso equivalente es el numeral que
no forma la secuencia `##`.

**Entrada:** `aula: # suelto`

**Resultado obtenido**

```
[CARACTER_NO_RECONOCIDO]   '#'        linea 1, columna 7
[PALABRA_NO_RECONOCIDA]    'suelto'   linea 1, columna 9
```

El segundo error confirma la recuperacion: tras el numeral invalido el
analisis continuo y evaluo la palabra siguiente.

### 6b - Cadena sin cerrar

**Entrada:** `seccion: "sin cerrar` seguido de un salto de linea

**Resultado esperado:** error reportado en la **posicion de apertura** de la
comilla, no en el final de la linea.

**Resultado obtenido**

```
[CADENA_SIN_CERRAR]        '"sin cerrar'   linea 1, columna 10
[PALABRA_NO_RECONOCIDA]    'siguiente'     linea 2, columna 1
```

La posicion reportada es la de la comilla que abrio la cadena.

**Estado: APROBADO**

---

## Caso 7 - Choques de horario simulados

**Objetivo:** detectar conflictos de catedratico y de aula.

**Entrada:** `entradas/horario_choques.hor`

```
clase: "LFP-0796" con "DOC-001" en "A-101" [dia: LUNES, inicio: 07:00, fin: 08:40, ...
clase: "BD2-0812" con "DOC-001" en "LAB-3" [dia: LUNES, inicio: 08:00, fin: 09:40, ...
clase: "SO1-0770" con "DOC-001" en "A-101" [dia: MARTES, inicio: 10:00, fin: 12:00, ...
clase: "BD2-0812" con "DOC-002" en "A-101" [dia: MARTES, inicio: 11:00, fin: 13:00, ...
```

**Resultado esperado**

- Un choque de catedratico: `DOC-001` el LUNES, aulas distintas
- Un choque de aula: `A-101` el MARTES, catedraticos distintos
- Ambos resaltados en rojo en el Reporte 1

**Resultado obtenido**

```
tokens = 238    errores = 0    choques = 2

CHOQUE 1  [CATEDRATICO]  'DOC-001'  LUNES
  LFP-0796 de 07:00 a 08:40 y BD2-0812 de 08:00 a 09:40
CHOQUE 2  [AULA]  'A-101'  MARTES
  SO1-0770 de 10:00 a 12:00 y BD2-0812 de 11:00 a 13:00
```

Las cuatro celdas correspondientes aparecen con fondo rojo y la marca
`CHOQUE DE HORARIO` en el Reporte 1.

**Estado: APROBADO**

---

## Caso 8 - Ausencia de falsos positivos en bloques adyacentes

**Objetivo:** verificar que los intervalos semiabiertos evitan falsos positivos.

**Entrada:** `entradas/casos_borde.hor`

```
clase: "LFP-0796" con "DOC-001" en "A-101" [dia: LUNES, inicio: 06:00, fin: 07:40, ...
clase: "LFP-0796" con "DOC-001" en "A-101" [dia: LUNES, inicio: 07:40, fin: 09:20, ...
```

Mismo catedratico, misma aula, mismo dia, y el fin de la primera coincide
exactamente con el inicio de la segunda.

**Resultado esperado:** **cero** choques. Un aula se libera en el instante en
que termina la clase.

**Resultado obtenido**

```
tokens = 135    errores = 0    choques = 0
```

**Estado: APROBADO**

---

## Caso 9 - Caracteres fuera del alfabeto protegidos por su contexto

**Objetivo:** verificar que el alfabeto restringido aplica solo al nivel
superior, y no dentro de cadenas ni de comentarios.

**Entrada:** `entradas/casos_borde.hor`

```
## Casos borde: horas limite, bloques adyacentes y caracteres raros protegidos
curso: "Simbolos @ % ~ dentro de cadena" [codigo: "LFP-0796", creditos: 4],
```

**Resultado esperado:** **cero** errores. Los simbolos `@`, `%` y `~` estan
dentro de un comentario y de una cadena, contextos donde se admite cualquier
caracter.

**Resultado obtenido**

```
errores = 0
```

Contrastado con el Caso 2, donde el mismo caracter `@` fuera de comillas si
produce error. Es la comprobacion de que `CARACTER_NO_RECONOCIDO` solo puede
originarse desde el estado inicial q0 del automata.

**Estado: APROBADO**

---

## Caso 10 - Archivo vacio y validacion de carga

**Objetivo:** verificar que el sistema no falla ante entradas degeneradas.

### 10a - Archivo vacio

**Entrada:** `entradas/vacio.hor`, sin contenido.

**Resultado obtenido**

```
tokens = 0    errores = 0    choques = 0
```

El analizador devuelve el marcador de fin de archivo en la primera llamada,
sin excepciones. Los reportes se generan con el mensaje de seccion vacia.

### 10b - Rutas invalidas

| Entrada | Resultado esperado | Resultado obtenido |
|---|---|---|
| Ruta inexistente | `ErrorDeCarga` con mensaje descriptivo | `El archivo no existe: ...` |
| Archivo con extension `.txt` | `ErrorDeCarga` | `El archivo debe tener extension .hor: ...` |
| `horario.HOR` en mayusculas | Aceptado | Aceptado |

**Estado: APROBADO**

---

## Caso 11 - Acumulacion de errores en una sola pasada

**Objetivo:** confirmar la recuperacion en modo panico sobre un archivo con
multiples errores de distinto tipo.

**Entrada:** `entradas/horario_errores.hor`

**Resultado esperado:** ocho errores que cubran las siete categorias, todos
reportados en una sola ejecucion, sin que el analisis se detenga.

**Resultado obtenido**

```
tokens = 147    errores = 8    categorias cubiertas = 7 de 7

1. [CODIGO_MAL_FORMADO]        '9-0812'        linea  9, columna 34
2. [CATEGORIA_NO_RECONOCIDA]   'TITULA'        linea 13, columna 66
3. [CARACTER_NO_RECONOCIDO]    '@'             linea 17, columna 34
4. [DIA_NO_RECONOCIDO]         'LUNEZ'         linea 21, columna 54
5. [HORA_FUERA_DE_RANGO]       '7:00'          linea 21, columna 69
6. [HORA_FUERA_DE_RANGO]       '25:00'         linea 21, columna 80
7. [PALABRA_NO_RECONOCIDA]     'salon'         linea 23, columna 89
8. [CADENA_SIN_CERRAR]         '"sin cerrar'   linea 25, columna 98
```

Pese a los ocho errores, el analizador reconocio 147 tokens y reconstruyo
2 cursos, 1 catedratico, 1 aula y 3 clases.

**Estado: APROBADO**

---

## Caso 12 - Generacion de los reportes HTML

**Objetivo:** verificar que los cuatro reportes se generan y son HTML valido.

**Resultado obtenido**

| Archivo de entrada | Reportes generados | HTML balanceado |
|---|---|---|
| `horario_valido.hor` | 4 | Si |
| `horario_choques.hor` | 4 | Si |
| `horario_errores.hor` | 4 | Si |

Verificado con un analizador de etiquetas HTML sobre los doce archivos
generados: todas las etiquetas abren y cierran correctamente.

**Estado: APROBADO**

---

## Resumen

| No. | Caso | Estado |
|---:|---|---|
| 1 | Archivo valido con las cuatro secciones | APROBADO |
| 2 | Caracter no reconocido | APROBADO |
| 3 | Hora fuera de rango, ocho variantes | APROBADO |
| 4 | Dia no reconocido | APROBADO |
| 5 | Codigo mal formado | APROBADO |
| 6 | Numeral suelto y cadena sin cerrar | APROBADO |
| 7 | Choques de horario simulados | APROBADO |
| 8 | Bloques adyacentes sin falso positivo | APROBADO |
| 9 | Caracteres protegidos por su contexto | APROBADO |
| 10 | Archivo vacio y validacion de carga | APROBADO |
| 11 | Acumulacion de errores en una pasada | APROBADO |
| 12 | Generacion de los reportes HTML | APROBADO |

**12 casos ejecutados, 12 aprobados.** El enunciado exige un minimo de 8.
