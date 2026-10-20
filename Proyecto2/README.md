# MarkdownCheck - Analizador Lexico-Sintactico de Markdown a HTML

**Autor:** Edgar Alessandro Chocon Oliva
**Carnet:** 202212978
**Curso:** Lenguajes Formales y de Programacion - Seccion B+
**Universidad de San Carlos de Guatemala - Facultad de Ingenieria**
**Segundo Semestre 2026**

---

## Descripcion

Aplicacion de escritorio que lee documentos escritos en un subconjunto de
Markdown (`.md`), los analiza y los traduce a HTML.

- El **analisis lexico** se realiza con un Automata Finito Determinista
  implementado manualmente en la clase `AnalizadorLexico`
  (metodo `siguiente_token()`).
- El **analisis sintactico** se realiza con un parser descendente recursivo
  implementado manualmente en la clase `AnalizadorSintactico`, con una funcion
  por cada simbolo no terminal de la gramatica.
- El parser construye un **arbol de derivacion** a partir del cual se generan
  los tres reportes HTML y el archivo `arbol.dot` de Graphviz.

**No se utiliza el modulo `re` para la tokenizacion, ni librerias de parsing
(ply, lark, antlr4) ni librerias de conversion de Markdown (markdown, mistune,
markdown2).**

## Subconjunto de Markdown soportado

| Elemento | Sintaxis | HTML generado |
|---|---|---|
| Encabezados | `#` a `######` | `<h1>` a `<h6>` |
| Parrafos | texto separado por una linea en blanco | `<p>` |
| Negrita | `**texto**` | `<strong>` |
| Cursiva | `*texto*` | `<em>` |
| Codigo en linea | `` `texto` `` | `<code>` |
| Listas no ordenadas | `-`, `*` o `+` (2 espacios por nivel) | `<ul><li>` anidados |
| Citas | `>`, `>>` o `> >` | `<blockquote>` anidados |
| Bloques de codigo | ```` ``` ```` ... ```` ``` ```` | `<pre><code>` |
| Regla horizontal | `---` | `<hr>` |

## Requisitos

- **Python 3.10 o superior**
- **PyQt6** (interfaz grafica)
- **Graphviz** (opcional), solo para convertir `arbol.dot` a imagen

Instalacion de dependencias:

```bash
cd Proyecto2
pip install -r requirements.txt
```

## Ejecucion

```bash
cd Proyecto2
python main.py
```

En Windows puede usarse `py main.py`. Tambien se puede abrir un archivo
directamente:

```bash
python main.py examples/ejemplo_valido.md
```

## Uso de la interfaz

1. **Abrir** (Ctrl+O) carga un archivo `.md`; tambien se puede arrastrar el
   archivo a la ventana o escribir directamente en el editor.
2. **Analizar** (F5) ejecuta el analisis lexico y sintactico.
3. El panel derecho muestra los resultados en tres pestanas:

   | Pestana | Contenido |
   |---|---|
   | Tokens | No., lexema, tipo, linea y columna de cada token |
   | Errores | No., lexema, tipo, fase, descripcion, linea y columna |
   | Arbol de derivacion | Arbol construido por el parser, con no terminales y terminales diferenciados |

4. Doble clic en un token, un error o una hoja del arbol ubica el cursor en esa
   posicion del documento. Las lineas con error se resaltan en el editor.

## Pruebas

Las pruebas unitarias usan `unittest`, de la biblioteca estandar:

```bash
cd Proyecto2
python -m unittest discover -s tests -v
```

## Estructura del proyecto

```
Proyecto2/
├── main.py                  Punto de entrada
├── requirements.txt         Dependencias
├── src/
│   ├── modelos/             TipoToken, Token, ErrorAnalisis, NodoAST
│   ├── analizador/          AnalizadorLexico, AnalizadorSintactico, GestorErrores
│   ├── servicios/           CargadorArchivos (lectura y validacion de .md)
│   ├── reportes/            GeneradorHTML, estadisticas, indice y arbol.dot
│   └── interfaz/            VentanaPrincipal, editor con numeros de linea y tema
├── tests/                   Pruebas unitarias
├── examples/                Archivos .md de entrada
├── docs/                    Manual tecnico, manual de usuario y casos de prueba
└── salidas/                 Reportes HTML y arbol.dot generados
```

## Documentacion

- [Manual tecnico](docs/MANUAL_TECNICO.md): arquitectura, tokens, AFD, gramatica
  libre de contexto y estrategia de recuperacion de errores.

## Estado del desarrollo

| Fase | Contenido | Estado |
|---|---|---|
| 1 | Estructura, modelos base, gramatica y AFD | Completada |
| 2 | Analizador lexico (AFD) y gestor de errores | Completada |
| 3 | Parser descendente recursivo e interfaz grafica | Completada |
| 4 | Reportes, pruebas y documentacion | Pendiente |
