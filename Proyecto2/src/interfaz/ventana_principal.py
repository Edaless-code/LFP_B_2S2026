"""Ventana principal de MarkdownCheck (PyQt6).

La ventana solo orquesta: lee el archivo con el CargadorArchivos, ejecuta el
analisis lexico y sintactico, muestra los resultados y pide al
GeneradorReportes que escriba los reportes. No contiene logica de analisis.
"""

import os
import time

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import (
    QAction,
    QCloseEvent,
    QColor,
    QDesktopServices,
    QDragEnterEvent,
    QDropEvent,
    QFont,
    QKeySequence,
)
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextBrowser,
    QToolBar,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from analizador.analizador_lexico import AnalizadorLexico
from analizador.analizador_sintactico import AnalizadorSintactico
from analizador.gestor_errores import GestorErrores
from interfaz import tema
from interfaz.editor_codigo import EditorCodigo
from modelos.error_analisis import ErrorAnalisis, Fase
from modelos.nodo_ast import NodoAST
from modelos.token import Token
from reportes.generador_html import GeneradorHTML
from reportes.generador_reportes import GeneradorReportes, SalidasGeneradas
from servicios.cargador_archivos import CargadorArchivos, ErrorCarga

NOMBRE_APLICACION = "MarkdownCheck"
DIRECTORIO_PROYECTO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DIRECTORIO_EJEMPLOS = os.path.join(DIRECTORIO_PROYECTO, "examples")
DIRECTORIO_SALIDAS = os.path.join(DIRECTORIO_PROYECTO, "salidas")
NOMBRE_SIN_TITULO = "sin_titulo.md"
FILTRO_MARKDOWN = "Archivos Markdown (*.md)"

COLUMNAS_TOKENS = ["No.", "Lexema", "Tipo", "Línea", "Columna"]
COLUMNAS_ERRORES = ["No.", "Lexema", "Tipo", "Fase", "Descripción", "Línea", "Columna"]
COLUMNAS_ARBOL = ["Símbolo", "Lexema", "Línea", "Columna"]

PESTANA_TOKENS = 0
PESTANA_ERRORES = 1
PESTANA_ARBOL = 2

# Subconjunto de CSS que interpreta QTextBrowser para la vista previa
CSS_VISTA_PREVIA = """
body { font-size: 11pt; }
h1, h2 { color: #1F2933; }
code { background-color: #EEF1F4; font-family: monospace; }
pre { background-color: #EEF1F4; color: #1F2933; font-family: monospace; }
blockquote { color: #52606D; margin-left: 18px; }
"""

TEXTO_INICIAL = (
    "Abra un archivo .md o escriba en el editor y presione Analizar (F5)."
)

AYUDA_SINTAXIS = """
<h3>Sintaxis Markdown soportada</h3>
<table cellpadding="4">
<tr><td><b>Encabezados</b></td><td><code># Título</code> a <code>###### Título</code></td></tr>
<tr><td><b>Párrafo</b></td><td>Texto separado por una línea en blanco</td></tr>
<tr><td><b>Negrita</b></td><td><code>**texto**</code></td></tr>
<tr><td><b>Cursiva</b></td><td><code>*texto*</code></td></tr>
<tr><td><b>Código en línea</b></td><td><code>`código`</code></td></tr>
<tr><td><b>Lista</b></td><td><code>- elemento</code>, <code>* elemento</code> o <code>+ elemento</code><br>
2 espacios por cada nivel de anidamiento</td></tr>
<tr><td><b>Cita</b></td><td><code>&gt; texto</code>; anidada con <code>&gt;&gt;</code> o <code>&gt; &gt;</code></td></tr>
<tr><td><b>Bloque de código</b></td><td><code>```lenguaje</code> ... <code>```</code></td></tr>
<tr><td><b>Regla horizontal</b></td><td><code>---</code></td></tr>
</table>
"""

ACERCA_DE = f"""
<h3>{NOMBRE_APLICACION}</h3>
<p>Analizador léxico-sintáctico de Markdown a HTML.</p>
<p>Analizador léxico implementado como AFD manual y analizador sintáctico
descendente recursivo, sin librerías de parsing ni de conversión Markdown.</p>
<p><b>Autor:</b> Edgar Alessandro Chocon Oliva<br>
<b>Carnet:</b> 202212978<br>
<b>Curso:</b> Lenguajes Formales y de Programación, Sección B+<br>
Universidad de San Carlos de Guatemala, Segundo Semestre 2026</p>
"""


class VentanaPrincipal(QMainWindow):
    """Ventana con el editor a la izquierda y los resultados a la derecha."""

    def __init__(self) -> None:
        super().__init__()
        self._ruta: str | None = None
        self._tokens: list[Token] = []
        self._errores: list[ErrorAnalisis] = []
        self._raiz: NodoAST | None = None
        self._analisis_vigente = False
        self._salidas: SalidasGeneradas | None = None
        self._generador_reportes = GeneradorReportes(DIRECTORIO_SALIDAS)

        self.setWindowTitle(NOMBRE_APLICACION)
        self.resize(1320, 820)
        self.setMinimumSize(960, 600)
        self.setAcceptDrops(True)

        self._crear_acciones()
        self._crear_menu()
        self._crear_barra_herramientas()
        self._crear_contenido()
        self._crear_barra_estado()

        self.editor.textChanged.connect(self._al_cambiar_texto)
        self.editor.cursorPositionChanged.connect(self._actualizar_posicion)
        self.editor.document().modificationChanged.connect(self._actualizar_titulo)

        self._limpiar_resultados()
        self._actualizar_titulo()

    # ------------------------------------------------------------------
    # Construccion de la interfaz
    # ------------------------------------------------------------------

    def _crear_accion(self, texto: str, atajo, funcion, consejo: str) -> QAction:
        accion = QAction(texto, self)
        accion.setShortcut(QKeySequence(atajo))
        accion.setToolTip(f"{consejo} ({QKeySequence(atajo).toString()})")
        accion.setStatusTip(consejo)
        accion.triggered.connect(funcion)
        return accion

    def _crear_acciones(self) -> None:
        self.accion_nuevo = self._crear_accion("Nuevo", QKeySequence.StandardKey.New, self._nuevo, "Documento en blanco")
        self.accion_abrir = self._crear_accion("Abrir", QKeySequence.StandardKey.Open, self._abrir, "Abrir un archivo .md")
        self.accion_guardar = self._crear_accion("Guardar", QKeySequence.StandardKey.Save, self._guardar, "Guardar el documento")
        self.accion_guardar_como = self._crear_accion(
            "Guardar como...", "Ctrl+Shift+S", self._guardar_como, "Guardar el documento con otro nombre"
        )
        self.accion_analizar = self._crear_accion("Analizar", "F5", self._analizar, "Ejecutar el análisis léxico y sintáctico")
        self.accion_salir = self._crear_accion("Salir", "Ctrl+Q", self.close, "Cerrar la aplicación")
        self.accion_sintaxis = self._crear_accion("Sintaxis soportada", "F1", self._mostrar_sintaxis, "Ver la sintaxis Markdown soportada")
        self.accion_acerca = QAction("Acerca de", self)
        self.accion_acerca.triggered.connect(self._mostrar_acerca_de)

        self.accion_documento = self._crear_accion(
            "Documento", "Ctrl+1", lambda: self._abrir_salida("documento"), "Abrir el Reporte 1: documento HTML"
        )
        self.accion_estadisticas = self._crear_accion(
            "Estadísticas", "Ctrl+2", lambda: self._abrir_salida("estadisticas"), "Abrir el Reporte 2: estadísticas"
        )
        self.accion_indice = self._crear_accion(
            "Índice", "Ctrl+3", lambda: self._abrir_salida("indice"), "Abrir el Reporte 3: tabla de contenido"
        )
        self.accion_arbol = self._crear_accion(
            "Árbol", "Ctrl+4", self._abrir_arbol, "Abrir el árbol de derivación generado con Graphviz"
        )
        self.accion_reporte_errores = self._crear_accion(
            "Errores", "Ctrl+5", lambda: self._abrir_salida("errores"), "Abrir el reporte HTML de errores"
        )
        self.accion_carpeta = self._crear_accion(
            "Carpeta de salidas", "Ctrl+6", lambda: self._abrir_salida("directorio"), "Abrir la carpeta con los archivos generados"
        )
        self._acciones_reportes = [
            self.accion_documento,
            self.accion_estadisticas,
            self.accion_indice,
            self.accion_arbol,
            self.accion_reporte_errores,
            self.accion_carpeta,
        ]

    def _crear_menu(self) -> None:
        menu_archivo = self.menuBar().addMenu("&Archivo")
        menu_archivo.addActions([self.accion_nuevo, self.accion_abrir, self.accion_guardar, self.accion_guardar_como])
        menu_archivo.addSeparator()
        menu_archivo.addAction(self.accion_salir)

        menu_analisis = self.menuBar().addMenu("A&nálisis")
        menu_analisis.addAction(self.accion_analizar)

        menu_reportes = self.menuBar().addMenu("&Reportes")
        menu_reportes.addActions([self.accion_documento, self.accion_estadisticas, self.accion_indice])
        menu_reportes.addSeparator()
        menu_reportes.addActions([self.accion_arbol, self.accion_reporte_errores, self.accion_carpeta])

        menu_ayuda = self.menuBar().addMenu("A&yuda")
        menu_ayuda.addActions([self.accion_sintaxis, self.accion_acerca])

    def _crear_barra_herramientas(self) -> None:
        barra = QToolBar("Principal", self)
        barra.setMovable(False)
        barra.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        barra.addActions([self.accion_nuevo, self.accion_abrir, self.accion_guardar])
        barra.addSeparator()
        barra.addAction(self.accion_analizar)
        barra.widgetForAction(self.accion_analizar).setObjectName("botonAnalizar")
        barra.addSeparator()
        barra.addActions(self._acciones_reportes)
        self.addToolBar(barra)

    def _crear_panel(self, titulo: str) -> tuple[QFrame, QVBoxLayout, QLabel]:
        """Panel con borde redondeado, titulo y una etiqueta de detalle."""
        panel = QFrame()
        panel.setObjectName("panel")
        diseno = QVBoxLayout(panel)
        diseno.setContentsMargins(0, 12, 0, 0)
        diseno.setSpacing(8)

        encabezado = QHBoxLayout()
        encabezado.setContentsMargins(14, 0, 14, 0)
        etiqueta_titulo = QLabel(titulo)
        etiqueta_titulo.setObjectName("tituloPanel")
        etiqueta_detalle = QLabel()
        etiqueta_detalle.setObjectName("detallePanel")
        encabezado.addWidget(etiqueta_titulo)
        encabezado.addStretch()
        encabezado.addWidget(etiqueta_detalle)
        diseno.addLayout(encabezado)
        return panel, diseno, etiqueta_detalle

    def _crear_contenido(self) -> None:
        # Panel izquierdo: editor
        panel_editor, diseno_editor, self.etiqueta_archivo = self._crear_panel("Documento")
        self.editor = EditorCodigo()
        self.editor.setPlaceholderText("Escriba aquí su documento Markdown o arrastre un archivo .md a la ventana.")
        diseno_editor.addWidget(self.editor)

        # Panel derecho: resultados
        panel_resultados, diseno_resultados, self.etiqueta_tiempo = self._crear_panel("Resultados del análisis")
        self.banner = QLabel()
        self.banner.setWordWrap(True)
        contenedor_banner = QHBoxLayout()
        contenedor_banner.setContentsMargins(14, 0, 14, 0)
        contenedor_banner.addWidget(self.banner)
        diseno_resultados.addLayout(contenedor_banner)

        self.tabla_tokens = self._crear_tabla(COLUMNAS_TOKENS, columna_flexible=1)
        self.tabla_errores = self._crear_tabla(COLUMNAS_ERRORES, columna_flexible=None)
        self.arbol = self._crear_arbol()
        self.tabla_tokens.cellDoubleClicked.connect(lambda fila, _: self._ir_a_fila(self.tabla_tokens, fila, 3))
        self.tabla_errores.cellDoubleClicked.connect(lambda fila, _: self._ir_a_fila(self.tabla_errores, fila, 5))

        self.pestanas = QTabWidget()
        self.pestanas.addTab(self.tabla_tokens, "Tokens")
        self.pestanas.addTab(self.tabla_errores, "Errores")
        self.pestanas.addTab(self.arbol, "Árbol de derivación")
        self.vista_previa = QTextBrowser()
        self.vista_previa.setOpenLinks(False)
        self.vista_previa.document().setDefaultStyleSheet(CSS_VISTA_PREVIA)
        self.vista_previa.document().setDocumentMargin(16)
        self.pestanas.addTab(self.vista_previa, "Vista previa")
        diseno_resultados.addWidget(self.pestanas)

        divisor = QSplitter(Qt.Orientation.Horizontal)
        divisor.addWidget(panel_editor)
        divisor.addWidget(panel_resultados)
        divisor.setSizes([560, 760])
        divisor.setHandleWidth(12)
        divisor.setChildrenCollapsible(False)

        central = QWidget()
        diseno = QHBoxLayout(central)
        diseno.setContentsMargins(12, 12, 12, 12)
        diseno.addWidget(divisor)
        self.setCentralWidget(central)

    def _crear_tabla(self, columnas: list[str], columna_flexible: int | None) -> QTableWidget:
        """Tabla de solo lectura y ordenable.

        Args:
            columnas: Encabezados de las columnas.
            columna_flexible: Columna que ocupa el espacio libre. Con None todas
                las columnas se ajustan a su contenido y aparece una barra de
                desplazamiento horizontal si no caben.
        """
        tabla = QTableWidget(0, len(columnas))
        tabla.setHorizontalHeaderLabels(columnas)
        tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        tabla.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        tabla.setAlternatingRowColors(True)
        tabla.setShowGrid(False)
        tabla.setWordWrap(False)
        tabla.verticalHeader().setVisible(False)
        tabla.verticalHeader().setDefaultSectionSize(28)
        cabecera = tabla.horizontalHeader()
        cabecera.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        cabecera.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        if columna_flexible is None:
            cabecera.setStretchLastSection(True)
        else:
            cabecera.setSectionResizeMode(columna_flexible, QHeaderView.ResizeMode.Stretch)
        tabla.setSortingEnabled(True)
        return tabla

    def _crear_arbol(self) -> QTreeWidget:
        arbol = QTreeWidget()
        arbol.setHeaderLabels(COLUMNAS_ARBOL)
        arbol.setAlternatingRowColors(True)
        arbol.setUniformRowHeights(True)
        arbol.header().setStretchLastSection(False)
        arbol.header().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        arbol.header().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        arbol.itemDoubleClicked.connect(self._ir_a_nodo)
        return arbol

    def _crear_barra_estado(self) -> None:
        self.etiqueta_posicion = QLabel()
        self.statusBar().addPermanentWidget(self.etiqueta_posicion)
        self._actualizar_posicion()

    # ------------------------------------------------------------------
    # Archivos
    # ------------------------------------------------------------------

    def _directorio_dialogo(self) -> str:
        if self._ruta:
            return os.path.dirname(self._ruta)
        if os.path.isdir(DIRECTORIO_EJEMPLOS):
            return DIRECTORIO_EJEMPLOS
        return os.path.expanduser("~")

    def _confirmar_descartar(self) -> bool:
        """Pregunta que hacer con los cambios sin guardar.

        Returns:
            True si se puede continuar (se guardo o se descarto).
        """
        if not self.editor.document().isModified():
            return True
        respuesta = QMessageBox.question(
            self,
            "Cambios sin guardar",
            "El documento tiene cambios sin guardar. ¿Desea guardarlos?",
            QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Save,
        )
        if respuesta == QMessageBox.StandardButton.Save:
            return self._guardar()
        return respuesta == QMessageBox.StandardButton.Discard

    def _nuevo(self) -> None:
        if not self._confirmar_descartar():
            return
        self._ruta = None
        self.editor.clear()
        self.editor.document().setModified(False)
        self._limpiar_resultados()
        self._actualizar_titulo()

    def _abrir(self) -> None:
        if not self._confirmar_descartar():
            return
        ruta, _ = QFileDialog.getOpenFileName(self, "Abrir archivo Markdown", self._directorio_dialogo(), FILTRO_MARKDOWN)
        if ruta:
            self.abrir_ruta(ruta)

    def abrir_ruta(self, ruta: str) -> bool:
        """Carga un archivo .md en el editor.

        Returns:
            True si el archivo se cargo correctamente.
        """
        try:
            texto = CargadorArchivos.cargar(ruta)
        except ErrorCarga as error:
            QMessageBox.warning(self, "No se pudo abrir el archivo", str(error))
            return False

        self._ruta = os.path.abspath(ruta)
        self.editor.setPlainText(texto)
        self.editor.document().setModified(False)
        self._limpiar_resultados()
        self._actualizar_titulo()
        lineas = self.editor.blockCount()
        self.statusBar().showMessage(f"Archivo cargado: {os.path.basename(ruta)} ({lineas} líneas)", 5000)
        return True

    def _guardar(self) -> bool:
        if self._ruta is None:
            return self._guardar_como()
        return self._escribir(self._ruta)

    def _guardar_como(self) -> bool:
        ruta, _ = QFileDialog.getSaveFileName(
            self, "Guardar archivo Markdown", self._ruta or self._directorio_dialogo(), FILTRO_MARKDOWN
        )
        if not ruta:
            return False
        if not ruta.lower().endswith(".md"):
            ruta += ".md"
        return self._escribir(ruta)

    def _escribir(self, ruta: str) -> bool:
        try:
            CargadorArchivos.guardar(ruta, self.editor.toPlainText())
        except ErrorCarga as error:
            QMessageBox.warning(self, "No se pudo guardar el archivo", str(error))
            return False
        self._ruta = os.path.abspath(ruta)
        self.editor.document().setModified(False)
        self._actualizar_titulo()
        self.statusBar().showMessage(f"Guardado: {os.path.basename(ruta)}", 5000)
        return True

    # ------------------------------------------------------------------
    # Analisis
    # ------------------------------------------------------------------

    def _analizar(self) -> None:
        """Ejecuta el analisis lexico y sintactico y muestra los resultados."""
        texto = self.editor.toPlainText()
        try:
            inicio = time.perf_counter()
            gestor = GestorErrores()
            lexico = AnalizadorLexico(texto, gestor)
            raiz = AnalizadorSintactico(lexico, gestor).analizar()
            milisegundos = (time.perf_counter() - inicio) * 1000
        except Exception as error:  # la interfaz nunca debe cerrarse por un fallo interno
            QMessageBox.critical(self, "Error interno", f"Ocurrió un error inesperado durante el análisis:\n\n{error}")
            return

        self._tokens = lexico.tokens
        self._errores = gestor.errores
        self._raiz = raiz
        self._analisis_vigente = True

        self._mostrar_tokens()
        self._mostrar_errores()
        self._mostrar_arbol()
        self.vista_previa.setHtml(GeneradorHTML(raiz).generar_cuerpo())
        self.editor.marcar_lineas_error({error.linea for error in self._errores})
        self.etiqueta_tiempo.setText(f"{milisegundos:.1f} ms")
        self._actualizar_banner()
        self._generar_salidas()

    def _generar_salidas(self) -> None:
        """Escribe los reportes del analisis actual en salidas/<archivo>/.

        Sin errores se generan los tres reportes y arbol.dot; con errores,
        solo el reporte de errores.
        """
        nombre = os.path.basename(self._ruta) if self._ruta else NOMBRE_SIN_TITULO
        try:
            if self._errores:
                self._salidas = self._generador_reportes.generar_errores(self._errores, nombre)
            else:
                self._salidas = self._generador_reportes.generar(self._raiz, nombre)
        except OSError as error:
            self._salidas = None
            QMessageBox.warning(self, "No se pudieron generar los reportes", str(error))
        self._actualizar_acciones_reportes()

        if self._salidas is not None:
            carpeta = os.path.relpath(self._salidas.directorio, DIRECTORIO_PROYECTO)
            if self._errores:
                mensaje = f"Reporte de errores generado en {carpeta}. Corrija los errores para generar los reportes 1, 2 y 3."
            else:
                mensaje = f"Reportes y arbol.dot generados en {carpeta}"
            self.statusBar().showMessage(mensaje, 8000)

    def _actualizar_acciones_reportes(self) -> None:
        """Habilita solo los botones de los archivos que existen."""
        salidas = self._salidas
        exito = salidas is not None and salidas.documento is not None
        for accion in (self.accion_documento, self.accion_estadisticas, self.accion_indice, self.accion_arbol):
            accion.setEnabled(exito)
        self.accion_reporte_errores.setEnabled(salidas is not None and salidas.errores is not None)
        self.accion_carpeta.setEnabled(salidas is not None)

    def _abrir_salida(self, atributo: str) -> None:
        """Abre con la aplicacion predeterminada un archivo o carpeta generado."""
        ruta = getattr(self._salidas, atributo, None) if self._salidas else None
        if not ruta or not os.path.exists(ruta):
            QMessageBox.information(self, "Reporte no disponible", "Ejecute el análisis para generar este archivo.")
            return
        if not QDesktopServices.openUrl(QUrl.fromLocalFile(ruta)):
            QMessageBox.information(self, "Abrir archivo", f"El archivo se encuentra en:\n{ruta}")

    def _abrir_arbol(self) -> None:
        """Abre el SVG del arbol; si Graphviz no esta instalado, indica donde esta arbol.dot."""
        if self._salidas is not None and self._salidas.arbol_imagen:
            self._abrir_salida("arbol_imagen")
            return
        ruta = self._salidas.arbol_dot if self._salidas else None
        if not ruta:
            QMessageBox.information(self, "Árbol no disponible", "Ejecute el análisis para generar arbol.dot.")
            return
        QMessageBox.information(
            self,
            "Árbol de derivación",
            "Se generó el archivo arbol.dot, pero Graphviz no está instalado para convertirlo en imagen.\n\n"
            f"Archivo: {ruta}\n\n"
            "Instale Graphviz (https://graphviz.org) o pegue el contenido del archivo en un visor DOT en línea.",
        )
        self._abrir_salida("directorio")

    def _actualizar_banner(self) -> None:
        if not self._errores:
            self.banner.setObjectName("bannerExito")
            self.banner.setText(
                f"Análisis completado sin errores: {len(self._tokens)} tokens reconocidos."
            )
            self.pestanas.setCurrentIndex(PESTANA_TOKENS)
        else:
            lexicos = sum(1 for error in self._errores if error.fase == Fase.LEXICO)
            sintacticos = len(self._errores) - lexicos
            total = len(self._errores)
            self.banner.setObjectName("bannerError")
            self.banner.setText(
                f"Se {'encontró' if total == 1 else 'encontraron'} {total} "
                f"{'error' if total == 1 else 'errores'} ({lexicos} léxicos, {sintacticos} sintácticos). "
                "Haga doble clic en un error para ubicarlo en el documento."
            )
            self.pestanas.setCurrentIndex(PESTANA_ERRORES)
        self._refrescar_estilo(self.banner)

    def _limpiar_resultados(self) -> None:
        self._tokens = []
        self._errores = []
        self._raiz = None
        self._analisis_vigente = False
        self.tabla_tokens.setRowCount(0)
        self.tabla_errores.setRowCount(0)
        self.arbol.clear()
        self.vista_previa.clear()
        self._salidas = None
        self._actualizar_acciones_reportes()
        self.pestanas.setTabText(PESTANA_TOKENS, "Tokens")
        self.pestanas.setTabText(PESTANA_ERRORES, "Errores")
        self.editor.marcar_lineas_error(set())
        self.etiqueta_tiempo.setText("")
        self._mostrar_aviso(TEXTO_INICIAL)

    def _mostrar_aviso(self, texto: str) -> None:
        self.banner.setObjectName("bannerNeutro")
        self.banner.setText(texto)
        self._refrescar_estilo(self.banner)

    def _al_cambiar_texto(self) -> None:
        """Marca los resultados como desactualizados cuando se edita el documento."""
        if self._analisis_vigente:
            self._analisis_vigente = False
            self.editor.marcar_lineas_error(set())
            self._mostrar_aviso("El documento cambió desde el último análisis. Presione Analizar (F5) para actualizar.")

    # ------------------------------------------------------------------
    # Presentacion de resultados
    # ------------------------------------------------------------------

    @staticmethod
    def _celda(valor) -> QTableWidgetItem:
        """Celda de tabla; los enteros se guardan como numero para ordenar bien."""
        celda = QTableWidgetItem()
        if isinstance(valor, int):
            celda.setData(Qt.ItemDataRole.DisplayRole, valor)
            celda.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        else:
            celda.setText(str(valor))
        return celda

    def _llenar_tabla(self, tabla: QTableWidget, filas: list[tuple]) -> None:
        tabla.setSortingEnabled(False)
        tabla.setRowCount(len(filas))
        for indice_fila, fila in enumerate(filas):
            for indice_columna, valor in enumerate(fila):
                tabla.setItem(indice_fila, indice_columna, self._celda(valor))
        tabla.setSortingEnabled(True)
        tabla.sortByColumn(0, Qt.SortOrder.AscendingOrder)

    def _mostrar_tokens(self) -> None:
        self._llenar_tabla(self.tabla_tokens, [token.a_fila() for token in self._tokens])
        gris = QColor(tema.TEXTO_SECUNDARIO)
        for fila, token in enumerate(self._tokens):
            if token.tipo.es_virtual:
                for columna in range(len(COLUMNAS_TOKENS)):
                    self.tabla_tokens.item(fila, columna).setForeground(gris)
        self.pestanas.setTabText(PESTANA_TOKENS, f"Tokens ({len(self._tokens)})")

    def _mostrar_errores(self) -> None:
        self._llenar_tabla(self.tabla_errores, [error.a_fila() for error in self._errores])
        rojo = QColor(tema.ERROR)
        for fila in range(self.tabla_errores.rowCount()):
            self.tabla_errores.item(fila, 2).setForeground(rojo)
            descripcion = self.tabla_errores.item(fila, 4)
            descripcion.setToolTip(descripcion.text())
        self.pestanas.setTabText(PESTANA_ERRORES, f"Errores ({len(self._errores)})")

    def _mostrar_arbol(self) -> None:
        self.arbol.clear()
        if self._raiz is not None:
            self.arbol.addTopLevelItem(self._crear_item_arbol(self._raiz))
            self.arbol.expandAll()

    def _crear_item_arbol(self, nodo: NodoAST) -> QTreeWidgetItem:
        """Convierte un NodoAST y sus hijos en elementos del QTreeWidget."""
        if nodo.es_terminal:
            token = nodo.token
            item = QTreeWidgetItem([nodo.simbolo, token.lexema_visible, str(token.linea), str(token.columna)])
            item.setForeground(0, QColor(tema.TERMINAL))
            item.setData(0, Qt.ItemDataRole.UserRole, (token.linea, token.columna))
        else:
            item = QTreeWidgetItem([nodo.simbolo, "", "", ""])
            item.setForeground(0, QColor(tema.NO_TERMINAL))
            fuente = QFont(item.font(0))
            fuente.setBold(True)
            item.setFont(0, fuente)
            for hijo in nodo.hijos:
                item.addChild(self._crear_item_arbol(hijo))
        return item

    # ------------------------------------------------------------------
    # Navegacion y estado
    # ------------------------------------------------------------------

    def _ir_a_fila(self, tabla: QTableWidget, fila: int, columna_linea: int) -> None:
        """Ubica en el editor la posicion de la fila (columnas Linea y Columna)."""
        linea = tabla.item(fila, columna_linea).data(Qt.ItemDataRole.DisplayRole)
        columna = tabla.item(fila, columna_linea + 1).data(Qt.ItemDataRole.DisplayRole)
        self.editor.ir_a(int(linea), int(columna))

    def _ir_a_nodo(self, item: QTreeWidgetItem, _columna: int) -> None:
        posicion = item.data(0, Qt.ItemDataRole.UserRole)
        if posicion:
            self.editor.ir_a(*posicion)

    def _actualizar_posicion(self) -> None:
        linea, columna = self.editor.posicion_cursor()
        self.etiqueta_posicion.setText(f"Línea {linea}, columna {columna}   ")

    def _actualizar_titulo(self, *_args) -> None:
        nombre = os.path.basename(self._ruta) if self._ruta else "Sin título"
        modificado = self.editor.document().isModified()
        self.etiqueta_archivo.setText(f"{nombre}{' (modificado)' if modificado else ''}")
        self.setWindowTitle(f"{nombre}{'*' if modificado else ''} - {NOMBRE_APLICACION}")

    @staticmethod
    def _refrescar_estilo(widget: QWidget) -> None:
        """Vuelve a aplicar la hoja de estilos despues de cambiar el objectName."""
        widget.style().unpolish(widget)
        widget.style().polish(widget)

    def _mostrar_sintaxis(self) -> None:
        QMessageBox.information(self, "Sintaxis soportada", AYUDA_SINTAXIS)

    def _mostrar_acerca_de(self) -> None:
        QMessageBox.about(self, f"Acerca de {NOMBRE_APLICACION}", ACERCA_DE)

    # ------------------------------------------------------------------
    # Eventos de la ventana
    # ------------------------------------------------------------------

    def dragEnterEvent(self, evento: QDragEnterEvent) -> None:
        """Acepta archivos .md arrastrados sobre la ventana."""
        urls = evento.mimeData().urls()
        if urls and urls[0].toLocalFile().lower().endswith(".md"):
            evento.acceptProposedAction()

    def dropEvent(self, evento: QDropEvent) -> None:
        if self._confirmar_descartar():
            self.abrir_ruta(evento.mimeData().urls()[0].toLocalFile())

    def closeEvent(self, evento: QCloseEvent) -> None:
        if self._confirmar_descartar():
            evento.accept()
        else:
            evento.ignore()
