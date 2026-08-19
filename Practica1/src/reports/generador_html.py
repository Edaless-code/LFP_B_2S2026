def _envolver_html(titulo, cuerpo):
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>{titulo}</title>
<style>
body {{ font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }}
h1 {{ color: #2c3e50; }}
table {{ border-collapse: collapse; width: 100%; background-color: white; }}
th, td {{ border: 1px solid #ccc; padding: 8px 12px; text-align: left; }}
th {{ background-color: #2c3e50; color: white; }}
tr:nth-child(even) {{ background-color: #f2f2f2; }}
</style>
</head>
<body>
<h1>{titulo}</h1>
{cuerpo}
</body>
</html>
"""


def generar_reporte_sudokus(resumen, ruta_salida):
    filas_html = ""
    for fila in resumen:
        filas_html += f"""<tr>
<td>{fila['id_sudoku']}</td>
<td>{fila['dificultad']}</td>
<td>{fila['cantidad_intentos']}</td>
<td>{fila['tiempo_promedio']}</td>
<td>{fila['tasa_exito']}%</td>
</tr>
"""
    cuerpo = f"""<table>
<tr><th>ID Sudoku</th><th>Dificultad</th><th>Intentos</th><th>Tiempo Promedio (s)</th><th>Tasa de Exito</th></tr>
{filas_html}</table>
"""
    html = _envolver_html("Resumen por Sudoku", cuerpo)
    with open(ruta_salida, "w", encoding="utf-8") as archivo:
        archivo.write(html)


def generar_reporte_jugadores(rendimiento, ruta_salida):
    filas_html = ""
    for fila in rendimiento:
        filas_html += f"""<tr>
<td>{fila['carnet']}</td>
<td>{fila['nombre_completo']}</td>
<td>{fila['nivel']}</td>
<td>{fila['cantidad_tableros']}</td>
<td>{fila['validez_promedio']}%</td>
<td>{fila['tiempo_promedio']}</td>
<td>{fila['resueltos_perfectos']}</td>
</tr>
"""
    cuerpo = f"""<table>
<tr><th>Carnet</th><th>Nombre</th><th>Nivel</th><th>Tableros Intentados</th><th>Validez Promedio</th><th>Tiempo Promedio (s)</th><th>Resueltos Perfectos</th></tr>
{filas_html}</table>
"""
    html = _envolver_html("Rendimiento por Jugador", cuerpo)
    with open(ruta_salida, "w", encoding="utf-8") as archivo:
        archivo.write(html)


def generar_reporte_top10(top10, ruta_salida):
    filas_html = ""
    for fila in top10:
        filas_html += f"""<tr>
<td>{fila['posicion']}</td>
<td>{fila['carnet']}</td>
<td>{fila['nombre_completo']}</td>
<td>{fila['id_sudoku']}</td>
<td>{fila['dificultad']}</td>
<td>{fila['tiempo_segundos']}</td>
</tr>
"""
    cuerpo = f"""<table>
<tr><th>Posicion</th><th>Carnet</th><th>Nombre</th><th>ID Sudoku</th><th>Dificultad</th><th>Tiempo (s)</th></tr>
{filas_html}</table>
"""
    html = _envolver_html("Top 10 Mejores Tiempos", cuerpo)
    with open(ruta_salida, "w", encoding="utf-8") as archivo:
        archivo.write(html)