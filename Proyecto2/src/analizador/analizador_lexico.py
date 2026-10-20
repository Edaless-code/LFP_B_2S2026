"""Analizador lexico de MarkdownCheck implementado como AFD manual.

Recorre el texto caracter a caracter siguiendo los estados documentados en
docs/MANUAL_TECNICO.md, seccion 3. No utiliza el modulo re.

El AFD se divide en cuatro contextos:
    inicio de linea        estados S0, S1, H1-H7, C1-C2, A1-A2, F1, LG, G1-G4, AS, MS
    contenido en linea     estados E0, T, I1, N2, K1, SL
    literal en linea       estados LI, K2
    literal de bloque      estados B0-B4

Los tokens se producen por bloques (una linea de encabezado, de item o de
cita, un parrafo completo o un bloque de codigo) y se entregan uno a uno con
siguiente_token(). Tokenizar el bloque completo antes de entregarlo permite
detectar los delimitadores sin cerrar y reportarlos en su posicion de apertura.
"""

from collections import deque

from analizador.gestor_errores import GestorErrores
from modelos.error_analisis import TipoError
from modelos.tipo_token import TipoToken
from modelos.token import Token

ESPACIO = " "
TABULACION = "\t"
SALTO = "\n"
RETORNO = "\r"
MARCA_BOM = "﻿"
NUMERAL = "#"
MAYOR_QUE = ">"
GUION = "-"
ASTERISCO = "*"
MAS = "+"
ACENTO_GRAVE = "`"

MAXIMO_NIVEL_ENCABEZADO = 6
MINIMO_GUIONES_REGLA = 3
LONGITUD_CERCA = 3
ANCHO_TABULACION = 2  # una tabulacion equivale a un nivel de lista

# Clases de linea que reconoce el contexto de inicio de linea
LINEA_VACIA = "vacia"
LINEA_ENCABEZADO = "encabezado"
LINEA_ENCABEZADO_INVALIDO = "encabezado_invalido"
LINEA_CITA = "cita"
LINEA_CODIGO = "codigo"
LINEA_REGLA = "regla"
LINEA_VINETA = "vineta"
LINEA_PARRAFO = "parrafo"


def es_espacio(caracter: str) -> bool:
    """Clase 'esp' del alfabeto: espacio o tabulacion."""
    return caracter == ESPACIO or caracter == TABULACION


class InicioLinea:
    """Resultado de recorrer el contexto de inicio de linea.

    Attributes:
        clase: Tipo de bloque que inicia la linea (constantes LINEA_*).
        indice: Indice del primer caracter que no es indentacion.
        sangria: Ancho de la indentacion (tabulacion = 2 espacios).
        fin_marcador: Indice del primer caracter despues del marcador de
            bloque (despues de los #, de la vineta o de los guiones).
    """

    def __init__(self, clase: str, indice: int, sangria: int, fin_marcador: int) -> None:
        self.clase = clase
        self.indice = indice
        self.sangria = sangria
        self.fin_marcador = fin_marcador


class AnalizadorLexico:
    """AFD manual que convierte el texto de un archivo .md en tokens.

    El analisis no se detiene ante un error: lo registra en el GestorErrores
    y continua hasta el final del archivo.
    """

    def __init__(self, texto: str, gestor_errores: GestorErrores) -> None:
        """Inicializa el analizador.

        Args:
            texto: Contenido completo del archivo .md.
            gestor_errores: Acumulador donde se registran los errores.
        """
        self._gestor = gestor_errores
        self._lineas = self._dividir_lineas(self._normalizar(texto))
        self._indice_linea = 0
        self._pendientes: deque[Token] = deque()
        self._emitidos: list[Token] = []
        self._pila_sangrias: list[int] = []
        self._numero_token = 0
        self._fin_generado = False

    # ------------------------------------------------------------------
    # Interfaz publica
    # ------------------------------------------------------------------

    def siguiente_token(self) -> Token:
        """Devuelve el siguiente token de la entrada.

        Cuando la cola de tokens pendientes esta vacia se tokeniza el
        siguiente bloque. Al agotarse la entrada devuelve FIN_ARCHIVO, y lo
        sigue devolviendo en las llamadas posteriores.
        """
        while not self._pendientes:
            if self._fin_generado:
                return self._emitidos[-1]
            self._procesar_bloque()

        token = self._pendientes.popleft()
        self._emitidos.append(token)
        return token

    def analizar_todo(self) -> list[Token]:
        """Consume la entrada completa y devuelve todos los tokens.

        Se construye sobre siguiente_token(), de modo que ambas formas de uso
        producen exactamente la misma secuencia.
        """
        while self.siguiente_token().tipo != TipoToken.FIN_ARCHIVO:
            pass
        return list(self._emitidos)

    @property
    def tokens(self) -> list[Token]:
        """Tokens entregados hasta el momento, en orden."""
        return list(self._emitidos)

    # ------------------------------------------------------------------
    # Preparacion del texto
    # ------------------------------------------------------------------

    @staticmethod
    def _normalizar(texto: str) -> str:
        """Unifica los finales de linea y garantiza un salto de linea final.

        Convierte \\r\\n y \\r en \\n, elimina la marca BOM que agregan algunos
        editores de Windows y agrega un \\n al final si falta, para que toda
        linea no vacia termine en un salto de linea.
        """
        caracteres: list[str] = []
        indice = 0
        while indice < len(texto):
            caracter = texto[indice]
            if caracter == RETORNO:
                caracteres.append(SALTO)
                if indice + 1 < len(texto) and texto[indice + 1] == SALTO:
                    indice += 1
            elif not (indice == 0 and caracter == MARCA_BOM):
                caracteres.append(caracter)
            indice += 1

        if caracteres and caracteres[-1] != SALTO:
            caracteres.append(SALTO)
        return "".join(caracteres)

    @staticmethod
    def _dividir_lineas(texto: str) -> list[str]:
        """Separa el texto normalizado en lineas, sin el caracter \\n."""
        lineas: list[str] = []
        actual: list[str] = []
        for caracter in texto:
            if caracter == SALTO:
                lineas.append("".join(actual))
                actual = []
            else:
                actual.append(caracter)
        return lineas

    # ------------------------------------------------------------------
    # Construccion de tokens
    # ------------------------------------------------------------------

    def _agregar(
        self,
        tipo: TipoToken,
        lexema: str,
        linea: int,
        columna: int,
        sangria: int = 0,
    ) -> Token:
        """Crea un token con el siguiente numero correlativo y lo encola."""
        self._numero_token += 1
        token = Token(self._numero_token, lexema, tipo, linea, columna, sangria)
        self._pendientes.append(token)
        return token

    def _agregar_salto_linea(self, numero_linea: int) -> None:
        """Emite el SALTO_LINEA que cierra una linea de bloque (estado SL)."""
        texto_linea = self._lineas[numero_linea - 1]
        self._agregar(TipoToken.SALTO_LINEA, SALTO, numero_linea, len(texto_linea) + 1)

    # ------------------------------------------------------------------
    # Contexto: inicio de linea
    # ------------------------------------------------------------------

    @staticmethod
    def _saltar_espacios(linea: str, indice: int) -> int:
        """Devuelve el indice del primer caracter que no es espacio."""
        while indice < len(linea) and es_espacio(linea[indice]):
            indice += 1
        return indice

    def _analizar_inicio(self, linea: str) -> InicioLinea:
        """Recorre los estados del contexto de inicio de linea.

        Determina que bloque inicia la linea sin emitir tokens; la emision la
        hace el procesador del bloque correspondiente.
        """
        # S0: indentacion
        indice = 0
        sangria = 0
        while indice < len(linea) and es_espacio(linea[indice]):
            sangria += ANCHO_TABULACION if linea[indice] == TABULACION else 1
            indice += 1

        if indice == len(linea):
            return InicioLinea(LINEA_VACIA, indice, sangria, indice)  # S1

        caracter = linea[indice]
        siguiente = linea[indice + 1] if indice + 1 < len(linea) else ""

        if caracter == ACENTO_GRAVE:
            # A1 -> A2 -> F1: tres acentos graves forman la cerca
            fin = indice
            while fin < len(linea) and fin - indice < LONGITUD_CERCA and linea[fin] == ACENTO_GRAVE:
                fin += 1
            if fin - indice == LONGITUD_CERCA:
                return InicioLinea(LINEA_CODIGO, indice, sangria, fin)
            return InicioLinea(LINEA_PARRAFO, indice, sangria, indice)

        if caracter == NUMERAL:
            # H1 a H6, H7 para mas de seis
            fin = indice
            while fin < len(linea) and linea[fin] == NUMERAL:
                fin += 1
            if fin < len(linea) and es_espacio(linea[fin]):
                if fin - indice <= MAXIMO_NIVEL_ENCABEZADO:
                    return InicioLinea(LINEA_ENCABEZADO, indice, sangria, fin)
                return InicioLinea(LINEA_ENCABEZADO_INVALIDO, indice, sangria, fin)
            return InicioLinea(LINEA_PARRAFO, indice, sangria, indice)

        if caracter == MAYOR_QUE:
            return InicioLinea(LINEA_CITA, indice, sangria, indice + 1)  # C1

        if caracter == GUION:
            # G1: guion seguido de espacio es vineta
            if es_espacio(siguiente):
                return InicioLinea(LINEA_VINETA, indice, sangria, indice + 1)
            # G2, G3, G4: tres o mas guiones y solo espacios hasta el fin de linea
            fin = indice
            while fin < len(linea) and linea[fin] == GUION:
                fin += 1
            if fin - indice >= MINIMO_GUIONES_REGLA and self._saltar_espacios(linea, fin) == len(linea):
                return InicioLinea(LINEA_REGLA, indice, sangria, fin)
            return InicioLinea(LINEA_PARRAFO, indice, sangria, indice)

        if (caracter == ASTERISCO or caracter == MAS) and es_espacio(siguiente):
            return InicioLinea(LINEA_VINETA, indice, sangria, indice + 1)  # AS, MS

        return InicioLinea(LINEA_PARRAFO, indice, sangria, indice)

    def _procesar_bloque(self) -> None:
        """Tokeniza el siguiente bloque del documento y encola sus tokens."""
        if self._indice_linea >= len(self._lineas):
            linea_fin = len(self._lineas) + 1
            self._cerrar_lista(linea_fin, 1)
            self._agregar(TipoToken.FIN_ARCHIVO, "", linea_fin, 1)
            self._fin_generado = True
            return

        linea = self._lineas[self._indice_linea]
        inicio = self._analizar_inicio(linea)

        if inicio.clase != LINEA_VINETA:
            columna = 1 if inicio.clase == LINEA_VACIA else inicio.indice + 1
            self._cerrar_lista(self._indice_linea + 1, columna)

        if inicio.clase == LINEA_VACIA:
            self._procesar_lineas_vacias()
        elif inicio.clase == LINEA_ENCABEZADO:
            self._procesar_encabezado(linea, inicio)
        elif inicio.clase == LINEA_ENCABEZADO_INVALIDO:
            self._gestor.registrar(
                TipoError.ENCABEZADO_INVALIDO,
                linea[inicio.indice:inicio.fin_marcador],
                self._indice_linea + 1,
                inicio.indice + 1,
            )
            self._procesar_parrafo(inicio)
        elif inicio.clase == LINEA_CITA:
            self._procesar_cita(linea, inicio)
        elif inicio.clase == LINEA_CODIGO:
            self._procesar_bloque_codigo(linea, inicio)
        elif inicio.clase == LINEA_REGLA:
            self._procesar_regla(linea, inicio)
        elif inicio.clase == LINEA_VINETA:
            self._procesar_vineta(linea, inicio)
        else:
            self._procesar_parrafo(inicio)

    # ------------------------------------------------------------------
    # Procesadores de bloque
    # ------------------------------------------------------------------

    def _procesar_lineas_vacias(self) -> None:
        """Agrupa las lineas en blanco consecutivas en un solo SALTO_PARRAFO."""
        primera = self._indice_linea + 1
        cantidad = 0
        while (
            self._indice_linea < len(self._lineas)
            and self._analizar_inicio(self._lineas[self._indice_linea]).clase == LINEA_VACIA
        ):
            cantidad += 1
            self._indice_linea += 1
        self._agregar(TipoToken.SALTO_PARRAFO, SALTO * cantidad, primera, 1)

    def _procesar_encabezado(self, linea: str, inicio: InicioLinea) -> None:
        """Emite NUMERAL, el contenido en linea y SALTO_LINEA."""
        numero_linea = self._indice_linea + 1
        self._agregar(
            TipoToken.NUMERAL,
            linea[inicio.indice:inicio.fin_marcador],
            numero_linea,
            inicio.indice + 1,
        )
        contenido = self._saltar_espacios(linea, inicio.fin_marcador)
        self._tokenizar_en_linea([(numero_linea, contenido)])
        self._agregar_salto_linea(numero_linea)
        self._indice_linea += 1

    def _procesar_vineta(self, linea: str, inicio: InicioLinea) -> None:
        """Emite INDENT/DEDENT segun la pila de sangrias, VIÑETA y el contenido."""
        numero_linea = self._indice_linea + 1
        columna = inicio.indice + 1
        self._actualizar_sangria(inicio.sangria, numero_linea, columna)

        self._agregar(
            TipoToken.VINETA,
            linea[inicio.indice],
            numero_linea,
            columna,
            sangria=inicio.sangria,
        )
        contenido = self._saltar_espacios(linea, inicio.fin_marcador)
        self._tokenizar_en_linea([(numero_linea, contenido)])
        self._agregar_salto_linea(numero_linea)
        self._indice_linea += 1

    def _procesar_cita(self, linea: str, inicio: InicioLinea) -> None:
        """Estados C1 y C2: reconoce '>' repetidos, con o sin un espacio entre ellos.

        Si despues del ultimo '>' no hay espacio, el contenido se tokeniza
        igual; el parser detecta CITA_MAL_FORMADA al ver que el contenido
        empieza en la columna inmediata siguiente al marcador.
        """
        numero_linea = self._indice_linea + 1
        fin = inicio.indice
        while True:
            fin += 1  # consume '>'
            if fin < len(linea) and linea[fin] == MAYOR_QUE:
                continue  # C1 -> C1
            if fin + 1 < len(linea) and linea[fin] == ESPACIO and linea[fin + 1] == MAYOR_QUE:
                fin += 1  # C1 -> C2 -> C1
                continue
            break

        self._agregar(TipoToken.CITA, linea[inicio.indice:fin], numero_linea, inicio.indice + 1)
        contenido = self._saltar_espacios(linea, fin)
        self._tokenizar_en_linea([(numero_linea, contenido)])
        self._agregar_salto_linea(numero_linea)
        self._indice_linea += 1

    def _procesar_regla(self, linea: str, inicio: InicioLinea) -> None:
        """Emite REGLA_HORIZONTAL con los guiones y el SALTO_LINEA que la confirma."""
        numero_linea = self._indice_linea + 1
        self._agregar(
            TipoToken.REGLA_HORIZONTAL,
            linea[inicio.indice:inicio.fin_marcador],
            numero_linea,
            inicio.indice + 1,
        )
        self._agregar_salto_linea(numero_linea)
        self._indice_linea += 1

    def _procesar_parrafo(self, inicio: InicioLinea) -> None:
        """Reune las lineas consecutivas del parrafo y tokeniza su contenido.

        Una linea continua el parrafo si no esta en blanco y no inicia otro
        bloque. El salto de linea entre dos lineas del mismo parrafo forma
        parte del contenido en linea (salto suave).
        """
        segmentos = [(self._indice_linea + 1, inicio.indice)]
        self._indice_linea += 1

        while self._indice_linea < len(self._lineas):
            siguiente = self._analizar_inicio(self._lineas[self._indice_linea])
            if siguiente.clase != LINEA_PARRAFO:
                break
            segmentos.append((self._indice_linea + 1, siguiente.indice))
            self._indice_linea += 1

        self._tokenizar_en_linea(segmentos)
        self._agregar_salto_linea(segmentos[-1][0])

    # ------------------------------------------------------------------
    # Contexto: literal de bloque de codigo
    # ------------------------------------------------------------------

    def _es_cerca_de_cierre(self, linea: str) -> int:
        """Estados B0 a B3: verifica si la linea es la cerca de cierre.

        Returns:
            El indice del primer acento grave si la linea esta formada por
            indentacion opcional, tres acentos graves y espacios opcionales;
            -1 en caso contrario.
        """
        indice = self._saltar_espacios(linea, 0)
        fin = indice
        while fin < len(linea) and linea[fin] == ACENTO_GRAVE:
            fin += 1
        if fin - indice == LONGITUD_CERCA and self._saltar_espacios(linea, fin) == len(linea):
            return indice
        return -1

    def _procesar_bloque_codigo(self, linea: str, inicio: InicioLinea) -> None:
        """Emite la cerca de apertura, LENGUAJE, el contenido literal y la cerca de cierre.

        El contenido no se tokeniza: todo lo que hay entre las cercas se
        emite como un unico TEXTO_LITERAL.
        """
        numero_apertura = self._indice_linea + 1
        self._agregar(
            TipoToken.CERCA_CODIGO,
            linea[inicio.indice:inicio.fin_marcador],
            numero_apertura,
            inicio.indice + 1,
        )

        # LG: identificador de lenguaje, sin los espacios finales
        inicio_lenguaje = self._saltar_espacios(linea, inicio.fin_marcador)
        fin_lenguaje = len(linea)
        while fin_lenguaje > inicio_lenguaje and es_espacio(linea[fin_lenguaje - 1]):
            fin_lenguaje -= 1
        if inicio_lenguaje < fin_lenguaje:
            self._agregar(
                TipoToken.LENGUAJE,
                linea[inicio_lenguaje:fin_lenguaje],
                numero_apertura,
                inicio_lenguaje + 1,
            )
        self._agregar_salto_linea(numero_apertura)

        # B0-B4: lineas literales hasta la cerca de cierre o el fin del archivo
        indice_cierre = self._indice_linea + 1
        columna_cierre = -1
        while indice_cierre < len(self._lineas):
            columna_cierre = self._es_cerca_de_cierre(self._lineas[indice_cierre])
            if columna_cierre >= 0:
                break
            indice_cierre += 1

        contenido = self._lineas[self._indice_linea + 1:indice_cierre]
        if contenido:
            self._agregar(TipoToken.TEXTO_LITERAL, SALTO.join(contenido), numero_apertura + 1, 1)

        if indice_cierre < len(self._lineas):
            numero_cierre = indice_cierre + 1
            self._agregar(
                TipoToken.CERCA_CODIGO,
                ACENTO_GRAVE * LONGITUD_CERCA,
                numero_cierre,
                columna_cierre + 1,
            )
            self._agregar_salto_linea(numero_cierre)
            self._indice_linea = indice_cierre + 1
        else:
            self._gestor.registrar(
                TipoError.BLOQUE_CODIGO_SIN_CERRAR,
                ACENTO_GRAVE * LONGITUD_CERCA,
                numero_apertura,
                inicio.indice + 1,
            )
            self._indice_linea = len(self._lineas)

    # ------------------------------------------------------------------
    # Indentacion de listas (INDENT / DEDENT)
    # ------------------------------------------------------------------

    def _actualizar_sangria(self, sangria: int, linea: int, columna: int) -> None:
        """Compara la sangria de una vineta con la pila y emite INDENT o DEDENT.

        El primer item fija la base de la lista. Una sangria mayor que el
        tope apila un nivel; una menor desapila hasta alcanzarla. La pila
        nunca baja de la base: si la sangria no coincide con ningun nivel,
        el item queda en el nivel mas cercano y el parser reporta
        INDENTACION_INVALIDA.
        """
        if not self._pila_sangrias:
            self._pila_sangrias.append(sangria)
            return

        if sangria > self._pila_sangrias[-1]:
            self._pila_sangrias.append(sangria)
            self._agregar(TipoToken.INDENT, "", linea, columna)
            return

        while len(self._pila_sangrias) > 1 and sangria < self._pila_sangrias[-1]:
            self._pila_sangrias.pop()
            self._agregar(TipoToken.DEDENT, "", linea, columna)

    def _cerrar_lista(self, linea: int, columna: int) -> None:
        """Emite un DEDENT por cada nivel abierto y vacia la pila de sangrias."""
        for _ in range(len(self._pila_sangrias) - 1):
            self._agregar(TipoToken.DEDENT, "", linea, columna)
        self._pila_sangrias.clear()

    # ------------------------------------------------------------------
    # Contexto: contenido en linea y literal en linea
    # ------------------------------------------------------------------

    def _tokenizar_en_linea(self, segmentos: list[tuple[int, int]]) -> None:
        """Estados E0, T, I1, N2, K1, LI y K2 sobre el contenido de un bloque.

        Args:
            segmentos: Pares (numero de linea, indice de inicio) que forman el
                contenido del bloque. Entre dos segmentos se intercala un
                salto de linea suave.
        """
        caracteres = self._caracteres_del_bloque(segmentos)
        abiertos: list[Token] = []      # pila de NEGRITA/CURSIVA sin cerrar
        acentos_como_texto: set[int] = set()
        posicion = 0

        while posicion < len(caracteres):
            caracter = caracteres[posicion][0]

            if caracter == ASTERISCO:
                posicion = self._reconocer_asteriscos(caracteres, posicion, abiertos)

            elif caracter == ACENTO_GRAVE and posicion not in acentos_como_texto:
                posicion = self._reconocer_codigo_inline(caracteres, posicion, acentos_como_texto)

            else:
                # Estado T: avanza mientras no aparezca un delimitador
                inicio = posicion
                while posicion < len(caracteres) and not self._es_delimitador(
                    caracteres, posicion, acentos_como_texto
                ):
                    posicion += 1
                self._agregar_desde(TipoToken.TEXTO, caracteres, inicio, posicion)

        for token in abiertos:
            self._reportar_sin_cerrar(token)

    def _caracteres_del_bloque(self, segmentos: list[tuple[int, int]]) -> list[tuple[str, int, int]]:
        """Lista de (caracter, linea, columna) del contenido de un bloque."""
        caracteres: list[tuple[str, int, int]] = []
        for orden, (numero_linea, inicio) in enumerate(segmentos):
            texto_linea = self._lineas[numero_linea - 1]
            if orden > 0:
                anterior = segmentos[orden - 1][0]
                caracteres.append((SALTO, anterior, len(self._lineas[anterior - 1]) + 1))
            for indice in range(inicio, len(texto_linea)):
                caracteres.append((texto_linea[indice], numero_linea, indice + 1))
        return caracteres

    @staticmethod
    def _es_delimitador(
        caracteres: list[tuple[str, int, int]], posicion: int, acentos_como_texto: set[int]
    ) -> bool:
        """Indica si el caracter en la posicion termina un TEXTO."""
        caracter = caracteres[posicion][0]
        if caracter == ASTERISCO:
            return True
        return caracter == ACENTO_GRAVE and posicion not in acentos_como_texto

    def _agregar_desde(
        self,
        tipo: TipoToken,
        caracteres: list[tuple[str, int, int]],
        inicio: int,
        fin: int,
    ) -> Token:
        """Emite un token cuyo lexema son los caracteres [inicio, fin)."""
        lexema = "".join(caracteres[indice][0] for indice in range(inicio, fin))
        _, linea, columna = caracteres[inicio]
        return self._agregar(tipo, lexema, linea, columna)

    def _reconocer_asteriscos(
        self,
        caracteres: list[tuple[str, int, int]],
        posicion: int,
        abiertos: list[Token],
    ) -> int:
        """Estados I1 y N2: divide una secuencia de asteriscos en NEGRITA y CURSIVA.

        Aplica mayor coincidencia (** antes que *). La unica excepcion es una
        secuencia de tres o mas que cierra una cursiva abierta dentro de una
        negrita: se cierra primero la cursiva para mantener el anidamiento.

        Returns:
            La posicion siguiente a la secuencia.
        """
        restantes = 0
        while posicion + restantes < len(caracteres) and caracteres[posicion + restantes][0] == ASTERISCO:
            restantes += 1

        while restantes > 0:
            cierra_ambos = (
                restantes >= 3
                and len(abiertos) >= 2
                and abiertos[-1].tipo == TipoToken.CURSIVA
                and abiertos[-2].tipo == TipoToken.NEGRITA
            )
            if cierra_ambos:
                self._delimitador(TipoToken.CURSIVA, caracteres, posicion, 1, abiertos)
                self._delimitador(TipoToken.NEGRITA, caracteres, posicion + 1, 2, abiertos)
                posicion += 3
                restantes -= 3
            elif restantes >= 2:
                self._delimitador(TipoToken.NEGRITA, caracteres, posicion, 2, abiertos)
                posicion += 2
                restantes -= 2
            else:
                self._delimitador(TipoToken.CURSIVA, caracteres, posicion, 1, abiertos)
                posicion += 1
                restantes -= 1
        return posicion

    def _delimitador(
        self,
        tipo: TipoToken,
        caracteres: list[tuple[str, int, int]],
        posicion: int,
        largo: int,
        abiertos: list[Token],
    ) -> None:
        """Emite un delimitador y actualiza la pila de abiertos.

        Si ya hay un delimitador del mismo tipo abierto, este lo cierra; los
        que se abrieron despues y siguen abiertos quedan sin cerrar (cruce de
        delimitadores) y se reportan. En otro caso, abre uno nuevo.
        """
        token = self._agregar_desde(tipo, caracteres, posicion, posicion + largo)

        cierra = False
        for abierto in abiertos:
            if abierto.tipo == tipo:
                cierra = True

        if not cierra:
            abiertos.append(token)
            return

        while abiertos[-1].tipo != tipo:
            self._reportar_sin_cerrar(abiertos.pop())
        abiertos.pop()

    def _reportar_sin_cerrar(self, token: Token) -> None:
        """Registra un delimitador sin cerrar y lo reclasifica como TEXTO."""
        tipo_error = (
            TipoError.NEGRITA_SIN_CERRAR
            if token.tipo == TipoToken.NEGRITA
            else TipoError.CURSIVA_SIN_CERRAR
        )
        self._gestor.registrar(tipo_error, token.lexema, token.linea, token.columna)
        token.tipo = TipoToken.TEXTO

    def _reconocer_codigo_inline(
        self,
        caracteres: list[tuple[str, int, int]],
        posicion: int,
        acentos_como_texto: set[int],
    ) -> int:
        """Estados K1, LI y K2: codigo en linea con contenido literal.

        Si el bloque termina sin el acento grave de cierre se reporta el
        error y el acento de apertura pasa a ser parte del texto.

        Returns:
            La posicion desde donde continua el analisis.
        """
        cierre = posicion + 1
        while cierre < len(caracteres) and caracteres[cierre][0] != ACENTO_GRAVE:
            cierre += 1

        if cierre == len(caracteres):
            _, linea, columna = caracteres[posicion]
            self._gestor.registrar(TipoError.CODIGO_INLINE_SIN_CERRAR, ACENTO_GRAVE, linea, columna)
            acentos_como_texto.add(posicion)
            return posicion

        self._agregar_desde(TipoToken.CODIGO_INLINE, caracteres, posicion, posicion + 1)
        if cierre > posicion + 1:
            self._agregar_desde(TipoToken.TEXTO_LITERAL, caracteres, posicion + 1, cierre)
        self._agregar_desde(TipoToken.CODIGO_INLINE, caracteres, cierre, cierre + 1)
        return cierre + 1
