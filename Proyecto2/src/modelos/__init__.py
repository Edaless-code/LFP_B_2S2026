"""Modelos de datos compartidos por el analizador, los reportes y la interfaz."""

from modelos.error_analisis import ErrorAnalisis, Fase, TipoError
from modelos.nodo_ast import NodoAST
from modelos.tipo_token import TipoToken
from modelos.token import Token

__all__ = ["ErrorAnalisis", "Fase", "NodoAST", "TipoError", "TipoToken", "Token"]
