"""Reporte 2: estadisticas del documento, calculadas sobre el arbol."""

from modelos.nodo_ast import NodoAST
from modelos.tipo_token import TipoToken
from reportes.estilos import ARCHIVO_ESTADISTICAS, pagina, texto_html

NIVELES_ENCABEZADO = 6


class Estadisticas:
    """Conteos de la estructura del documento.

    Attributes:
        palabras: Palabras de las hojas TEXTO; el codigo no se cuenta.
        parrafos: Nodos <parrafo>.
        encabezados_por_nivel: Cantidad de encabezados H1 a H6 (indice 0 = H1).
        listas: Listas de primer nivel (las sublistas no se cuentan aparte).
        items_lista: Nodos <item_lista> en todos los niveles.
        profundidad_listas: Maxima cantidad de <lista> anidadas.
        citas: Citas de primer nivel.
        lineas_cita: Nodos <linea_cita> en todos los niveles.
        profundidad_citas: Maxima cantidad de <cita> anidadas.
        bloques_codigo, negritas, cursivas, codigos_inline, reglas: Cantidad de
            nodos de cada tipo.
        tachados, enlaces, imagenes: Elementos en linea del alcance opcional.
        listas_ordenadas: Listas (de cualquier nivel) con enumerador.
        tareas, tareas_completadas: Items con casilla y con casilla marcada.
    """

    def __init__(self) -> None:
        self.palabras = 0
        self.parrafos = 0
        self.encabezados_por_nivel = [0] * NIVELES_ENCABEZADO
        self.listas = 0
        self.items_lista = 0
        self.profundidad_listas = 0
        self.citas = 0
        self.lineas_cita = 0
        self.profundidad_citas = 0
        self.bloques_codigo = 0
        self.negritas = 0
        self.cursivas = 0
        self.codigos_inline = 0
        self.reglas = 0
        self.tachados = 0
        self.enlaces = 0
        self.imagenes = 0
        self.listas_ordenadas = 0
        self.tareas = 0
        self.tareas_completadas = 0

    @property
    def encabezados(self) -> int:
        return sum(self.encabezados_por_nivel)


def contar_palabras(texto: str) -> int:
    """Cantidad de secuencias de caracteres separadas por espacios en blanco."""
    return len(texto.split())


def calcular_estadisticas(raiz: NodoAST) -> Estadisticas:
    """Recorre el arbol una vez y acumula todos los conteos."""
    estadisticas = Estadisticas()

    def recorrer(nodo: NodoAST, nivel_lista: int, nivel_cita: int) -> None:
        simbolo = nodo.simbolo

        if nodo.es_terminal:
            if nodo.token.tipo == TipoToken.TEXTO:
                estadisticas.palabras += contar_palabras(nodo.lexema)
            elif nodo.token.tipo == TipoToken.CASILLA:
                estadisticas.tareas += 1
                estadisticas.tareas_completadas += 1 if nodo.lexema[1] in ("x", "X") else 0
            return

        if simbolo == "<lista>":
            nivel_lista += 1
            estadisticas.listas += 1 if nivel_lista == 1 else 0
            if nodo.hijos[0].hijos[0].token.tipo == TipoToken.ENUMERADOR:
                estadisticas.listas_ordenadas += 1
            estadisticas.profundidad_listas = max(estadisticas.profundidad_listas, nivel_lista)
        elif simbolo == "<cita>":
            nivel_cita += 1
            estadisticas.citas += 1 if nivel_cita == 1 else 0
            estadisticas.profundidad_citas = max(estadisticas.profundidad_citas, nivel_cita)
        elif simbolo == "<encabezado>":
            estadisticas.encabezados_por_nivel[len(nodo.hijos[0].lexema) - 1] += 1
        elif simbolo == "<parrafo>":
            estadisticas.parrafos += 1
        elif simbolo == "<item_lista>":
            estadisticas.items_lista += 1
        elif simbolo == "<linea_cita>":
            estadisticas.lineas_cita += 1
        elif simbolo == "<bloque_codigo>":
            estadisticas.bloques_codigo += 1
        elif simbolo == "<negrita>":
            estadisticas.negritas += 1
        elif simbolo == "<cursiva>":
            estadisticas.cursivas += 1
        elif simbolo == "<codigo_inline>":
            estadisticas.codigos_inline += 1
        elif simbolo == "<regla_horizontal>":
            estadisticas.reglas += 1
        elif simbolo == "<tachado>":
            estadisticas.tachados += 1
        elif simbolo == "<enlace>":
            estadisticas.enlaces += 1
        elif simbolo == "<imagen>":
            estadisticas.imagenes += 1

        for hijo in nodo.hijos:
            recorrer(hijo, nivel_lista, nivel_cita)

    recorrer(raiz, 0, 0)
    return estadisticas


def _tarjeta(valor: int, etiqueta: str) -> str:
    return f'<div class="tarjeta"><div class="valor">{valor}</div><div class="etiqueta">{etiqueta}</div></div>'


def _par(etiqueta: str, valor: str, clase: str = "") -> str:
    atributo = f' class="{clase}"' if clase else ""
    return f'<div class="par"><span>{etiqueta}</span><strong{atributo}>{valor}</strong></div>'


def _niveles(cantidad: int) -> str:
    return f"{cantidad} {'nivel' if cantidad == 1 else 'niveles'}"


def generar_reporte_estadisticas(estadisticas: Estadisticas, nombre_archivo: str) -> str:
    """Reporte 2 completo: pagina HTML independiente con CSS embebido."""
    e = estadisticas
    tarjetas = "".join(
        [
            _tarjeta(e.palabras, "Palabras totales"),
            _tarjeta(e.parrafos, "Párrafos"),
            _tarjeta(e.encabezados, "Encabezados"),
            _tarjeta(e.listas, "Listas"),
            _tarjeta(e.items_lista, "Ítems de lista"),
            _tarjeta(e.citas, "Citas"),
            _tarjeta(e.lineas_cita, "Líneas de cita"),
            _tarjeta(e.bloques_codigo, "Bloques de código"),
            _tarjeta(e.reglas, "Reglas horizontales"),
        ]
    )

    maximo = max(e.encabezados_por_nivel) or 1
    filas = []
    for indice, cantidad in enumerate(e.encabezados_por_nivel):
        ancho = round(cantidad * 100 / maximo)
        filas.append(
            f'<tr><td class="nivel">H{indice + 1}</td>'
            f'<td><div class="pista"><div class="relleno" style="width: {ancho}%"></div></div></td>'
            f'<td class="cantidad">{cantidad}</td></tr>'
        )

    cuerpo = (
        '<h1 class="titulo-reporte">Estadísticas del Documento</h1>\n'
        f'<p class="subtitulo">{texto_html(nombre_archivo)}</p>\n'
        f'<div class="tarjetas">{tarjetas}</div>\n'
        '<h2 class="seccion">Encabezados por nivel</h2>\n'
        f'<table class="barras">{"".join(filas)}</table>\n'
        '<h2 class="seccion">Profundidad máxima de anidamiento</h2>\n'
        '<div class="pares">'
        f'{_par("Listas", _niveles(e.profundidad_listas), "listas")}'
        f'{_par("Citas", _niveles(e.profundidad_citas), "citas")}'
        "</div>\n"
        '<h2 class="seccion">Elementos en línea</h2>\n'
        '<div class="pares">'
        f'{_par("Negrita (**texto**)", str(e.negritas))}'
        f'{_par("Cursiva (*texto*)", str(e.cursivas))}'
        f'{_par("Código en línea (`texto`)", str(e.codigos_inline))}'
        f'{_par("Regla horizontal (---)", str(e.reglas))}'
        f'{_par("Tachado (~~texto~~)", str(e.tachados))}'
        f'{_par("Enlaces [texto](url)", str(e.enlaces))}'
        f'{_par("Imágenes ![alt](url)", str(e.imagenes))}'
        f'{_par("Listas ordenadas (1.)", str(e.listas_ordenadas))}'
        "</div>\n"
        '<h2 class="seccion">Listas de tareas</h2>\n'
        '<div class="pares">'
        f'{_par("Tareas", str(e.tareas))}'
        f'{_par("Tareas completadas", f"{e.tareas_completadas} de {e.tareas}")}'
        "</div>\n"
        '<p class="nota">Todos los valores se calculan recorriendo el árbol de derivación. '
        "Las palabras dentro de código no se cuentan.</p>"
    )
    return pagina(f"{nombre_archivo} - Estadísticas", cuerpo, ARCHIVO_ESTADISTICAS)
