"""Interfaz grafica de escritorio de HorarioScript, construida con Tkinter.

La ventana es una capa delgada: no contiene logica de analisis. Se limita a
pedir el archivo, delegar en el analizador, el constructor del horario, el
detector de choques y el generador de reportes, y mostrar los resultados.
"""

import csv
import json
import os
import time
import tkinter as tk
import webbrowser
from tkinter import filedialog, messagebox, ttk

from analizador.analizador_lexico import AnalizadorLexico
from analizador.gestor_errores import GestorErrores
from horario.constructor_horario import ConstructorHorario
from horario.detector_choques import DetectorChoques
from reportes.generador_reportes import GeneradorReportes
from servicios.cargador_archivos import CargadorArchivos, ErrorDeCarga

TITULO = "HorarioScript - Analizador Lexico"
AUTOR = "Edgar Alessandro Chocon Oliva - 202212978"

ANCHO_VENTANA = 1200
ALTO_VENTANA = 760
ANCHO_MINIMO = 980
ALTO_MINIMO = 620

FUENTE_CODIGO = ("Consolas", 10)
FUENTE_TITULO = ("Segoe UI", 11, "bold")

COLUMNAS_TOKENS = (
    ("numero", "No.", 60),
    ("lexema", "Lexema", 280),
    ("tipo", "Tipo de token", 240),
    ("linea", "Linea", 70),
    ("columna", "Columna", 80),
)

COLUMNAS_ERRORES = (
    ("numero", "No.", 60),
    ("lexema", "Lexema", 160),
    ("tipo", "Tipo de error", 210),
    ("descripcion", "Descripcion", 430),
    ("linea", "Linea", 70),
    ("columna", "Columna", 80),
)

COLUMNAS_CHOQUES = (
    ("numero", "No.", 60),
    ("tipo", "Tipo", 130),
    ("recurso", "Recurso", 120),
    ("dia", "Dia", 110),
    ("bloque_a", "Bloque A", 130),
    ("bloque_b", "Bloque B", 130),
    ("descripcion", "Descripcion", 430),
)

COLUMNAS_RESUMEN = (
    ("concepto", "Concepto", 320),
    ("valor", "Valor", 240),
)


class AplicacionHorarioScript(tk.Tk):
    """Ventana principal del analizador lexico de HorarioScript."""

    def __init__(self) -> None:
        """Construye la ventana y deja la aplicacion lista para usarse."""
        super().__init__()

        self.title(TITULO)
        self.geometry(f"{ANCHO_VENTANA}x{ALTO_VENTANA}")
        self.minsize(ANCHO_MINIMO, ALTO_MINIMO)

        self._ruta_actual = ""
        self._tokens = []
        self._errores = []
        self._choques = []
        self._horario = None
        self._rutas_reportes = {}
        self._duracion_ms = 0.0

        self._directorio_proyecto = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )

        self._construir_interfaz()
        self._actualizar_botones()

    # ------------------------------------------------------------------
    # Construccion de la interfaz
    # ------------------------------------------------------------------

    def _construir_interfaz(self) -> None:
        """Arma las cuatro zonas de la ventana."""
        self._construir_barra_superior()
        self._construir_cuerpo()
        self._construir_barra_reportes()
        self._construir_barra_estado()

    def _construir_barra_superior(self) -> None:
        """Barra con las acciones de archivo y analisis."""
        barra = ttk.Frame(self, padding=(10, 8))
        barra.pack(side=tk.TOP, fill=tk.X)

        self._boton_abrir = ttk.Button(
            barra, text="Abrir archivo .hor", command=self._abrir_archivo
        )
        self._boton_abrir.pack(side=tk.LEFT)

        self._boton_analizar = ttk.Button(
            barra, text="Analizar", command=self._analizar
        )
        self._boton_analizar.pack(side=tk.LEFT, padx=(8, 0))

        self._boton_limpiar = ttk.Button(
            barra, text="Limpiar", command=self._limpiar
        )
        self._boton_limpiar.pack(side=tk.LEFT, padx=(8, 0))

        ttk.Separator(barra, orient=tk.VERTICAL).pack(
            side=tk.LEFT, fill=tk.Y, padx=12
        )

        self._boton_csv = ttk.Button(
            barra, text="Exportar tokens a CSV", command=self._exportar_csv
        )
        self._boton_csv.pack(side=tk.LEFT)

        self._boton_json = ttk.Button(
            barra, text="Exportar tokens a JSON", command=self._exportar_json
        )
        self._boton_json.pack(side=tk.LEFT, padx=(8, 0))

        self._etiqueta_archivo = ttk.Label(
            barra, text="Ningun archivo cargado", foreground="#5b6670"
        )
        self._etiqueta_archivo.pack(side=tk.RIGHT)

    def _construir_cuerpo(self) -> None:
        """Panel dividido: codigo fuente a la izquierda, resultados a la derecha."""
        panel = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        panel.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=(0, 8))

        marco_codigo = ttk.LabelFrame(panel, text="Codigo fuente", padding=6)
        panel.add(marco_codigo, weight=2)

        self._texto = tk.Text(
            marco_codigo, wrap=tk.NONE, font=FUENTE_CODIGO, undo=True
        )
        barra_v = ttk.Scrollbar(
            marco_codigo, orient=tk.VERTICAL, command=self._texto.yview
        )
        barra_h = ttk.Scrollbar(
            marco_codigo, orient=tk.HORIZONTAL, command=self._texto.xview
        )
        self._texto.configure(
            yscrollcommand=barra_v.set, xscrollcommand=barra_h.set
        )

        self._texto.grid(row=0, column=0, sticky="nsew")
        barra_v.grid(row=0, column=1, sticky="ns")
        barra_h.grid(row=1, column=0, sticky="ew")
        marco_codigo.rowconfigure(0, weight=1)
        marco_codigo.columnconfigure(0, weight=1)

        marco_resultados = ttk.Frame(panel)
        panel.add(marco_resultados, weight=3)

        self._pestanas = ttk.Notebook(marco_resultados)
        self._pestanas.pack(fill=tk.BOTH, expand=True)

        self._tabla_tokens = self._crear_pestana("Tokens", COLUMNAS_TOKENS)
        self._tabla_errores = self._crear_pestana("Errores lexicos", COLUMNAS_ERRORES)
        self._tabla_choques = self._crear_pestana("Choques de horario", COLUMNAS_CHOQUES)
        self._tabla_resumen = self._crear_pestana("Resumen", COLUMNAS_RESUMEN)

        self._tabla_errores.tag_configure("error", background="#fdeaea")
        self._tabla_choques.tag_configure("choque", background="#fdeaea")

    def _crear_pestana(self, titulo: str, columnas: tuple) -> ttk.Treeview:
        """Crea una pestana con una tabla y sus barras de desplazamiento.

        Args:
            titulo: Texto de la pestana.
            columnas: Tuplas (identificador, encabezado, ancho).

        Returns:
            El Treeview creado.
        """
        marco = ttk.Frame(self._pestanas, padding=4)
        self._pestanas.add(marco, text=titulo)

        identificadores = tuple(columna[0] for columna in columnas)
        tabla = ttk.Treeview(marco, columns=identificadores, show="headings")

        for identificador, encabezado, ancho in columnas:
            tabla.heading(identificador, text=encabezado)
            tabla.column(identificador, width=ancho, anchor=tk.W, stretch=True)

        barra_v = ttk.Scrollbar(marco, orient=tk.VERTICAL, command=tabla.yview)
        barra_h = ttk.Scrollbar(marco, orient=tk.HORIZONTAL, command=tabla.xview)
        tabla.configure(yscrollcommand=barra_v.set, xscrollcommand=barra_h.set)

        tabla.grid(row=0, column=0, sticky="nsew")
        barra_v.grid(row=0, column=1, sticky="ns")
        barra_h.grid(row=1, column=0, sticky="ew")
        marco.rowconfigure(0, weight=1)
        marco.columnconfigure(0, weight=1)

        return tabla

    def _construir_barra_reportes(self) -> None:
        """Barra con los botones que abren los reportes HTML."""
        barra = ttk.LabelFrame(self, text="Reportes HTML", padding=(10, 8))
        barra.pack(side=tk.TOP, fill=tk.X, padx=10, pady=(0, 8))

        self._botones_reporte = {}
        definiciones = (
            ("horario", "Reporte 1: Horario semanal"),
            ("catedraticos", "Reporte 2: Carga de catedraticos"),
            ("estadistico", "Reporte 3: Estadistico general"),
            ("errores", "Reporte de errores lexicos"),
        )
        for clave, texto in definiciones:
            boton = ttk.Button(
                barra, text=texto,
                command=lambda c=clave: self._abrir_reporte(c),
            )
            boton.pack(side=tk.LEFT, padx=(0, 8))
            self._botones_reporte[clave] = boton

    def _construir_barra_estado(self) -> None:
        """Barra inferior con el mensaje de estado y la autoria."""
        barra = ttk.Frame(self, padding=(10, 6))
        barra.pack(side=tk.BOTTOM, fill=tk.X)

        self._etiqueta_estado = ttk.Label(barra, text="Listo.")
        self._etiqueta_estado.pack(side=tk.LEFT)

        ttk.Label(barra, text=AUTOR, foreground="#5b6670").pack(side=tk.RIGHT)

    # ------------------------------------------------------------------
    # Acciones
    # ------------------------------------------------------------------

    def _estado(self, mensaje: str) -> None:
        """Actualiza el mensaje de la barra de estado."""
        self._etiqueta_estado.configure(text=mensaje)
        self.update_idletasks()

    def _actualizar_botones(self) -> None:
        """Habilita o deshabilita los botones segun el estado del analisis."""
        hay_analisis = len(self._tokens) > 0 or len(self._errores) > 0
        estado_export = tk.NORMAL if self._tokens else tk.DISABLED
        self._boton_csv.configure(state=estado_export)
        self._boton_json.configure(state=estado_export)

        for clave, boton in self._botones_reporte.items():
            disponible = hay_analisis and clave in self._rutas_reportes
            boton.configure(state=tk.NORMAL if disponible else tk.DISABLED)

    def _abrir_archivo(self) -> None:
        """Pide un archivo .hor al usuario y lo carga en el area de texto."""
        ruta = filedialog.askopenfilename(
            title="Seleccionar archivo HorarioScript",
            initialdir=os.path.join(self._directorio_proyecto, "entradas"),
            filetypes=[("Archivos HorarioScript", "*.hor"), ("Todos", "*.*")],
        )
        if not ruta:
            return

        try:
            contenido = CargadorArchivos.cargar(ruta)
        except ErrorDeCarga as error:
            messagebox.showerror("No se pudo abrir el archivo", str(error))
            self._estado("Error al cargar el archivo.")
            return

        self._ruta_actual = ruta
        self._texto.delete("1.0", tk.END)
        self._texto.insert("1.0", contenido)
        self._etiqueta_archivo.configure(text=os.path.basename(ruta))
        self._limpiar_resultados()
        self._estado(f"Archivo cargado: {ruta}")

    def _limpiar(self) -> None:
        """Vacia el area de texto y todos los resultados."""
        self._texto.delete("1.0", tk.END)
        self._ruta_actual = ""
        self._etiqueta_archivo.configure(text="Ningun archivo cargado")
        self._limpiar_resultados()
        self._estado("Listo.")

    def _limpiar_resultados(self) -> None:
        """Vacia las cuatro tablas y descarta el analisis anterior."""
        for tabla in (self._tabla_tokens, self._tabla_errores,
                      self._tabla_choques, self._tabla_resumen):
            for fila in tabla.get_children():
                tabla.delete(fila)
        self._tokens = []
        self._errores = []
        self._choques = []
        self._horario = None
        self._rutas_reportes = {}
        self._duracion_ms = 0.0
        self._actualizar_botones()

    def _analizar(self) -> None:
        """Ejecuta el flujo completo sobre el contenido del area de texto."""
        texto = self._texto.get("1.0", tk.END)
        if texto.strip() == "":
            messagebox.showwarning(
                "Nada que analizar", "Carga un archivo .hor o escribe contenido."
            )
            return

        self._limpiar_resultados()
        self._estado("Analizando...")

        inicio = time.perf_counter()
        gestor = GestorErrores()
        self._tokens = AnalizadorLexico(texto, gestor).analizar_todo()
        self._errores = gestor.errores

        self._horario = ConstructorHorario(self._tokens).construir()
        detector = DetectorChoques(self._horario)
        self._choques = detector.detectar()
        self._duracion_ms = (time.perf_counter() - inicio) * 1000

        self._llenar_tabla_tokens()
        self._llenar_tabla_errores()
        self._llenar_tabla_choques()
        self._llenar_resumen()
        self._generar_reportes(detector)
        self._actualizar_botones()

        self._estado(
            f"Analisis completo: {len(self._tokens)} tokens, "
            f"{len(self._errores)} errores, {len(self._choques)} choques "
            f"({self._duracion_ms:.2f} ms)."
        )

    def _generar_reportes(self, detector: DetectorChoques) -> None:
        """Genera los cuatro reportes HTML en la carpeta de salidas."""
        nombre = "sesion"
        if self._ruta_actual:
            base = os.path.basename(self._ruta_actual)
            nombre = base[: len(base) - 4] if base.lower().endswith(".hor") else base

        destino = os.path.join(self._directorio_proyecto, "salidas", nombre)
        try:
            generador = GeneradorReportes(destino)
            self._rutas_reportes = generador.generar_todos(
                self._horario, self._choques,
                detector.clases_en_choque(), self._errores,
            )
        except OSError as error:
            messagebox.showerror(
                "No se pudieron generar los reportes", str(error)
            )
            self._rutas_reportes = {}

    def _llenar_tabla_tokens(self) -> None:
        """Vuelca la lista de tokens en su tabla."""
        for token in self._tokens:
            self._tabla_tokens.insert("", tk.END, values=token.a_fila())

    def _llenar_tabla_errores(self) -> None:
        """Vuelca la lista de errores en su tabla."""
        for error in self._errores:
            self._tabla_errores.insert(
                "", tk.END, values=error.a_fila(), tags=("error",)
            )

    def _llenar_tabla_choques(self) -> None:
        """Vuelca la lista de choques en su tabla."""
        for choque in self._choques:
            self._tabla_choques.insert(
                "", tk.END, values=choque.a_fila(), tags=("choque",)
            )

    def _llenar_resumen(self) -> None:
        """Muestra las estadisticas del analisis y la frecuencia por tipo."""
        frecuencias: dict[str, int] = {}
        for token in self._tokens:
            clave = token.tipo.value
            frecuencias[clave] = frecuencias.get(clave, 0) + 1

        filas = [
            ("Archivo analizado",
             os.path.basename(self._ruta_actual) if self._ruta_actual else "(sin archivo)"),
            ("Tiempo de analisis", f"{self._duracion_ms:.2f} ms"),
            ("Tokens reconocidos", len(self._tokens)),
            ("Errores lexicos", len(self._errores)),
            ("Choques de horario", len(self._choques)),
        ]
        if self._horario is not None:
            filas.extend([
                ("Cursos declarados", len(self._horario.cursos)),
                ("Catedraticos declarados", len(self._horario.catedraticos)),
                ("Aulas declaradas", len(self._horario.aulas)),
                ("Clases programadas", len(self._horario.clases)),
            ])
        filas.append(("--- Frecuencia por tipo de token ---", ""))
        for tipo in sorted(frecuencias):
            filas.append((tipo, frecuencias[tipo]))

        for concepto, valor in filas:
            self._tabla_resumen.insert("", tk.END, values=(concepto, valor))

    def _abrir_reporte(self, clave: str) -> None:
        """Abre en el navegador el reporte HTML indicado."""
        ruta = self._rutas_reportes.get(clave)
        if not ruta or not os.path.exists(ruta):
            messagebox.showinfo(
                "Reporte no disponible",
                "Ejecuta el analisis para generar los reportes.",
            )
            return
        webbrowser.open(f"file:///{os.path.abspath(ruta)}")
        self._estado(f"Reporte abierto: {ruta}")

    def _ruta_de_exportacion(self, extension: str) -> str:
        """Pide al usuario donde guardar la exportacion de tokens."""
        return filedialog.asksaveasfilename(
            title="Guardar tabla de tokens",
            defaultextension=extension,
            initialdir=os.path.join(self._directorio_proyecto, "salidas"),
            initialfile=f"tokens{extension}",
            filetypes=[(f"Archivo {extension[1:].upper()}", f"*{extension}")],
        )

    def _exportar_csv(self) -> None:
        """Exporta la tabla de tokens a un archivo CSV."""
        ruta = self._ruta_de_exportacion(".csv")
        if not ruta:
            return
        try:
            with open(ruta, "w", encoding="utf-8", newline="") as archivo:
                escritor = csv.writer(archivo)
                escritor.writerow(["numero", "lexema", "tipo", "linea", "columna"])
                for token in self._tokens:
                    escritor.writerow(token.a_fila())
        except OSError as error:
            messagebox.showerror("No se pudo exportar", str(error))
            return
        self._estado(f"Tokens exportados a {ruta}")

    def _exportar_json(self) -> None:
        """Exporta la tabla de tokens a un archivo JSON."""
        ruta = self._ruta_de_exportacion(".json")
        if not ruta:
            return
        datos = [
            {
                "numero": token.numero,
                "lexema": token.lexema,
                "tipo": token.tipo.value,
                "linea": token.linea,
                "columna": token.columna,
            }
            for token in self._tokens
        ]
        try:
            with open(ruta, "w", encoding="utf-8") as archivo:
                json.dump(datos, archivo, ensure_ascii=False, indent=2)
        except OSError as error:
            messagebox.showerror("No se pudo exportar", str(error))
            return
        self._estado(f"Tokens exportados a {ruta}")
