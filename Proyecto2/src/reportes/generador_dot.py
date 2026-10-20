"""Generacion del archivo arbol.dot (Graphviz) a partir del arbol de derivacion."""

from modelos.nodo_ast import NodoAST

COLOR_RAIZ = "#2E75B6"
COLOR_NO_TERMINAL = "#D6EAF8"
COLOR_TERMINAL = "#F9E79F"
LARGO_MAXIMO_LEXEMA = 28


def escapar_dot(texto: str) -> str:
    """Escapa un texto para usarlo dentro de una etiqueta DOT entre comillas."""
    resultado: list[str] = []
    for caracter in texto:
        if caracter == "\\":
            resultado.append("\\\\")
        elif caracter == '"':
            resultado.append('\\"')
        elif caracter == "\n":
            resultado.append("\\\\n")  # se muestra como \n, no como salto real
        elif caracter == "\t":
            resultado.append(" ")
        else:
            resultado.append(caracter)
    return "".join(resultado)


def _etiqueta(nodo: NodoAST) -> str:
    """Etiqueta del nodo: el simbolo y, en las hojas con texto, el lexema."""
    if not nodo.es_terminal or nodo.lexema == "":
        return escapar_dot(nodo.simbolo)
    lexema = nodo.lexema
    if len(lexema) > LARGO_MAXIMO_LEXEMA:
        lexema = lexema[:LARGO_MAXIMO_LEXEMA] + "..."
    return f"{escapar_dot(nodo.simbolo)}\\n{escapar_dot(lexema)}"


def generar_dot(raiz: NodoAST) -> str:
    """Codigo DOT del arbol completo.

    La raiz <documento> se pinta de azul oscuro, los demas no terminales de
    azul claro y los terminales de amarillo (seccion 4.10 del enunciado).
    """
    nodos: list[str] = []
    aristas: list[str] = []
    contador = [0]

    def visitar(nodo: NodoAST) -> str:
        identificador = f"n{contador[0]}"
        contador[0] += 1

        if nodo is raiz:
            estilo = f'fillcolor="{COLOR_RAIZ}", fontcolor=white'
        elif nodo.es_terminal:
            estilo = f'fillcolor="{COLOR_TERMINAL}"'
        else:
            estilo = f'fillcolor="{COLOR_NO_TERMINAL}"'
        nodos.append(f'    {identificador} [label="{_etiqueta(nodo)}", {estilo}];')

        for hijo in nodo.hijos:
            aristas.append(f"    {identificador} -> {visitar(hijo)};")
        return identificador

    visitar(raiz)
    return (
        "digraph ArbolDerivacion {\n"
        "    rankdir=TB;\n"
        '    node [shape=box, style="rounded,filled", fontname="Arial", fontsize=10];\n'
        '    edge [color="#7B8794"];\n'
        "\n"
        + "\n".join(nodos)
        + "\n\n"
        + "\n".join(aristas)
        + "\n}\n"
    )
