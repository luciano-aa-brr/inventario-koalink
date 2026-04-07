from tkinter import messagebox
import customtkinter as ctk
import database

# Importar las nuevas utilidades
from config import Config
from utils import center_window, show_error, show_info
from constants import Constants
from exceptions import PDFGenerationError
from logger import logger


class HistorialModule(ctk.CTkFrame):
    """Frame del módulo de historial de préstamos.

    Muestra préstamos activos, permite editar información y exportar el reporte.
    """

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.ent_buscar_historial = None
        self.combo_filtro_cat_historial = None
        self.tabla_historial = None

    def clear(self):
        """Elimina los widgets actuales del historial."""
        for widget in self.winfo_children():
            widget.destroy()

    def show_historial(self):
        """Carga la vista de historial de préstamos activos."""
        self.clear()

        ctk.CTkLabel(self, text="📋 Control de Préstamos Activos", font=("Arial", 24, "bold"), text_color="#FFFA03").pack(pady=20)

        busqueda_frame = ctk.CTkFrame(self, fg_color="transparent")
        busqueda_frame.pack(fill="x", padx=30)

        self.ent_buscar_historial = ctk.CTkEntry(busqueda_frame, placeholder_text="Buscar por profesor, alumno o equipo...", width=300)
        self.ent_buscar_historial.pack(side="left", padx=5)
        self.ent_buscar_historial.bind("<KeyRelease>", lambda e: self.actualizar_tabla_historial())

        ctk.CTkLabel(busqueda_frame, text="Filtrar por Ítem:").pack(side="left", padx=(15, 5))

        try:
            opciones_filtro = ["Todos"] + list(database.CATEGORIAS_PREFIJOS.keys())
        except Exception:
            opciones_filtro = ["Todos", "Tablet", "Notebook", "PC", "Libro", "Material Didáctico", "Impresora", "Proyector"]

        self.combo_filtro_cat_historial = ctk.CTkComboBox(busqueda_frame, values=opciones_filtro, width=160, command=lambda e: self.actualizar_tabla_historial())
        self.combo_filtro_cat_historial.set("Todos")
        self.combo_filtro_cat_historial.pack(side="left", padx=5)

        ctk.CTkButton(busqueda_frame, text="📄 Exportar a PDF", fg_color="#e67e22", hover_color="#d35400", command=self.exportar_pdf_historial).pack(side="right", padx=5)

        self.tabla_historial = ctk.CTkScrollableFrame(self, fg_color="#1d1d1d", corner_radius=15)
        self.tabla_historial.pack(fill="both", expand=True, padx=30, pady=15)

        self.actualizar_tabla_historial()

    def editar_info_prestamo(self, id_prestamo, equipo, resp_actual, dest_actual, tipo_actual, cant, fecha):
        """Abre un modal para editar los datos del préstamo seleccionado."""
        dialogo = ctk.CTkToplevel(self)
        dialogo.title("Editar Préstamo Activo")
        center_window(dialogo, 450, 480)
        dialogo.grab_set()

        ctk.CTkLabel(dialogo, text="✏️ Editar Préstamo", font=("Arial", 18, "bold"), text_color="#f39c12").pack(pady=10)

        info_frame = ctk.CTkFrame(dialogo, fg_color="#2b2b2b", corner_radius=8)
        info_frame.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(info_frame, text=f"Artículo: {equipo} (x{cant})", font=("Arial", 12, "bold")).pack(pady=(5,0))
        ctk.CTkLabel(info_frame, text=f"Fecha Salida: {fecha[:16]}", font=("Arial", 11), text_color="#aaaaaa").pack(pady=(0,5))

        ctk.CTkLabel(dialogo, text="Tipo de Usuario:").pack(pady=(15, 0))
        combo_tipo = ctk.CTkComboBox(dialogo, values=["Estudiante", "Funcionario"], width=300)
        combo_tipo.set(tipo_actual)
        combo_tipo.pack(pady=5)

        ctk.CTkLabel(dialogo, text="Nombre del Responsable:").pack(pady=(10, 0))
        ent_resp = ctk.CTkEntry(dialogo, width=300)
        ent_resp.insert(0, resp_actual)
        ent_resp.pack(pady=5)

        ctk.CTkLabel(dialogo, text="Destino / Sala:").pack(pady=(10, 0))
        ent_dest = ctk.CTkEntry(dialogo, width=300)
        ent_dest.insert(0, dest_actual)
        ent_dest.pack(pady=5)

        def confirmar():
            n_tipo = combo_tipo.get()
            n_resp = ent_resp.get().strip()
            n_dest = ent_dest.get().strip()

            if not n_resp or not n_dest:
                messagebox.showwarning("Atención", "Responsable y Destino no pueden estar vacíos.")
                return

            exito, msj = database.actualizar_info_prestamo_db(id_prestamo, n_resp, n_dest, n_tipo)
            if exito:
                dialogo.destroy()
                self.actualizar_tabla_historial()
            else:
                messagebox.showerror("Error", msj)

        ctk.CTkButton(dialogo, text="💾 Guardar Cambios", fg_color="#27ae60", hover_color="#2ecc71", command=confirmar).pack(pady=20)

    def actualizar_tabla_historial(self):
        """Refresca la tabla del historial de préstamos activos."""
        for w in self.tabla_historial.winfo_children():
            w.destroy()

        termino = self.ent_buscar_historial.get().strip()
        categoria = self.combo_filtro_cat_historial.get()
        registros = database.obtener_historial_activos_db(termino, categoria)

        h_frame = ctk.CTkFrame(self.tabla_historial, fg_color="#333333")
        h_frame.pack(fill="x", pady=(0, 5))
        ctk.CTkLabel(h_frame, text="ARTÍCULO", width=200, font=("Arial", 11, "bold")).pack(side="left", padx=5, pady=5)
        ctk.CTkLabel(h_frame, text="RESPONSABLE", width=180, font=("Arial", 11, "bold")).pack(side="left", padx=5, pady=5)
        ctk.CTkLabel(h_frame, text="CANT.", width=50, font=("Arial", 11, "bold")).pack(side="left", padx=5, pady=5)
        ctk.CTkLabel(h_frame, text="FECHA SALIDA", width=150, font=("Arial", 11, "bold")).pack(side="left", padx=5, pady=5)
        ctk.CTkLabel(h_frame, text="ACCIONES", width=80, font=("Arial", 11, "bold")).pack(side="left", padx=5, pady=5)

        for idx, reg in enumerate(registros, start=1):
            nom, resp, dest, tipo, cant, fecha, cod, id_prestamo = reg
            color_fila = "#2b2b2b" if idx % 2 == 0 else "transparent"
            f = ctk.CTkFrame(self.tabla_historial, fg_color=color_fila, corner_radius=6)
            f.pack(fill="x", pady=2, padx=2)
            ctk.CTkLabel(f, text=nom, width=200, anchor="w", wraplength=180, bg_color=color_fila).pack(side="left", padx=5, pady=5)
            ctk.CTkLabel(f, text=f"{resp}\n(📍 {dest})", width=180, anchor="w", font=("Arial", 10), bg_color=color_fila).pack(side="left", padx=5, pady=5)
            ctk.CTkLabel(f, text=str(cant), width=50, text_color="#2ecc71", font=("Arial", 13, "bold"), bg_color=color_fila).pack(side="left", padx=5, pady=5)
            ctk.CTkLabel(f, text=fecha[:16], width=150, text_color="#888888", bg_color=color_fila).pack(side="left", padx=5, pady=5)
            btn_frame = ctk.CTkFrame(f, fg_color=color_fila, bg_color=color_fila)
            btn_frame.pack(side="left", padx=5, pady=5)
            ctk.CTkButton(btn_frame, text="✏️ Editar", width=70, fg_color="#f39c12", hover_color="#d35400", command=lambda i=id_prestamo, n=nom, r=resp, d=dest, t=tipo, c=cant, f_date=fecha: self.editar_info_prestamo(i, n, r, d, t, c, f_date)).pack(pady=2)

    def exportar_pdf_historial(self):
        """Genera un reporte PDF de los préstamos activos filtrados."""
        try:
            from fpdf import FPDF
            import webbrowser
            import os
            from datetime import datetime, timezone, timedelta
        except ImportError:
            messagebox.showerror("Error", "Falta la librería FPDF. Instálala con: pip install fpdf")
            return

        termino = self.ent_buscar_historial.get().strip()
        categoria = self.combo_filtro_cat_historial.get()
        registros = database.obtener_historial_activos_db(termino, categoria)

        if not registros:
            messagebox.showinfo("Sistema de Inventario Escolar", f"No hay préstamos activos para exportar en la categoría: {categoria}")
            return

        zona_chile = timezone(timedelta(hours=-3))
        hora_exacta = datetime.now(zona_chile)
        hora_local_str = hora_exacta.strftime("%d/%m/%Y %H:%M")
        hora_archivo = hora_exacta.strftime("%Y%m%d_%H%M")

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, "Reporte de Prestamos Activos", ln=True, align='C')
        pdf.set_font("Arial", '', 10)
        pdf.cell(0, 10, f"Generado el: {hora_local_str}", ln=True, align='C')

        if categoria != "Todos":
            pdf.set_font("Arial", 'I', 11)
            pdf.cell(0, 8, f"Filtro aplicado: {categoria}", ln=True, align='C')

        pdf.ln(5)
        pdf.set_font("Arial", 'B', 10)
        pdf.set_fill_color(200, 200, 200)
        pdf.cell(75, 10, "Articulo", border=1, fill=True)
        pdf.cell(60, 10, "Responsable", border=1, fill=True)
        pdf.cell(15, 10, "Cant.", border=1, align='C', fill=True)
        pdf.cell(40, 10, "Fecha Salida", border=1, align='C', fill=True)
        pdf.ln()

        pdf.set_font("Arial", '', 9)
        for reg in registros:
            nom, resp, dest, tipo, cant, fecha, cod, id_prestamo = reg
            nom_str = (nom[:35] + '..') if len(nom) > 35 else nom
            resp_str = (f"{resp} ({dest})"[:28] + '..') if len(f"{resp} ({dest})") > 28 else f"{resp} ({dest})"
            nom_str = nom_str.encode('latin-1', 'replace').decode('latin-1')
            resp_str = resp_str.encode('latin-1', 'replace').decode('latin-1')
            pdf.cell(75, 8, nom_str, border=1)
            pdf.cell(60, 8, resp_str, border=1)
            pdf.cell(15, 8, str(cant), border=1, align='C')
            pdf.cell(40, 8, fecha[:16], border=1, align='C')
            pdf.ln()

        nombre_archivo = f"Reporte_Prestamos_{hora_archivo}.pdf"
        try:
            pdf.output(nombre_archivo)
            webbrowser.open_new(os.path.abspath(nombre_archivo))
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar el PDF.\nDetalle: {e}")
