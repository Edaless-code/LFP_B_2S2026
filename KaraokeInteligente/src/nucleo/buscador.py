"""Identificacion de canciones a partir de unas cuantas palabras de su letra.

Se usa igual en el modo manual (palabras tecleadas) y en el automatico
(palabras transcritas por la IA). El procedimiento es:

1. Se normalizan las palabras (sin tildes, minusculas) y se descartan
   vocalizaciones como "la la la" u "oh".
2. Cada palabra se compara con el vocabulario de la base, aceptando palabras
   parecidas ("corazon" ~ "corazones") para tolerar errores de escritura o de
   transcripcion.
3. Con un indice invertido (palabra -> lineas donde aparece) se eligen las
   lineas candidatas, ponderando cada palabra por lo poco comun que es (IDF):
   "cucaracha" pesa mucho mas que "la".
4. Cada candidata se evalua contra ventanas de 1 a 4 lineas consecutivas con
   una alineacion de subsecuencia comun (LCS) ponderada, que respeta el orden
   de las palabras.
5. El puntaje (0 a 1) es la fraccion del peso de la consulta que se encontro,
   corregida por la densidad de la coincidencia.
"""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass

from nucleo.modelos import Coincidencia
from nucleo.texto import normalizar, palabras, palabras_significativas, similitud_palabras

UMBRAL_PALABRA = 0.78
MAX_LINEAS_CANDIDATAS = 60
MAX_LINEAS_VENTANA = 4


@dataclass
class Alineacion:
    puntaje: float
    linea_inicio: int
    linea_fin: int
    progreso: float
    palabras_encontradas: int


class BuscadorCanciones:
    def __init__(self, repositorio) -> None:
        self.repositorio = repositorio
        self._revision = -1
        self.nombres: dict[int, str] = {}
        self.lineas: dict[int, list[str]] = {}
        self.tokens: dict[int, list[list[str]]] = {}
        self.indice: dict[str, set[tuple[int, int]]] = defaultdict(set)
        self.frecuencia: dict[str, int] = defaultdict(int)
        self.trigramas: dict[str, set[str]] = defaultdict(set)
        self.total_lineas = 0
        self._equivalentes: dict[str, dict[str, float]] = {}

    # ================================================================== indice
    def asegurar_indice(self) -> None:
        if self._revision != self.repositorio.revision:
            self.reconstruir()

    def reconstruir(self) -> None:
        self.nombres.clear()
        self.lineas.clear()
        self.tokens.clear()
        self.indice = defaultdict(set)
        self.frecuencia = defaultdict(int)
        self.trigramas = defaultdict(set)
        self._equivalentes.clear()
        for codigo, nombre, indice_linea, linea in self.repositorio.todas_las_lineas():
            self.nombres[codigo] = nombre
            self.lineas.setdefault(codigo, []).append(linea)
            fichas = palabras(linea)
            self.tokens.setdefault(codigo, []).append(fichas)
            for palabra in set(fichas):
                self.indice[palabra].add((codigo, indice_linea))
                self.frecuencia[palabra] += 1
        for palabra in self.indice:
            for trigrama in _trigramas(palabra):
                self.trigramas[trigrama].add(palabra)
        self.total_lineas = sum(len(l) for l in self.lineas.values())
        self._revision = self.repositorio.revision

    def peso(self, palabra: str) -> float:
        """Peso IDF: las palabras raras identifican mejor una cancion."""
        total = max(1, self.total_lineas)
        frecuencia = self.frecuencia.get(palabra, 0)
        if frecuencia == 0:
            return math.log((total + 1) / 1.5) * 0.7
        return max(0.15, math.log((total + 1) / (frecuencia + 0.5)))

    def equivalentes(self, palabra: str) -> dict[str, float]:
        """Palabras del vocabulario iguales o parecidas a `palabra`, con su similitud."""
        if palabra in self._equivalentes:
            return self._equivalentes[palabra]
        resultado: dict[str, float] = {}
        if palabra in self.indice:
            resultado[palabra] = 1.0
        if len(palabra) >= 3:
            candidatas: set[str] = set()
            for trigrama in _trigramas(palabra):
                candidatas |= self.trigramas.get(trigrama, set())
            for candidata in candidatas:
                if candidata in resultado:
                    continue
                similitud = similitud_palabras(palabra, candidata)
                if similitud >= UMBRAL_PALABRA:
                    resultado[candidata] = similitud
        self._equivalentes[palabra] = resultado
        return resultado

    # ============================================================== busqueda
    def preparar_consulta(self, texto: str) -> list[str]:
        return palabras_significativas(texto)

    def buscar(
        self,
        texto: str,
        limite: int = 5,
        bonificaciones: dict[int, float] | None = None,
        incluir_titulos: bool = True,
    ) -> list[Coincidencia]:
        """Devuelve las canciones mas parecidas al texto, la mejor primero (una por cancion)."""
        self.asegurar_indice()
        consulta = self.preparar_consulta(texto)
        if not consulta:
            return []
        candidatas = self._lineas_candidatas(consulta)
        mejores: dict[int, Coincidencia] = {}
        evaluadas: set[tuple[int, int, int]] = set()
        for codigo, indice_linea in candidatas:
            for inicio in (indice_linea - 1, indice_linea):
                if inicio < 0:
                    continue
                for largo in range(1, MAX_LINEAS_VENTANA + 1):
                    fin = inicio + largo - 1
                    if fin >= len(self.tokens[codigo]):
                        break
                    clave = (codigo, inicio, fin)
                    if clave in evaluadas:
                        continue
                    evaluadas.add(clave)
                    alineacion = self.alinear(consulta, codigo, inicio, fin)
                    if alineacion is None:
                        continue
                    actual = mejores.get(codigo)
                    if actual is None or alineacion.puntaje > actual.puntaje + 1e-9:
                        mejores[codigo] = Coincidencia(
                            codigo=codigo,
                            nombre=self.nombres[codigo],
                            puntaje=alineacion.puntaje,
                            linea_inicio=alineacion.linea_inicio,
                            linea_fin=alineacion.linea_fin,
                            texto_linea=self.lineas[codigo][alineacion.linea_fin],
                            progreso_en_linea=alineacion.progreso,
                        )
                    if self._cantidad_fichas(codigo, inicio, fin) >= len(consulta) + 3:
                        break
        if incluir_titulos:
            self._buscar_en_titulos(texto, mejores)
        if bonificaciones:
            for codigo, extra in bonificaciones.items():
                if codigo in mejores:
                    mejores[codigo].puntaje = min(1.0, mejores[codigo].puntaje + extra)
        resultado = sorted(mejores.values(), key=lambda c: (-c.puntaje, c.codigo))
        return resultado[:limite]

    def _cantidad_fichas(self, codigo: int, inicio: int, fin: int) -> int:
        return sum(len(self.tokens[codigo][i]) for i in range(inicio, fin + 1))

    def _lineas_candidatas(self, consulta: list[str]) -> list[tuple[int, int]]:
        puntajes: dict[tuple[int, int], float] = defaultdict(float)
        for palabra in set(consulta):
            peso = self.peso(palabra)
            vistas: dict[tuple[int, int], float] = {}
            for equivalente, similitud in self.equivalentes(palabra).items():
                for ubicacion in self.indice.get(equivalente, ()):
                    if similitud > vistas.get(ubicacion, 0.0):
                        vistas[ubicacion] = similitud
            for ubicacion, similitud in vistas.items():
                puntajes[ubicacion] += peso * similitud
        ordenadas = sorted(puntajes.items(), key=lambda p: -p[1])
        return [ubicacion for ubicacion, _ in ordenadas[:MAX_LINEAS_CANDIDATAS]]

    def _buscar_en_titulos(self, texto: str, mejores: dict[int, Coincidencia]) -> None:
        buscado = normalizar(texto)
        if len(buscado) < 3:
            return
        for codigo, nombre in self.nombres.items():
            titulo = normalizar(nombre)
            if buscado == titulo:
                puntaje = 1.0
            elif len(buscado) >= 5 and buscado in titulo:
                puntaje = 0.6 + 0.35 * len(buscado) / max(1, len(titulo))
            else:
                continue
            actual = mejores.get(codigo)
            if actual is None or puntaje > actual.puntaje:
                mejores[codigo] = Coincidencia(
                    codigo=codigo,
                    nombre=nombre,
                    puntaje=puntaje,
                    linea_inicio=0,
                    linea_fin=0,
                    texto_linea=self.lineas[codigo][0] if self.lineas.get(codigo) else "",
                    progreso_en_linea=0.0,
                    por_titulo=True,
                )

    # ============================================================== alineacion
    def alinear(self, consulta: list[str], codigo: int, inicio: int, fin: int) -> Alineacion | None:
        """Alinea la consulta contra las lineas inicio..fin (inclusive) de una cancion.

        Es una LCS ponderada: cada palabra de la consulta puede emparejarse con
        una palabra igual o parecida de la letra, respetando el orden.
        """
        lineas_cancion = self.tokens.get(codigo)
        if not lineas_cancion or not consulta:
            return None
        ventana: list[str] = []
        linea_de: list[int] = []
        posicion_en_linea: list[float] = []
        for indice in range(max(0, inicio), min(fin, len(lineas_cancion) - 1) + 1):
            fichas = lineas_cancion[indice]
            for posicion, ficha in enumerate(fichas):
                ventana.append(ficha)
                linea_de.append(indice)
                posicion_en_linea.append((posicion + 1) / len(fichas))
        if not ventana:
            return None
        pesos = [self.peso(p) for p in consulta]
        total = sum(pesos)
        similitudes = [self.equivalentes(p) for p in consulta]
        largo = len(ventana)
        # Cada celda: (puntaje, primer indice, ultimo indice, palabras emparejadas)
        vacio = (0.0, -1, -1, 0)
        anterior = [vacio] * (largo + 1)
        for i, palabra in enumerate(consulta):
            equivalentes = similitudes[i]
            if palabra not in equivalentes:
                equivalentes = dict(equivalentes)
                equivalentes[palabra] = 1.0
            peso = pesos[i]
            actual = [vacio] * (largo + 1)
            for j in range(largo):
                arriba = anterior[j + 1]
                izquierda = actual[j]
                mejor = arriba if arriba[0] >= izquierda[0] else izquierda
                similitud = equivalentes.get(ventana[j])
                if similitud:
                    diagonal = anterior[j]
                    candidato = diagonal[0] + peso * similitud
                    if candidato > mejor[0] + 1e-12 or (abs(candidato - mejor[0]) <= 1e-12 and j > mejor[2]):
                        primero = diagonal[1] if diagonal[1] >= 0 else j
                        mejor = (candidato, primero, j, diagonal[3] + 1)
                actual[j + 1] = mejor
            anterior = actual
        puntaje, primero, ultimo, emparejadas = anterior[largo]
        if emparejadas == 0:
            return None
        cobertura = puntaje / total if total else 0.0
        extension = ultimo - primero + 1
        densidad = min(1.0, emparejadas / extension) if extension else 0.0
        return Alineacion(
            puntaje=min(1.0, cobertura * (0.8 + 0.2 * densidad)),
            linea_inicio=linea_de[primero],
            linea_fin=linea_de[ultimo],
            progreso=posicion_en_linea[ultimo],
            palabras_encontradas=emparejadas,
        )

    def lineas_de(self, codigo: int) -> list[list[str]]:
        self.asegurar_indice()
        return self.tokens.get(codigo, [])


def _trigramas(palabra: str) -> set[str]:
    marcada = f"#{palabra}#"
    return {marcada[i : i + 3] for i in range(len(marcada) - 2)}
