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

En Windows puede usarse `py main.py`.

## Estructura del proyecto

```
Proyecto2/
├── main.py                  Punto de entrada
├── requirements.txt         Dependencias
├── src/
│   ├── modelos/             TipoToken, Token, ErrorAnalisis, NodoAST
│   ├── analizador/          AnalizadorLexico, AnalizadorSintactico, GestorErrores
│   ├── reportes/            GeneradorHTML, estadisticas, indice y arbol.dot
│   └── interfaz/            Ventana principal en PyQt6
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
| 2 | Analizador lexico (AFD) | Pendiente |
| 3 | Parser descendente recursivo e interfaz grafica | Pendiente |
| 4 | Reportes, pruebas y documentacion | Pendiente |
