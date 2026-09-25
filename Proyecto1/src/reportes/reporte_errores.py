"""Reporte adicional de errores lexicos exigido por la seccion 4.8."""

from reportes.estilos import envolver, escapar


def generar(errores: list) -> str:
    """Genera el documento HTML con la tabla de errores lexicos.

    Args:
        errores: Lista de ErrorLexico acumulada por el GestorErrores.

    Returns:
        El documento HTML completo.
    """
    if not errores:
        cuerpo = (
            '<div class="vacio">El analisis no encontro errores lexicos.</div>'
        )
    else:
        filas = ""
        for error in errores:
            filas += (
                "<tr>"
                f'<td class="num">{error.numero}</td>'
                f"<td>{escapar(error.lexema)}</td>"
                f"<td>{escapar(error.tipo.value)}</td>"
                f"<td>{escapar(error.descripcion)}</td>"
                f'<td class="num">{error.linea}</td>'
                f'<td class="num">{error.columna}</td>'
                "</tr>"
            )
        cuerpo = (
            "<section><h2>Errores detectados</h2><table><thead><tr>"
            '<th class="num">No.</th><th>Lexema</th><th>Tipo de error</th>'
            '<th>Descripcion</th><th class="num">Linea</th><th class="num">Columna</th>'
            f"</tr></thead><tbody>{filas}</tbody></table></section>"
        )

    return envolver(
        "Reporte de Errores Lexicos",
        f"{len(errores)} errores encontrados durante el analisis",
        cuerpo,
    )
