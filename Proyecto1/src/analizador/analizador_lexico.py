"""Analizador lexico de HorarioScript implementado como AFD manual.

Recorre el texto caracter a caracter siguiendo la tabla de transiciones
documentada en docs/MANUAL_TECNICO.md, seccion 3.4. No utiliza el modulo re
ni metodos de cadena de alto nivel para la tokenizacion.
"""

from analizador.alfabeto import (
    COMILLA,
    DOS_PUNTOS,
    GUION,
    NUMERAL,
    es_alfanumerico,
    es_digito,
    es_espacio,
    es_letra,
    es_salto_linea,
    es_simbolo,
)
from analizador.gestor_errores import GestorErrores
from analizador.palabras_reservadas import (
    ATRIBUTO_CATEGORIA,
    ATRIBUTO_DIA,
    clasificar_palabra,
)
from modelos.error_lexico import TipoError
from modelos.tipo_token import TipoToken
from modelos.token import Token

ANCHO_TABULACION = 1
HORA_MINIMA_EN_MINUTOS = 6 * 60
HORA_MAXIMA_EN_MINUTOS = 21 * 60
MINUTO_MAXIMO = 59
DIGITOS_DE_HORA = 2


class AnalizadorLexico:
    """AFD manual que convierte el texto de un archivo .hor en tokens.

    El analisis no se detiene ante un error: lo delega al GestorErrores y
    continua hasta el final del archivo (recuperacion en modo panico).
    """

    def __init__(self, texto: str, gestor_errores: GestorErrores) -> None:
        """Inicializa el analizador.

        Args:
            texto: Contenido completo del archivo .hor.
            gestor_errores: Acumulador donde se registran los errores.
        """
        self._texto = texto
        self._gestor = gestor_errores
        self._pos = 0
        self._linea = 1
        self._columna = 1
        self._numero_token = 0
        self._ultimo_atributo = ""

    # ------------------------------------------------------------------
    # Primitivas de lectura
    # ------------------------------------------------------------------

    def _hay_mas(self) -> bool:
        """Indica si queda al menos un caracter por leer."""
        return self._pos < len(self._texto)

    def _caracter_actual(self) -> str:
        """Devuelve el caracter bajo el cursor, o cadena vacia si es EOF."""
        if self._hay_mas():
            return self._texto[self._pos]
        return ""

    def _mirar(self, desplazamiento: int = 1) -> str:
        """Devuelve un caracter adelantado sin consumirlo (lookahead).

        Args:
            desplazamiento: Cuantas posiciones mirar hacia adelante.

        Returns:
            El caracter en esa posicion, o cadena vacia si excede el texto.
        """
        indice = self._pos + desplazamiento
        if indice < len(self._texto):
            return self._texto[indice]
        return ""

    def _avanzar(self) -> str:
        """Consume el caracter actual y actualiza linea y columna.

        Returns:
            El caracter consumido, o cadena vacia si ya se llego a EOF.
        """
        caracter = self._caracter_actual()
        if caracter == "":
            return ""

        self._pos += 1
        if es_salto_linea(caracter):
            self._linea += 1
            self._columna = 1
        elif caracter == "\t":
            self._columna += ANCHO_TABULACION
        else:
            self._columna += 1
        return caracter

    def _crear_token(
        self, lexema: str, tipo: TipoToken, linea: int, columna: int
    ) -> Token:
        """Construye un token asignandole el siguiente numero correlativo."""
        self._numero_token += 1
        return Token(self._numero_token, lexema, tipo, linea, columna)

    # ------------------------------------------------------------------
    # Auxiliares de recuperacion y validacion
    # ------------------------------------------------------------------

    def _consumir_resto_invalido(self) -> str:
        """Consume el resto de una secuencia alfanumerica o con guiones.

        Se usa tras detectar un codigo mal formado, para que el fragmento
        completo se reporte como un unico error en lugar de fragmentarse.
        """
        resto = ""
        while es_alfanumerico(self._caracter_actual()) or self._caracter_actual() == GUION:
            resto += self._avanzar()
        return resto

    def _consumir_resto_hora_invalida(self) -> str:
        """Consume el resto de una secuencia de digitos y dos puntos.

        Evita que '7:00' produzca tres reportes (error, SIMBOLO, ENTERO)
        en lugar de uno solo.
        """
        resto = ""
        while es_digito(self._caracter_actual()) or self._caracter_actual() == DOS_PUNTOS:
            resto += self._avanzar()
        return resto

    def _hora_en_rango(self, lexema: str) -> bool:
        """Valida el rango institucional de una hora con formato HH:MM.

        Esta validacion es semantica y ocurre fuera del automata, sobre el
        lexema ya reconocido. Ver manual tecnico, seccion 4.2.

        Args:
            lexema: Cadena de exactamente cinco caracteres, DD:DD.

        Returns:
            True si la hora esta entre 06:00 y 21:00 y los minutos son validos.
        """
        horas = int(lexema[0]) * 10 + int(lexema[1])
        minutos = int(lexema[3]) * 10 + int(lexema[4])
        if minutos > MINUTO_MAXIMO:
            return False
        total = horas * 60 + minutos
        return HORA_MINIMA_EN_MINUTOS <= total <= HORA_MAXIMA_EN_MINUTOS

    def _error_de_palabra_desconocida(self) -> TipoError:
        """Elige el tipo de error segun el ultimo atributo emitido.

        Implementa el contexto minimo de la opcion B documentada en el
        manual tecnico, seccion 4.6.
        """
        if self._ultimo_atributo == ATRIBUTO_DIA:
            return TipoError.DIA_NO_RECONOCIDO
        if self._ultimo_atributo == ATRIBUTO_CATEGORIA:
            return TipoError.CATEGORIA_NO_RECONOCIDA
        return TipoError.PALABRA_NO_RECONOCIDA

    def _contenido_es_codigo(self, contenido: str) -> bool:
        """Verifica si el texto cumple el patron de codigo: L (L|D)* - D+.

        Args:
            contenido: Texto interior de un literal, sin las comillas.

        Returns:
            True si el contenido completo cumple el patron de codigo.
        """
        total = len(contenido)
        if total == 0 or not es_letra(contenido[0]):
            return False

        indice = 0
        while indice < total and es_alfanumerico(contenido[indice]):
            indice += 1
        if indice >= total or contenido[indice] != GUION:
            return False

        indice += 1
        if indice >= total or not es_digito(contenido[indice]):
            return False
        while indice < total and es_digito(contenido[indice]):
            indice += 1
        return indice == total

    # ------------------------------------------------------------------
    # Lectores por rama del AFD
    # ------------------------------------------------------------------

    def _leer_palabra_o_codigo(self) -> Token | None:
        """Reconoce los estados q1, q2 y q3: palabras reservadas y codigos.

        Precondicion: el caracter actual es una letra.

        Returns:
            El token reconocido, o None si se registro un error.
        """
        linea_inicio = self._linea
        columna_inicio = self._columna
        lexema = ""

        # Estado q1: maximal munch sobre la secuencia alfanumerica.
        while es_alfanumerico(self._caracter_actual()):
            lexema += self._avanzar()

        # Estado q1 -> q2: el guion abre la posibilidad de un CODIGO.
        if self._caracter_actual() == GUION:
            lexema += self._avanzar()

            # Estado q2: tras el guion debe venir al menos un digito.
            if not es_digito(self._caracter_actual()):
                lexema += self._consumir_resto_invalido()
                self._gestor.registrar(
                    TipoError.CODIGO_MAL_FORMADO, lexema, linea_inicio, columna_inicio
                )
                return None

            # Estado q3: digitos del codigo.
            while es_digito(self._caracter_actual()):
                lexema += self._avanzar()

            # Estado q3: una letra o un segundo guion invalidan el codigo.
            actual = self._caracter_actual()
            if es_letra(actual) or actual == GUION:
                lexema += self._consumir_resto_invalido()
                self._gestor.registrar(
                    TipoError.CODIGO_MAL_FORMADO, lexema, linea_inicio, columna_inicio
                )
                return None

            self._ultimo_atributo = ""
            return self._crear_token(
                lexema, TipoToken.CODIGO, linea_inicio, columna_inicio
            )

        # Estado q1: aceptacion por retroceso, se clasifica por tabla.
        tipo = clasificar_palabra(lexema)
        if tipo is None:
            self._gestor.registrar(
                self._error_de_palabra_desconocida(),
                lexema,
                linea_inicio,
                columna_inicio,
            )
            self._ultimo_atributo = ""
            return None

        if tipo is TipoToken.PALABRA_RESERVADA_ATRIBUTO:
            self._ultimo_atributo = lexema
        else:
            self._ultimo_atributo = ""

        return self._crear_token(lexema, tipo, linea_inicio, columna_inicio)

    def _leer_cadena(self) -> Token | None:
        """Reconoce el estado q10: literales entre comillas dobles.

        Al cerrar la comilla subclasifica el contenido: CODIGO si cumple el
        patron L (L|D)* - D+, CADENA en caso contrario. Ver manual tecnico,
        seccion 4.3.

        Precondicion: el caracter actual es una comilla doble.

        Returns:
            El token reconocido, o None si la cadena quedo sin cerrar.
        """
        linea_inicio = self._linea
        columna_inicio = self._columna

        lexema = self._avanzar()  # comilla de apertura
        contenido = ""

        # Estado q10: cualquier caracter excepto comilla y salto de linea.
        while self._hay_mas():
            actual = self._caracter_actual()
            if actual == COMILLA or es_salto_linea(actual):
                break
            contenido += self._avanzar()

        # EOF o salto de linea sin cierre: se reporta en la posicion de apertura.
        if not self._hay_mas() or es_salto_linea(self._caracter_actual()):
            self._gestor.registrar(
                TipoError.CADENA_SIN_CERRAR,
                lexema + contenido,
                linea_inicio,
                columna_inicio,
            )
            return None

        lexema += contenido + self._avanzar()  # comilla de cierre

        tipo = (
            TipoToken.CODIGO
            if self._contenido_es_codigo(contenido)
            else TipoToken.CADENA
        )
        return self._crear_token(lexema, tipo, linea_inicio, columna_inicio)

    def _leer_comentario(self) -> Token | None:
        """Reconoce los estados q11 y q12: comentarios de linea.

        Precondicion: el caracter actual es un numeral.

        Returns:
            El token de comentario, o None si el numeral estaba solo.
        """
        linea_inicio = self._linea
        columna_inicio = self._columna

        # Estado q11: se requiere un segundo numeral.
        if self._mirar() != NUMERAL:
            lexema = self._avanzar()
            self._gestor.registrar(
                TipoError.CARACTER_NO_RECONOCIDO, lexema, linea_inicio, columna_inicio
            )
            return None

        lexema = self._avanzar() + self._avanzar()

        # Estado q12: todo hasta el salto de linea o EOF.
        while self._hay_mas() and not es_salto_linea(self._caracter_actual()):
            lexema += self._avanzar()

        return self._crear_token(
            lexema, TipoToken.COMENTARIO_LINEA, linea_inicio, columna_inicio
        )

    def _leer_numero_u_hora(self) -> Token | None:
        """Reconoce los estados q4, q5 y q6: enteros y apertura de hora.

        Los tres estados se distinguen unicamente por la cantidad de digitos
        consumidos, asi que se representan con un contador en lugar de tres
        bloques de codigo duplicados.

        Precondicion: el caracter actual es un digito.

        Returns:
            Un token ENTERO u HORA, o None si se registro un error.
        """
        linea_inicio = self._linea
        columna_inicio = self._columna
        self._ultimo_atributo = ""

        # Estados q4, q5 y q6: consume la secuencia completa de digitos.
        lexema = self._avanzar()
        digitos = 1
        while es_digito(self._caracter_actual()):
            lexema += self._avanzar()
            digitos += 1

        siguiente = self._caracter_actual()

        # Un guion tras digitos no abre un codigo valido: el patron exige
        # que todo codigo comience con letra.
        if siguiente == GUION:
            lexema += self._avanzar() + self._consumir_resto_invalido()
            self._gestor.registrar(
                TipoError.CODIGO_MAL_FORMADO, lexema, linea_inicio, columna_inicio
            )
            return None

        if siguiente == DOS_PUNTOS:
            # Solo q5, es decir exactamente dos digitos, admite los dos puntos.
            if digitos != DIGITOS_DE_HORA:
                lexema += self._consumir_resto_hora_invalida()
                self._gestor.registrar(
                    TipoError.HORA_FUERA_DE_RANGO, lexema, linea_inicio, columna_inicio
                )
                return None
            return self._leer_minutos(lexema, linea_inicio, columna_inicio)

        # Aceptacion por retroceso desde q4, q5 o q6.
        return self._crear_token(
            lexema, TipoToken.ENTERO, linea_inicio, columna_inicio
        )

    def _leer_minutos(
        self, lexema: str, linea_inicio: int, columna_inicio: int
    ) -> Token | None:
        """Reconoce los estados q7, q8 y q9: la parte MM de un literal de hora.

        Args:
            lexema: Los dos digitos de la hora ya consumidos.
            linea_inicio: Linea donde inicia el literal.
            columna_inicio: Columna donde inicia el literal.

        Returns:
            El token HORA, o None si el formato o el rango son invalidos.
        """
        # Estado q5 -> q7: consume los dos puntos.
        lexema += self._avanzar()

        # Estados q7 y q8: se exigen exactamente dos digitos de minutos.
        for _ in range(DIGITOS_DE_HORA):
            if not es_digito(self._caracter_actual()):
                lexema += self._consumir_resto_hora_invalida()
                self._gestor.registrar(
                    TipoError.HORA_FUERA_DE_RANGO, lexema, linea_inicio, columna_inicio
                )
                return None
            lexema += self._avanzar()

        # Estado q9: un digito o unos dos puntos adicionales rompen HH:MM.
        if es_digito(self._caracter_actual()) or self._caracter_actual() == DOS_PUNTOS:
            lexema += self._consumir_resto_hora_invalida()
            self._gestor.registrar(
                TipoError.HORA_FUERA_DE_RANGO, lexema, linea_inicio, columna_inicio
            )
            return None

        # Estado q9: la forma es correcta; falta la validacion semantica.
        if not self._hora_en_rango(lexema):
            self._gestor.registrar(
                TipoError.HORA_FUERA_DE_RANGO, lexema, linea_inicio, columna_inicio
            )
            return None

        return self._crear_token(lexema, TipoToken.HORA, linea_inicio, columna_inicio)

    # ------------------------------------------------------------------
    # API publica
    # ------------------------------------------------------------------

    def siguiente_token(self) -> Token:
        """Devuelve el siguiente token del archivo y avanza el cursor.

        Los errores se registran en el GestorErrores y el analisis continua
        (recuperacion en modo panico). Al agotarse la entrada devuelve un
        token de tipo FIN_ARCHIVO.

        Returns:
            El siguiente token reconocido, o FIN_ARCHIVO si ya no queda texto.
        """
        while True:
            # Estado q0: los blancos y saltos de linea son delimitadores
            # silenciosos. No producen token, pero si mueven los contadores.
            while self._hay_mas() and (
                es_espacio(self._caracter_actual())
                or es_salto_linea(self._caracter_actual())
            ):
                self._avanzar()

            # Estado q0 con EOF: se acabo la entrada.
            if not self._hay_mas():
                return self._crear_token(
                    "", TipoToken.FIN_ARCHIVO, self._linea, self._columna
                )

            # La posicion se captura antes de consumir el primer caracter.
            linea_inicio = self._linea
            columna_inicio = self._columna
            actual = self._caracter_actual()

            # Estado q0: despacho hacia la rama correspondiente del AFD.
            if es_letra(actual):
                token = self._leer_palabra_o_codigo()
            elif es_digito(actual):
                token = self._leer_numero_u_hora()
            elif actual == COMILLA:
                token = self._leer_cadena()
            elif actual == NUMERAL:
                token = self._leer_comentario()
            elif es_simbolo(actual):
                lexema = self._avanzar()
                token = self._crear_token(
                    lexema, TipoToken.SIMBOLO, linea_inicio, columna_inicio
                )
            else:
                lexema = self._avanzar()
                self._gestor.registrar(
                    TipoError.CARACTER_NO_RECONOCIDO,
                    lexema,
                    linea_inicio,
                    columna_inicio,
                )
                token = None

            if token is not None:
                return token
            # Si token es None hubo un error: no se devuelve nada y el bucle
            # reinicia para buscar el siguiente token valido. La ausencia de
            # return en este punto es la recuperacion en modo panico.

    def analizar_todo(self) -> list[Token]:
        """Analiza el texto completo y devuelve todos los tokens reconocidos.

        Reinicia el estado antes de empezar, de modo que puede invocarse
        varias veces sobre la misma instancia.

        Returns:
            Lista de tokens sin incluir el marcador FIN_ARCHIVO.
        """
        self.reiniciar()
        tokens: list[Token] = []
        while True:
            token = self.siguiente_token()
            if token.tipo is TipoToken.FIN_ARCHIVO:
                return tokens
            tokens.append(token)

    def reiniciar(self) -> None:
        """Devuelve el analizador y su gestor de errores al estado inicial."""
        self._pos = 0
        self._linea = 1
        self._columna = 1
        self._numero_token = 0
        self._ultimo_atributo = ""
        self._gestor.limpiar()
