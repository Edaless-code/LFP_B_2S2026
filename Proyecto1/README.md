# HorarioScript - Analizador Lexico para Horarios Academicos

**Autor:** Edgar Alessandro Chocon Oliva
**Carnet:** 202212978
**Curso:** Lenguajes Formales y de Programacion - Seccion B+
**Universidad de San Carlos de Guatemala - Facultad de Ingenieria**
**Segundo Semestre 2026**

---

## Descripcion

Analizador lexico de escritorio para **HorarioScript**, un lenguaje de dominio
especifico que describe horarios academicos en archivos con extension `.hor`.

El sistema lee el archivo, lo tokeniza mediante un **Automata Finito
Determinista implementado manualmente**, reporta los errores lexicos con su
posicion exacta, detecta choques de horario y genera cuatro reportes HTML.

El AFD esta escrito a mano, caracter por caracter. **No se utiliza el modulo
`re`, ni metodos de cadena de alto nivel (`split`, `find`, `strip`, `replace`),
ni generadores de analizadores lexicos como PLY o ANTLR.**

## Requisitos

- **Python 3.10 o superior** (desarrollado y probado en 3.12.4)
- **Tkinter**, incluido en la biblioteca estandar de Python
- Ninguna dependencia externa

Verificacion rapida:

```bash
python --version
python -c "import tkinter; print('Tkinter disponible')"
```

## Ejecucion

```bash
cd Proyecto1
python main.py
```

En Windows puede usarse `py main.py`.

## Uso paso a paso

1. **Abrir archivo .hor** abre el selector en la carpeta `entradas/`.
2. El contenido aparece en el panel izquierdo, que es **editable**: se puede
   modificar y volver a analizar sin recargar el archivo.
3. **Analizar** ejecuta el flujo completo. La barra de estado muestra el
   numero de tokens, de errores, de choques y el tiempo en milisegundos.
4. Las cuatro pestanas de la derecha muestran los resultados:

   | Pestana | Contenido |
   |---|---|
   | Tokens | No., lexema, tipo, linea y columna de cada token |
   | Errores lexicos | No., lexema, tipo, descripcion y posicion exacta |
   | Choques de horario | Recurso en conflicto, dia y bloques traslapados |
   | Resumen | Tiempo de analisis y frecuencia de tokens por tipo |

5. Los cuatro botones de **Reportes HTML** abren cada reporte en el navegador.
   Los archivos se guardan en `salidas/<nombre_del_archivo>/`.
6. **Exportar tokens a CSV** y **a JSON** guardan la tabla de tokens.

## Estructura del proyecto

```
Proyecto1/
├── main.py                       Punto de entrada: lanza la interfaz grafica
├── README.md
├── src/
│   ├── modelos/                  Estructuras de datos, sin logica
│   │   ├── tipo_token.py         Enumeracion de los 13 tipos de token
│   │   ├── token.py              Clase Token
│   │   ├── error_lexico.py       Clase ErrorLexico y sus 7 categorias
│   │   └── entidades.py          Curso, Catedratico, Aula, Clase, Choque
│   ├── analizador/               Motor lexico
│   │   ├── alfabeto.py           Clasificacion de caracteres, escrita a mano
│   │   ├── palabras_reservadas.py Tablas de busqueda del lenguaje
│   │   ├── gestor_errores.py     Clase GestorErrores, modo panico
│   │   └── analizador_lexico.py  Clase AnalizadorLexico y siguiente_token()
│   ├── horario/                  Dominio del horario
│   │   ├── constructor_horario.py Reconstruye entidades desde los tokens
│   │   └── detector_choques.py   Clase DetectorChoques
│   ├── reportes/                 Generacion de HTML
│   │   ├── estilos.py            CSS compartido y escapado
│   │   ├── reporte_horario.py    Reporte 1
│   │   ├── reporte_catedraticos.py Reporte 2
│   │   ├── reporte_estadistico.py  Reporte 3
│   │   ├── reporte_errores.py    Reporte de errores
│   │   └── generador_reportes.py Clase GeneradorReportes
│   ├── servicios/
│   │   └── cargador_archivos.py  Carga y validacion de archivos .hor
│   └── interfaz/
│       └── aplicacion.py         Clase AplicacionHorarioScript (Tkinter)
├── entradas/                     Archivos .hor de ejemplo
├── salidas/                      Reportes HTML generados
├── pruebas/                      Suites de verificacion
└── docs/                         Manuales, casos de prueba y diagrama del AFD
```

**Principio de organizacion:** el motor lexico (`analizador/`) no importa nada
de la interfaz ni de los reportes. Puede probarse por completo desde consola,
sin abrir la ventana.

## El lenguaje HorarioScript

Un archivo `.hor` tiene un bloque raiz `HORARIO` con cuatro secciones:

```
## Horario Lenguajes Formales - Segundo Semestre 2026
HORARIO {
  CURSOS {
    curso: "Lenguajes Formales y de Programacion" [codigo: "LFP-0796", creditos: 4],
  };
  CATEDRATICOS {
    catedratico: "Otto Rodriguez" [codigo: "DOC-001", categoria: TITULAR],
  };
  AULAS {
    aula: "A-101" [capacidad: 40, edificio: "T-3"],
  };
  CLASES {
    clase: "LFP-0796" con "DOC-001" en "A-101" [dia: LUNES, inicio: 07:00, fin: 08:40, seccion: "N"],
  };
};
```

### Tipos de token reconocidos

| Tipo | Regla | Ejemplo |
|---|---|---|
| `PALABRA_RESERVADA_BLOQUE` | `HORARIO CURSOS CATEDRATICOS AULAS CLASES` | `HORARIO` |
| `PALABRA_RESERVADA_ELEMENTO` | `curso catedratico aula clase` | `curso` |
| `PALABRA_RESERVADA_RELACION` | `con en` | `con` |
| `PALABRA_RESERVADA_ATRIBUTO` | `codigo creditos categoria capacidad edificio dia inicio fin seccion` | `creditos` |
| `CODIGO` | Letra, alfanumericos, guion, digitos | `LFP-0796` |
| `CADENA` | Texto entre comillas dobles | `"Otto Rodriguez"` |
| `HORA` | `HH:MM` entre 06:00 y 21:00 | `07:00` |
| `ENTERO` | Uno o mas digitos | `40` |
| `DIA` | `LUNES MARTES MIERCOLES JUEVES VIERNES SABADO` | `MARTES` |
| `CATEGORIA` | `TITULAR INTERINO AUXILIAR` | `TITULAR` |
| `SIMBOLO` | `{ } [ ] : , ;` | `{` |
| `COMENTARIO_LINEA` | Desde `##` hasta el fin de linea | `## Ciclo 2026` |
| `FIN_ARCHIVO` | Marcador interno de fin de entrada | |

### Categorias de error

| Categoria | Cuando ocurre |
|---|---|
| `CARACTER_NO_RECONOCIDO` | Caracter fuera del alfabeto, como `@` o `%` |
| `CADENA_SIN_CERRAR` | Se abrio `"` y llego el fin de linea o de archivo |
| `HORA_FUERA_DE_RANGO` | Formato distinto de `HH:MM` o fuera de 06:00-21:00 |
| `DIA_NO_RECONOCIDO` | Valor de `dia:` que no es uno de los seis validos |
| `CODIGO_MAL_FORMADO` | No cumple letra, alfanumericos, guion, digitos |
| `CATEGORIA_NO_RECONOCIDA` | Valor de `categoria:` invalido |
| `PALABRA_NO_RECONOCIDA` | Secuencia alfanumerica ajena al lenguaje |

El analisis **no se detiene ante un error**: los acumula todos en una sola
pasada y continua hasta el final del archivo (recuperacion en modo panico).

## Deteccion de choques de horario

Existe un choque cuando dos bloques cumplen las tres condiciones a la vez:

1. Mismo **dia**
2. Sus horarios se **traslapan**
3. Comparten **catedratico** o **aula**

Los intervalos se tratan como semiabiertos `[inicio, fin)`: una clase que
termina a las 08:40 **no** choca con otra que empieza a las 08:40.

Un mismo par de clases puede producir dos choques distintos si comparte a la
vez catedratico y aula, porque son dos problemas con soluciones diferentes.

## Reportes generados

| Reporte | Archivo | Contenido |
|---|---|---|
| 1. Horario semanal | `reporte_horario_semanal.html` | Rejilla de Lunes a Sabado por seccion. Celdas verdes confirmadas, rojas en choque |
| 2. Carga de catedraticos | `reporte_carga_catedraticos.html` | Horas semanales, cursos, secciones y nivel de carga |
| 3. Estadistico general | `reporte_estadistico.html` | Indicadores clave y ocupacion de aulas con barra de progreso |
| Errores lexicos | `reporte_errores.html` | Tabla completa de errores con posicion exacta |

Todos llevan el CSS incrustado y se abren en cualquier navegador sin recursos
externos.

## Archivos de ejemplo incluidos

| Archivo | Proposito |
|---|---|
| `horario_valido.hor` | Las cuatro secciones, sin errores ni choques |
| `horario_choques.hor` | Un choque de catedratico y uno de aula |
| `horario_errores.hor` | Ocho errores que cubren las siete categorias |
| `casos_borde.hor` | Horas limite 06:00 y 21:00, bloques adyacentes |
| `vacio.hor` | Archivo vacio |

## Pruebas

```bash
cd Proyecto1
python pruebas/prueba_base.py       # Estructuras base
python pruebas/pruebas_lexer.py     # AFD: tokens, horas, errores, comentarios
python pruebas/prueba_horario.py    # Traslape, construccion y choques
python pruebas/prueba_reportes.py   # Flujo completo y generacion de HTML
```

Las cuatro suites deben terminar con su mensaje de exito.

## Funcionalidades opcionales implementadas

- **Exportacion de la tabla de tokens a CSV y a JSON**
- **Estadisticas del analisis**: tiempo de ejecucion en milisegundos y
  frecuencia de tokens por tipo, en la pestana Resumen

## Documentacion

| Documento | Ruta |
|---|---|
| Manual Tecnico | `docs/MANUAL_TECNICO.md` |
| Manual de Usuario | `docs/MANUAL_USUARIO.md` |
| Casos de Prueba | `docs/CASOS_PRUEBA.md` |
| Diagrama del AFD | `docs/afd.dot` y `docs/imagenes/afd.png` |
