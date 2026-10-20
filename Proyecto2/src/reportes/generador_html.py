"""Reporte 1: traduccion del arbol de derivacion a HTML.

El HTML se genera recorriendo el arbol construido por el parser, nunca el
texto original: cada no terminal tiene un metodo que produce su fragmento a
partir de los fragmentos de sus hijos.

Si el documento tiene bloques de codigo, el reporte carga highlight.js desde
una CDN para colorear la sintaxis (alcance opcional). Es solo visual: el
contenido del bloque ya esta escapado y, sin conexion a internet, el codigo
se muestra igual pero sin colores.
"""

from modelos.nodo_ast import NodoAST
from modelos.tipo_token import TipoToken
from reportes.estilos import ARCHIVO_DOCUMENTO, atributo_html, pagina, texto_html

ANCLA_POR_DEFECTO = "seccion"
MARCAS_CASILLA_COMPLETA = ("x", "X")

VERSION_HIGHLIGHT = "11.9.0"
URL_HIGHLIGHT = f"https://cdnjs.cloudflare.com/ajax/libs/highlight.js/{VERSION_HIGHLIGHT}"
CABECERA_HIGHLIGHT = f'<link rel="stylesheet" href="{URL_HIGHLIGHT}/styles/atom-one-dark.min.css">\n'
SCRIPTS_HIGHLIGHT = (
    f'<script src="{URL_HIGHLIGHT}/highlight.min.js"></script>\n'
    "<script>if (window.hljs) { hljs.highlightAll(); }</script>\n"
)


class Encabezado:
    """Encabezado reconocido por el parser, con el ancla que lo identifica.

    Attributes:
        nivel: Nivel del encabezado, de 1 a 6.
        texto: Texto plano del encabezado, sin delimitadores.
        ancla: Identificador unico usado como id en el Reporte 1 y como
            destino de los enlaces del Reporte 3.
    """

    def __init__(self, nivel: int, texto: str, ancla: str) -> None:
        self.nivel = nivel
        self.texto = texto
        self.ancla = ancla


def texto_plano(nodo: NodoAST) -> str:
    """Concatena el texto de las hojas TEXTO y TEXTO_LITERAL del subarbol."""
    if nodo.es_terminal:
        if nodo.token.tipo in (TipoToken.TEXTO, TipoToken.TEXTO_LITERAL):
            return nodo.lexema
        return ""
    return "".join(texto_plano(hijo) for hijo in nodo.hijos)


def crear_ancla(texto: str, usadas: set[str]) -> str:
    """Convierte el texto de un encabezado en un identificador unico.

    Letras y digitos se conservan en minuscula; cualquier otro caracter se
    convierte en guion, sin guiones repetidos ni en los extremos. Si el
    identificador ya existe se le agrega un sufijo -2, -3, etc.
    """
    caracteres: list[str] = []
    for caracter in texto.lower():
        if caracter.isalnum():
            caracteres.append(caracter)
        elif caracteres and caracteres[-1] != "-":
            caracteres.append("-")
    while caracteres and caracteres[-1] == "-":
        caracteres.pop()

    base = "".join(caracteres) or ANCLA_POR_DEFECTO
    ancla = base
    sufijo = 2
    while ancla in usadas:
        ancla = f"{base}-{sufijo}"
        sufijo += 1
    usadas.add(ancla)
    return ancla


def extraer_encabezados(raiz: NodoAST) -> list[Encabezado]:
    """Encabezados del documento en orden de aparicion (recorrido en preorden)."""
    encabezados: list[Encabezado] = []
    usadas: set[str] = set()

    def recorrer(nodo: NodoAST) -> None:
        if nodo.simbolo == "<encabezado>":
            nivel = len(nodo.hijos[0].lexema)
            texto = texto_plano(nodo.hijos[1]).strip()
            encabezados.append(Encabezado(nivel, texto, crear_ancla(texto, usadas)))
        for hijo in nodo.hijos:
            recorrer(hijo)

    recorrer(raiz)
    return encabezados


class GeneradorHTML:
    """Recorre el arbol de derivacion y produce el HTML equivalente."""

    def __init__(self, raiz: NodoAST, prefijo_rutas: str = "") -> None:
        """
        Args:
            raiz: Raiz <documento> del arbol de derivacion.
            prefijo_rutas: Ruta desde la carpeta del reporte hasta la carpeta
                del archivo .md. Se antepone a las rutas relativas de enlaces e
                imagenes, que en Markdown son relativas al documento.
        """
        self._raiz = raiz
        self._prefijo_rutas = prefijo_rutas
        self.encabezados = extraer_encabezados(raiz)
        self._siguiente_encabezado = 0
        self._traducciones = {
            "<documento>": self._documento,
            "<bloque>": self._hijos,
            "<separador>": self._separador,
            "<encabezado>": self._encabezado,
            "<parrafo>": self._parrafo,
            "<lista>": self._lista,
            "<item_lista>": self._item_lista,
            "<sublista>": self._hijos,
            "<cita>": self._cita,
            "<linea_cita>": self._linea_cita,
            "<bloque_codigo>": self._bloque_codigo,
            "<regla_horizontal>": self._regla_horizontal,
            "<en_linea>": self._hijos,
            "<negrita>": self._negrita,
            "<cursiva>": self._cursiva,
            "<tachado>": self._tachado,
            "<codigo_inline>": self._codigo_inline,
            "<enlace>": self._enlace,
            "<imagen>": self._imagen,
        }

    def generar_cuerpo(self) -> str:
        """HTML del contenido del documento, sin la pagina que lo envuelve."""
        self._siguiente_encabezado = 0
        return self._traducir(self._raiz)

    def generar_reporte(self, nombre_archivo: str) -> str:
        """Reporte 1 completo: pagina HTML independiente con CSS embebido."""
        cuerpo = (
            '<div class="insignia">Análisis completado sin errores</div>\n'
            f'<article class="documento">\n{self.generar_cuerpo()}</article>'
        )
        if self._tiene_codigo(self._raiz):
            return pagina(
                f"{nombre_archivo} - Documento HTML",
                cuerpo,
                ARCHIVO_DOCUMENTO,
                cabecera_extra=CABECERA_HIGHLIGHT,
                scripts=SCRIPTS_HIGHLIGHT,
            )
        return pagina(f"{nombre_archivo} - Documento HTML", cuerpo, ARCHIVO_DOCUMENTO)

    def _tiene_codigo(self, nodo: NodoAST) -> bool:
        """Indica si el subarbol contiene algun <bloque_codigo>."""
        if nodo.simbolo == "<bloque_codigo>":
            return True
        return any(self._tiene_codigo(hijo) for hijo in nodo.hijos)

    # ------------------------------------------------------------------
    # Recorrido
    # ------------------------------------------------------------------

    def _traducir(self, nodo: NodoAST) -> str:
        """Traduce un nodo segun su simbolo; las hojas TEXTO se escapan."""
        if nodo.es_terminal:
            if nodo.token.tipo == TipoToken.TEXTO:
                return texto_html(nodo.lexema)
            return ""
        return self._traducciones[nodo.simbolo](nodo)

    def _hijos(self, nodo: NodoAST) -> str:
        return "".join(self._traducir(hijo) for hijo in nodo.hijos)

    @staticmethod
    def _hijo(nodo: NodoAST, simbolo: str) -> NodoAST | None:
        """Primer hijo con el simbolo indicado, o None."""
        for hijo in nodo.hijos:
            if hijo.simbolo == simbolo:
                return hijo
        return None

    # ------------------------------------------------------------------
    # Bloques
    # ------------------------------------------------------------------

    def _documento(self, nodo: NodoAST) -> str:
        return self._hijos(nodo)

    @staticmethod
    def _separador(_nodo: NodoAST) -> str:
        return ""

    def _encabezado(self, nodo: NodoAST) -> str:
        encabezado = self.encabezados[self._siguiente_encabezado]
        self._siguiente_encabezado += 1
        contenido = self._traducir(self._hijo(nodo, "<en_linea>"))
        etiqueta = f"h{encabezado.nivel}"
        return f'<{etiqueta} id="{atributo_html(encabezado.ancla)}">{contenido}</{etiqueta}>\n'

    def _parrafo(self, nodo: NodoAST) -> str:
        return f"<p>{self._hijos(nodo)}</p>\n"

    def _lista(self, nodo: NodoAST) -> str:
        """<ul> si los items usan vineta; <ol> si usan enumerador.

        Si una lista ordenada no empieza en 1 se conserva su numero inicial
        con el atributo start.
        """
        marcador = nodo.hijos[0].hijos[0].token
        if marcador.tipo != TipoToken.ENUMERADOR:
            return f"<ul>\n{self._hijos(nodo)}</ul>\n"
        inicio = int(marcador.lexema[:-1])
        atributo = f' start="{inicio}"' if inicio != 1 else ""
        return f"<ol{atributo}>\n{self._hijos(nodo)}</ol>\n"

    def _item_lista(self, nodo: NodoAST) -> str:
        contenido = self._traducir(self._hijo(nodo, "<en_linea>"))
        sublista = self._hijo(nodo, "<sublista>")
        anidada = f"\n{self._traducir(sublista)}" if sublista is not None else ""

        casilla = self._casilla(nodo)
        if casilla is None:
            return f"<li>{contenido}{anidada}</li>\n"
        marcada = " checked" if casilla.lexema[1] in MARCAS_CASILLA_COMPLETA else ""
        return f'<li class="tarea"><input type="checkbox" disabled{marcada}>{contenido}{anidada}</li>\n'

    @staticmethod
    def _casilla(nodo: NodoAST) -> NodoAST | None:
        """Hoja CASILLA de un <item_lista>, o None si no es una tarea."""
        for hijo in nodo.hijos:
            if hijo.es_terminal and hijo.token.tipo == TipoToken.CASILLA:
                return hijo
        return None

    def _cita(self, nodo: NodoAST) -> str:
        return f"<blockquote>\n{self._hijos(nodo)}</blockquote>\n"

    def _linea_cita(self, nodo: NodoAST) -> str:
        return f"<p>{self._traducir(self._hijo(nodo, '<en_linea>'))}</p>\n"

    def _bloque_codigo(self, nodo: NodoAST) -> str:
        lenguaje = ""
        contenido = ""
        for hijo in nodo.hijos:
            if hijo.es_terminal and hijo.token.tipo == TipoToken.LENGUAJE:
                lenguaje = hijo.lexema
            elif hijo.es_terminal and hijo.token.tipo == TipoToken.TEXTO_LITERAL:
                contenido = hijo.lexema
        clase = f' class="language-{atributo_html(lenguaje)}"' if lenguaje else ""
        return f"<pre><code{clase}>{texto_html(contenido)}</code></pre>\n"

    @staticmethod
    def _regla_horizontal(_nodo: NodoAST) -> str:
        return "<hr>\n"

    # ------------------------------------------------------------------
    # Contenido en linea
    # ------------------------------------------------------------------

    def _negrita(self, nodo: NodoAST) -> str:
        return f"<strong>{self._traducir(self._hijo(nodo, '<en_linea>'))}</strong>"

    def _cursiva(self, nodo: NodoAST) -> str:
        return f"<em>{self._traducir(self._hijo(nodo, '<en_linea>'))}</em>"

    def _tachado(self, nodo: NodoAST) -> str:
        return f"<del>{self._traducir(self._hijo(nodo, '<en_linea>'))}</del>"

    @staticmethod
    def _codigo_inline(nodo: NodoAST) -> str:
        return f"<code>{texto_html(texto_plano(nodo))}</code>"

    def _destino(self, nodo: NodoAST) -> str:
        """Destino de un enlace o imagen: el lexema de URL sin los parentesis.

        Las rutas relativas se ajustan con el prefijo para que sigan
        apuntando al mismo archivo desde la carpeta del reporte. Las
        direcciones con esquema (https:, mailto:), absolutas o anclas (#) no
        se modifican.
        """
        destino = ""
        for hijo in nodo.hijos:
            if hijo.es_terminal and hijo.token.tipo == TipoToken.URL:
                destino = hijo.lexema[1:-1]
        es_relativa = ":" not in destino and not destino.startswith(("/", "#"))
        if self._prefijo_rutas and es_relativa:
            return f"{self._prefijo_rutas}/{destino}"
        return destino

    def _enlace(self, nodo: NodoAST) -> str:
        texto = self._traducir(self._hijo(nodo, "<en_linea>"))
        return f'<a href="{atributo_html(self._destino(nodo))}">{texto}</a>'

    def _imagen(self, nodo: NodoAST) -> str:
        alternativo = texto_plano(nodo)
        return f'<img src="{atributo_html(self._destino(nodo))}" alt="{atributo_html(alternativo)}">'

