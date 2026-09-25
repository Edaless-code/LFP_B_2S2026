"""Reconstruccion de las entidades del horario a partir de la lista de tokens.

El Proyecto 1 es un analizador lexico, no sintactico. Esta clase no valida la
gramatica del archivo: recorre la secuencia de tokens ya reconocida y extrae
de ella los datos necesarios para detectar choques y generar los reportes.
Los tokens mal formados simplemente no aportan datos, y el analisis continua.
"""

from modelos.entidades import Aula, Catedratico, Clase, Curso, Horario
from modelos.tipo_token import TipoToken

ELEMENTO_CURSO = "curso"
ELEMENTO_CATEDRATICO = "catedratico"
ELEMENTO_AULA = "aula"
ELEMENTO_CLASE = "clase"

RELACION_CATEDRATICO = "con"
RELACION_AULA = "en"

TIPOS_DE_VALOR = frozenset({
    TipoToken.CADENA,
    TipoToken.CODIGO,
    TipoToken.ENTERO,
    TipoToken.HORA,
    TipoToken.DIA,
    TipoToken.CATEGORIA,
})


class ConstructorHorario:
    """Construye un Horario recorriendo linealmente la lista de tokens."""

    def __init__(self, tokens: list) -> None:
        """Inicializa el constructor.

        Args:
            tokens: Lista de tokens producida por AnalizadorLexico.analizar_todo().
        """
        self._tokens = [
            token for token in tokens
            if token.tipo is not TipoToken.COMENTARIO_LINEA
        ]
        self._pos = 0

    # ------------------------------------------------------------------
    # Navegacion sobre la lista de tokens
    # ------------------------------------------------------------------

    def _actual(self):
        """Devuelve el token bajo el cursor, o None si se agoto la lista."""
        if self._pos < len(self._tokens):
            return self._tokens[self._pos]
        return None

    def _es_simbolo(self, lexema: str) -> bool:
        """Indica si el token actual es el simbolo indicado."""
        token = self._actual()
        return (token is not None
                and token.tipo is TipoToken.SIMBOLO
                and token.lexema == lexema)

    def _saltar_simbolo(self, lexema: str) -> None:
        """Consume el simbolo indicado si esta presente."""
        if self._es_simbolo(lexema):
            self._pos += 1

    @staticmethod
    def _sin_comillas(lexema: str) -> str:
        """Quita las comillas envolventes de un literal, si las tiene."""
        if len(lexema) >= 2 and lexema[0] == '"' and lexema[-1] == '"':
            return lexema[1:-1]
        return lexema

    def _leer_valor(self) -> str | None:
        """Consume y devuelve el valor bajo el cursor, sin comillas.

        Returns:
            El texto del valor, o None si el token actual no es un valor.
        """
        token = self._actual()
        if token is None or token.tipo not in TIPOS_DE_VALOR:
            return None
        self._pos += 1
        return self._sin_comillas(token.lexema)

    def _leer_valor_tras_relacion(self, relacion: str) -> str:
        """Consume 'con' o 'en' y devuelve el valor que le sigue.

        Args:
            relacion: Palabra reservada de relacion esperada.

        Returns:
            El valor asociado, o cadena vacia si la relacion no aparece.
        """
        token = self._actual()
        if (token is None
                or token.tipo is not TipoToken.PALABRA_RESERVADA_RELACION
                or token.lexema != relacion):
            return ""
        self._pos += 1
        return self._leer_valor() or ""

    def _leer_atributos(self) -> dict[str, str]:
        """Lee los pares 'atributo: valor' encerrados entre corchetes.

        Returns:
            Diccionario con los atributos encontrados. Vacio si no hay
            corchete de apertura en la posicion actual.
        """
        atributos: dict[str, str] = {}
        if not self._es_simbolo("["):
            return atributos

        self._pos += 1  # consume '['
        while self._pos < len(self._tokens):
            if self._es_simbolo("]"):
                self._pos += 1
                break

            token = self._actual()
            if token.tipo is TipoToken.PALABRA_RESERVADA_ATRIBUTO:
                nombre = token.lexema
                self._pos += 1
                self._saltar_simbolo(":")
                valor = self._leer_valor()
                if valor is not None:
                    atributos[nombre] = valor
            else:
                self._pos += 1

        return atributos

    @staticmethod
    def _a_entero(texto: str) -> int:
        """Convierte un texto a entero, devolviendo 0 si no es numerico."""
        total = 0
        if len(texto) == 0:
            return 0
        for caracter in texto:
            if not ("0" <= caracter <= "9"):
                return 0
            total = total * 10 + int(caracter)
        return total

    # ------------------------------------------------------------------
    # Construccion
    # ------------------------------------------------------------------

    def construir(self) -> Horario:
        """Recorre los tokens y arma el horario completo.

        Returns:
            Un Horario con los cursos, catedraticos, aulas y clases hallados.
        """
        horario = Horario()
        self._pos = 0

        while self._pos < len(self._tokens):
            token = self._actual()
            if token.tipo is TipoToken.PALABRA_RESERVADA_ELEMENTO:
                self._construir_elemento(horario)
            else:
                self._pos += 1

        return horario

    def _construir_elemento(self, horario: Horario) -> None:
        """Construye la entidad que corresponde al elemento bajo el cursor."""
        token = self._actual()
        elemento = token.lexema
        linea = token.linea

        self._pos += 1
        self._saltar_simbolo(":")
        principal = self._leer_valor()
        if principal is None:
            return

        if elemento == ELEMENTO_CURSO:
            atributos = self._leer_atributos()
            codigo = atributos.get("codigo", "")
            horario.cursos[codigo] = Curso(
                nombre=principal,
                codigo=codigo,
                creditos=self._a_entero(atributos.get("creditos", "")),
            )

        elif elemento == ELEMENTO_CATEDRATICO:
            atributos = self._leer_atributos()
            codigo = atributos.get("codigo", "")
            horario.catedraticos[codigo] = Catedratico(
                nombre=principal,
                codigo=codigo,
                categoria=atributos.get("categoria", ""),
            )

        elif elemento == ELEMENTO_AULA:
            # En AULAS el valor principal es el codigo del aula, no un nombre.
            atributos = self._leer_atributos()
            horario.aulas[principal] = Aula(
                codigo=principal,
                capacidad=self._a_entero(atributos.get("capacidad", "")),
                edificio=atributos.get("edificio", ""),
            )

        elif elemento == ELEMENTO_CLASE:
            codigo_catedratico = self._leer_valor_tras_relacion(RELACION_CATEDRATICO)
            codigo_aula = self._leer_valor_tras_relacion(RELACION_AULA)
            atributos = self._leer_atributos()
            horario.clases.append(Clase(
                codigo_curso=principal,
                codigo_catedratico=codigo_catedratico,
                codigo_aula=codigo_aula,
                dia=atributos.get("dia", ""),
                inicio=atributos.get("inicio", ""),
                fin=atributos.get("fin", ""),
                seccion=atributos.get("seccion", ""),
                linea=linea,
            ))
