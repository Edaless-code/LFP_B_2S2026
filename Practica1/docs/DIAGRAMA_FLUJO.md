# Diagrama de Flujo

Representacion grafica del proceso general del sistema: lectura de archivos,
validacion matricial del tablero, calculo de estadisticas y generacion de
reportes.

```mermaid
flowchart TD
    Inicio([Inicio]) --> Menu[Mostrar menu principal]
    Menu --> Opcion{Opcion seleccionada}

    Opcion -->|1| CargaSudokus[Leer sudokus.lfp con open/readlines\nsplit por coma\ncrear objetos Tablero]
    CargaSudokus --> Menu

    Opcion -->|2| CargaJugadores[Leer jugadores.lfp\nsplit por coma\ncrear objetos Jugador]
    CargaJugadores --> Menu

    Opcion -->|3| CargaIntentos[Leer intentos.lfp\nsplit por coma\ncrear objetos Intento]
    CargaIntentos --> Menu

    Opcion -->|4| Validar[Para cada intento:\nbuscar su Tablero por id_sudoku]
    Validar --> ValidarUnidades[Validar 9 filas, 9 columnas\ny 9 cajas 3x3]
    ValidarUnidades --> ValidarPistas[Verificar que las pistas\noriginales no cambiaron]
    ValidarPistas --> CalcularPorcentaje[Calcular porcentaje de validez\nunidades_validas / 27 * 100]
    CalcularPorcentaje --> GuardarResultado[Guardar resultado en el\nobjeto Intento]
    GuardarResultado --> Menu

    Opcion -->|5| Reporte1[Agrupar intentos por sudoku\nCalcular tiempo promedio y tasa de exito]
    Reporte1 --> HTML1[Generar reporte_sudokus.html]
    HTML1 --> Menu

    Opcion -->|6| Reporte2[Agrupar intentos por jugador\nCalcular validez y tiempo promedio]
    Reporte2 --> HTML2[Generar reporte_jugadores.html]
    HTML2 --> Menu

    Opcion -->|7| Reporte3[Filtrar intentos resueltos al 100%\nOrdenar por tiempo\nTomar los primeros 10]
    Reporte3 --> HTML3[Generar reporte_top10.html]
    HTML3 --> Menu

    Opcion -->|8| Fin([Fin del programa])
    Opcion -->|Otra| Invalida[Mostrar mensaje de opcion invalida]
    Invalida --> Menu
```

## Detalle del subproceso de validacion (opcion 4)

```mermaid
flowchart TD
    A[Recibir matriz original y matriz solucion] --> B[Contador = 0]
    B --> C[Revisar las 9 filas]
    C --> D[Revisar las 9 columnas]
    D --> E[Revisar las 9 cajas de 3x3]
    E --> F[Cada unidad valida suma 1 al contador]
    F --> G[Porcentaje = contador / 27 * 100]
    G --> H[Verificar que las celdas con pista\nno hayan cambiado]
    H --> I{Porcentaje = 100%\ny pistas respetadas?}
    I -->|Si| J[resuelto_correctamente = True]
    I -->|No| K[resuelto_correctamente = False]
```
