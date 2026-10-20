"""Analizador sintactico de MarkdownCheck: parser descendente recursivo.

Implementa la gramatica de docs/MANUAL_TECNICO.md, seccion 4, con un metodo
por cada simbolo no terminal. Cada metodo construye y devuelve el NodoAST de
su produccion, de modo que el resultado del analisis es el arbol de
derivacion completo con raiz <documento>.

La gramatica es LL(1): el token actual basta para decidir que produccion
aplicar. La recursion que solo expresa repeticion se implementa con ciclos y
la que expresa anidamiento (sublistas, citas, negrita y cursiva) con llamadas
recursivas.
"""

from analizador.analizador_lexico import AnalizadorLexico
from analizador.gestor_errores import GestorErrores
from modelos.error_analisis import TipoError
from modelos.nodo_ast import NodoAST
from modelos.tipo_token import TipoToken
from modelos.token import Token

# PRIMERO(<parrafo>): tokens que inician contenido en linea
PRIMERO_EN_LINEA = frozenset(
    {
        TipoToken.TEXTO,
        TipoToken.NEGRITA,
        TipoToken.CURSIVA,
        TipoToken.TACHADO,
        TipoToken.CODIGO_INLINE,
        TipoToken.CORCHETE_ABRE,
        TipoToken.IMAGEN_ABRE,
    }
)

# Marcadores de item: VIÑETA (lista no ordenada) o ENUMERADOR (lista ordenada)
MARCADORES_LISTA = frozenset({TipoToken.VINETA, TipoToken.ENUMERADOR})

# PRIMERO(<bloque>): union disjunta de los PRIMERO de sus siete alternativas
PRIMERO_BLOQUE = PRIMERO_EN_LINEA | frozenset(
    {
        TipoToken.NUMERAL,
        TipoToken.VINETA,
        TipoToken.ENUMERADOR,
        TipoToken.CITA,
        TipoToken.CERCA_CODIGO,
        TipoToken.REGLA_HORIZONTAL,
        TipoToken.SALTO_PARRAFO,
    }
)

SIN_DELIMITADORES_ABIERTOS: frozenset = frozenset()
ESPACIOS_POR_NIVEL = 2
MAYOR_QUE = ">"


class AnalizadorSintactico:
    """Parser descendente recursivo que construye el arbol de derivacion.

    Solicita los tokens al analizador lexico de uno en uno, mediante
    siguiente_token(). Ante un error lo registra en el GestorErrores y
    continua, de modo que todos los errores se reportan en una sola pasada.
    """

    def __init__(self, lexico: AnalizadorLexico, gestor_errores: GestorErrores) -> None:
        """Inicializa el parser y lee el primer token (lookahead).

        Args:
            lexico: Analizador lexico que provee los tokens.
            gestor_errores: El mismo acumulador que usa el analizador lexico.
        """
        self._lexico = lexico
        self._gestor = gestor_errores
        self._actual: Token = lexico.siguiente_token()
        self._ultimo_token_con_error: Token | None = None
        self.raiz: NodoAST | None = None

    def analizar(self) -> NodoAST:
        """Analiza el documento completo.

        Returns:
            La raiz <documento> del arbol de derivacion. Los errores quedan
            en el GestorErrores, ordenados por posicion.
        """
        self.raiz = self.documento()
        self._gestor.ordenar_por_posicion()
        return self.raiz

    # ------------------------------------------------------------------
    # Primitivas
    # ------------------------------------------------------------------

    def _avanzar(self) -> Token:
        """Consume el token actual y lee el siguiente."""
        token = self._actual
        self._actual = self._lexico.siguiente_token()
        return token

    def _consumir(self, nodo: NodoAST) -> Token:
        """Consume el token actual y lo agrega como hoja del nodo."""
        token = self._avanzar()
        nodo.agregar_hijo(NodoAST.terminal(token))
        return token

    def _esperar(self, tipo: TipoToken, nodo: NodoAST) -> bool:
        """Consume el token si es del tipo esperado; si no, reporta el error.

        Cuando falta el token no se consume nada: el parser actua como si se
        hubiera insertado y continua (recuperacion a nivel de frase).

        Returns:
            True si el token esperado estaba presente.
        """
        if self._actual.tipo == tipo:
            self._consumir(nodo)
            return True
        self._reportar(TipoError.TOKEN_INESPERADO, self._actual)
        return False

    def _reportar(self, tipo: TipoError, token: Token, lexema: str | None = None, columna: int | None = None) -> None:
        """Registra un error sintactico, una sola vez por token."""
        if token is self._ultimo_token_con_error:
            return
        self._ultimo_token_con_error = token
        self._gestor.registrar(
            tipo,
            token.lexema_visible if lexema is None else lexema,
            token.linea,
            token.columna if columna is None else columna,
        )

    def _recuperar(self) -> None:
        """Modo panico para un token que no puede iniciar un bloque.

        Reporta el token y descarta tokens hasta un punto de sincronizacion:
        un SALTO_LINEA (que tambien se descarta), el inicio de un bloque o el
        fin del archivo.
        """
        self._reportar(TipoError.TOKEN_INESPERADO, self._actual)
        while self._actual.tipo != TipoToken.FIN_ARCHIVO:
            if self._actual.tipo == TipoToken.SALTO_LINEA:
                self._avanzar()
                return
            if self._actual.tipo in PRIMERO_BLOQUE:
                return
            self._avanzar()

    # ------------------------------------------------------------------
    # Estructura del documento
    # ------------------------------------------------------------------

    def documento(self) -> NodoAST:
        """<documento> ::= { <bloque> } FIN_ARCHIVO"""
        nodo = NodoAST.no_terminal("documento")
        while self._actual.tipo != TipoToken.FIN_ARCHIVO:
            if self._actual.tipo in PRIMERO_BLOQUE:
                nodo.agregar_hijo(self.bloque())
            else:
                self._recuperar()
        self._consumir(nodo)
        return nodo

    def bloque(self) -> NodoAST:
        """<bloque> ::= <encabezado> | <parrafo> | <lista> | <cita>(1)
                     | <bloque_codigo> | <regla_horizontal> | <separador>
        """
        nodo = NodoAST.no_terminal("bloque")
        tipo = self._actual.tipo

        if tipo == TipoToken.NUMERAL:
            nodo.agregar_hijo(self.encabezado())
        elif tipo in PRIMERO_EN_LINEA:
            nodo.agregar_hijo(self.parrafo())
        elif tipo in MARCADORES_LISTA:
            nodo.agregar_hijo(self.lista())
        elif tipo == TipoToken.CITA:
            nodo.agregar_hijo(self.cita(1))
        elif tipo == TipoToken.CERCA_CODIGO:
            nodo.agregar_hijo(self.bloque_codigo())
        elif tipo == TipoToken.REGLA_HORIZONTAL:
            nodo.agregar_hijo(self.regla_horizontal())
        else:
            nodo.agregar_hijo(self.separador())
        return nodo

    def separador(self) -> NodoAST:
        """<separador> ::= SALTO_PARRAFO"""
        nodo = NodoAST.no_terminal("separador")
        self._consumir(nodo)
        return nodo

    def encabezado(self) -> NodoAST:
        """<encabezado> ::= NUMERAL <en_linea>(∅) SALTO_LINEA"""
        nodo = NodoAST.no_terminal("encabezado")
        self._consumir(nodo)
        nodo.agregar_hijo(self.en_linea(SIN_DELIMITADORES_ABIERTOS))
        self._esperar(TipoToken.SALTO_LINEA, nodo)
        return nodo

    def parrafo(self) -> NodoAST:
        """<parrafo> ::= <en_linea>(∅) SALTO_LINEA"""
        nodo = NodoAST.no_terminal("parrafo")
        nodo.agregar_hijo(self.en_linea(SIN_DELIMITADORES_ABIERTOS))
        self._esperar(TipoToken.SALTO_LINEA, nodo)
        return nodo

    def regla_horizontal(self) -> NodoAST:
        """<regla_horizontal> ::= REGLA_HORIZONTAL SALTO_LINEA"""
        nodo = NodoAST.no_terminal("regla_horizontal")
        self._consumir(nodo)
        self._esperar(TipoToken.SALTO_LINEA, nodo)
        return nodo

    # ------------------------------------------------------------------
    # Listas
    # ------------------------------------------------------------------

    def lista(self) -> NodoAST:
        """<lista>(m) ::= <item_lista>(m) { <item_lista>(m) }

        El marcador m (VIÑETA u ENUMERADOR) lo fija el primer item: una lista
        no ordenada termina cuando aparece un ENUMERADOR en el mismo nivel, y
        viceversa. Todos los items deben tener la misma sangria que el
        primero; si no, se reporta INDENTACION_INVALIDA y el item se acepta
        en esta lista.
        """
        nodo = NodoAST.no_terminal("lista")
        marcador = self._actual.tipo
        sangria_lista = self._actual.sangria
        while self._actual.tipo == marcador:
            if self._actual.sangria != sangria_lista:
                self._reportar_indentacion(self._actual)
            nodo.agregar_hijo(self.item_lista())
        return nodo

    def item_lista(self) -> NodoAST:
        """<item_lista>(m) ::= m [ CASILLA ] <en_linea>(∅) SALTO_LINEA [ <sublista> ]"""
        nodo = NodoAST.no_terminal("item_lista")
        vineta = self._consumir(nodo)
        if self._actual.tipo == TipoToken.CASILLA:
            self._consumir(nodo)
        nodo.agregar_hijo(self.en_linea(SIN_DELIMITADORES_ABIERTOS))
        self._esperar(TipoToken.SALTO_LINEA, nodo)
        if self._actual.tipo == TipoToken.INDENT:
            nodo.agregar_hijo(self.sublista(vineta.sangria))
        return nodo

    def sublista(self, sangria_padre: int) -> NodoAST:
        """<sublista> ::= INDENT <lista> { <lista> } DEDENT

        Una sublista debe estar exactamente un nivel (2 espacios) a la
        derecha del item que la contiene. Puede contener varias listas
        seguidas si cambia el tipo de marcador (por ejemplo, items con
        vineta seguidos de items numerados).

        Args:
            sangria_padre: Sangria de la vineta del item contenedor.
        """
        nodo = NodoAST.no_terminal("sublista")
        self._consumir(nodo)

        if self._actual.tipo not in MARCADORES_LISTA:
            self._reportar(TipoError.TOKEN_INESPERADO, self._actual)
        while self._actual.tipo in MARCADORES_LISTA:
            if self._actual.sangria != sangria_padre + ESPACIOS_POR_NIVEL:
                self._reportar_indentacion(self._actual)
            nodo.agregar_hijo(self.lista())

        self._esperar(TipoToken.DEDENT, nodo)
        return nodo

    def _reportar_indentacion(self, vineta: Token) -> None:
        """Registra INDENTACION_INVALIDA en la posicion de la vineta."""
        self._reportar(TipoError.INDENTACION_INVALIDA, vineta)

    # ------------------------------------------------------------------
    # Citas
    # ------------------------------------------------------------------

    @staticmethod
    def nivel_cita(token: Token) -> int:
        """Nivel de una CITA: cantidad de '>' en su lexema (>> y > > valen 2)."""
        nivel = 0
        for caracter in token.lexema:
            if caracter == MAYOR_QUE:
                nivel += 1
        return nivel

    def cita(self, nivel: int) -> NodoAST:
        """<cita>(n) ::= <elemento_cita>(n) { <elemento_cita>(n) }

        <elemento_cita>(n) ::= <linea_cita>(n)   si nivel(CITA) = n
                             | <cita>(n+1)       si nivel(CITA) > n

        Una CITA de nivel menor que n termina esta cita y regresa el control
        a la cita contenedora.

        Args:
            nivel: Nivel de anidamiento n de esta cita (1 = cita externa).
        """
        nodo = NodoAST.no_terminal("cita")
        while self._actual.tipo == TipoToken.CITA:
            nivel_actual = self.nivel_cita(self._actual)
            if nivel_actual < nivel:
                break
            if nivel_actual == nivel:
                nodo.agregar_hijo(self.linea_cita())
            else:
                nodo.agregar_hijo(self.cita(nivel + 1))
        return nodo

    def linea_cita(self) -> NodoAST:
        """<linea_cita>(n) ::= CITA <en_linea>(∅) SALTO_LINEA

        Si el contenido empieza en la columna inmediata al ultimo '>', falta
        el espacio separador y se reporta CITA_MAL_FORMADA; la linea se acepta
        igualmente como cita.
        """
        nodo = NodoAST.no_terminal("linea_cita")
        marca = self._consumir(nodo)

        columna_siguiente = marca.columna + len(marca.lexema)
        sin_espacio = (
            self._actual.tipo != TipoToken.SALTO_LINEA
            and self._actual.linea == marca.linea
            and self._actual.columna == columna_siguiente
        )
        if sin_espacio:
            self._reportar(TipoError.CITA_MAL_FORMADA, marca, columna=columna_siguiente - 1)

        nodo.agregar_hijo(self.en_linea(SIN_DELIMITADORES_ABIERTOS))
        self._esperar(TipoToken.SALTO_LINEA, nodo)
        return nodo

    # ------------------------------------------------------------------
    # Bloques de codigo
    # ------------------------------------------------------------------

    def bloque_codigo(self) -> NodoAST:
        """<bloque_codigo> ::= CERCA_CODIGO [ LENGUAJE ] SALTO_LINEA
                               [ TEXTO_LITERAL ] CERCA_CODIGO SALTO_LINEA

        Si falta la cerca de cierre porque el archivo termino, el analizador
        lexico ya reporto BLOQUE_CODIGO_SIN_CERRAR y no se reporta de nuevo.
        """
        nodo = NodoAST.no_terminal("bloque_codigo")
        apertura = self._consumir(nodo)
        if self._actual.tipo == TipoToken.LENGUAJE:
            self._consumir(nodo)
        self._esperar(TipoToken.SALTO_LINEA, nodo)
        if self._actual.tipo == TipoToken.TEXTO_LITERAL:
            self._consumir(nodo)

        reportado_por_lexico = self._actual.tipo == TipoToken.FIN_ARCHIVO and self._gestor.contiene(
            TipoError.BLOQUE_CODIGO_SIN_CERRAR, apertura.linea
        )
        if not reportado_por_lexico and self._esperar(TipoToken.CERCA_CODIGO, nodo):
            self._esperar(TipoToken.SALTO_LINEA, nodo)
        return nodo

    # ------------------------------------------------------------------
    # Contenido en linea
    # ------------------------------------------------------------------

    def en_linea(self, abiertos: frozenset) -> NodoAST:
        """<en_linea>(A) ::= { <negrita>(A) | <cursiva>(A) | <tachado>(A) | <codigo_inline>
                             | <enlace> | <imagen> | TEXTO }

        Args:
            abiertos: Conjunto A de delimitadores abiertos por las producciones
                que contienen a esta. Un delimitador que esta en A solo puede
                ser el cierre de su construccion, por lo que termina la
                repeticion en lugar de abrir una nueva.
        """
        nodo = NodoAST.no_terminal("en_linea")
        while True:
            tipo = self._actual.tipo
            if tipo == TipoToken.TEXTO:
                self._consumir(nodo)
            elif tipo == TipoToken.CODIGO_INLINE:
                nodo.agregar_hijo(self.codigo_inline())
            elif tipo == TipoToken.NEGRITA and TipoToken.NEGRITA not in abiertos:
                nodo.agregar_hijo(self.negrita(abiertos))
            elif tipo == TipoToken.CURSIVA and TipoToken.CURSIVA not in abiertos:
                nodo.agregar_hijo(self.cursiva(abiertos))
            elif tipo == TipoToken.TACHADO and TipoToken.TACHADO not in abiertos:
                nodo.agregar_hijo(self.tachado(abiertos))
            elif tipo == TipoToken.CORCHETE_ABRE:
                nodo.agregar_hijo(self.enlace())
            elif tipo == TipoToken.IMAGEN_ABRE:
                nodo.agregar_hijo(self.imagen())
            else:
                return nodo

    def negrita(self, abiertos: frozenset) -> NodoAST:
        """<negrita>(A) ::= NEGRITA <en_linea>(A ∪ {NEGRITA}) NEGRITA"""
        nodo = NodoAST.no_terminal("negrita")
        self._consumir(nodo)
        nodo.agregar_hijo(self.en_linea(abiertos | {TipoToken.NEGRITA}))
        self._esperar(TipoToken.NEGRITA, nodo)
        return nodo

    def cursiva(self, abiertos: frozenset) -> NodoAST:
        """<cursiva>(A) ::= CURSIVA <en_linea>(A ∪ {CURSIVA}) CURSIVA"""
        nodo = NodoAST.no_terminal("cursiva")
        self._consumir(nodo)
        nodo.agregar_hijo(self.en_linea(abiertos | {TipoToken.CURSIVA}))
        self._esperar(TipoToken.CURSIVA, nodo)
        return nodo

    def tachado(self, abiertos: frozenset) -> NodoAST:
        """<tachado>(A) ::= TACHADO <en_linea>(A ∪ {TACHADO}) TACHADO"""
        nodo = NodoAST.no_terminal("tachado")
        self._consumir(nodo)
        nodo.agregar_hijo(self.en_linea(abiertos | {TipoToken.TACHADO}))
        self._esperar(TipoToken.TACHADO, nodo)
        return nodo

    def enlace(self) -> NodoAST:
        """<enlace> ::= CORCHETE_ABRE <en_linea>(∅) CORCHETE_CIERRA URL

        El texto del enlace es un contexto en linea independiente: el
        analizador lexico lo tokeniza con su propia pila de delimitadores, por
        lo que empieza sin delimitadores abiertos.
        """
        nodo = NodoAST.no_terminal("enlace")
        self._consumir(nodo)
        nodo.agregar_hijo(self.en_linea(SIN_DELIMITADORES_ABIERTOS))
        if self._esperar(TipoToken.CORCHETE_CIERRA, nodo):
            self._esperar(TipoToken.URL, nodo)
        return nodo

    def imagen(self) -> NodoAST:
        """<imagen> ::= IMAGEN_ABRE [ TEXTO ] CORCHETE_CIERRA URL"""
        nodo = NodoAST.no_terminal("imagen")
        self._consumir(nodo)
        if self._actual.tipo == TipoToken.TEXTO:
            self._consumir(nodo)
        if self._esperar(TipoToken.CORCHETE_CIERRA, nodo):
            self._esperar(TipoToken.URL, nodo)
        return nodo

    def codigo_inline(self) -> NodoAST:
        """<codigo_inline> ::= CODIGO_INLINE [ TEXTO_LITERAL ] CODIGO_INLINE"""
        nodo = NodoAST.no_terminal("codigo_inline")
        self._consumir(nodo)
        if self._actual.tipo == TipoToken.TEXTO_LITERAL:
            self._consumir(nodo)
        self._esperar(TipoToken.CODIGO_INLINE, nodo)
        return nodo
