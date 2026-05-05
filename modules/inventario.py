import os
from tkinter import messagebox
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm
import barcode
from barcode.writer import ImageWriter
import customtkinter as ctk
import database

# Importar las nuevas utilidades
from config import Config
from utils import center_window, clean_temp_files, show_error, show_info
from constants import Constants
from exceptions import PDFGenerationError, BarcodeGenerationError
from logger import logger

LISTA_CATEGORIAS = list(Config.CATEGORIAS_PREFIJOS.keys())
LISTA_FILTROS = ["Todos"] + LISTA_CATEGORIAS


class InventarioModule(ctk.CTkFrame):
    """Frame del módulo de inventario.

    Contiene la vista principal de stock, la creación de nuevas entradas y los
    controles de baja / edición de artículos.
    """

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.pagina_actual = 1
        self.items_por_pagina = 50
        self.ver_inactivos_var = ctk.BooleanVar(value=False)
        self.filtro_cat = None
        self.entry_buscador = None
        self.paginacion_frame = None
        self.tabla_container = None

    def clear(self):
        """Elimina todos los widgets hijos del módulo."""
        for widget in self.winfo_children():
            widget.destroy()

    def show_inventario(self):
        """Muestra la vista de inventario con filtros, búsqueda y paginación."""
        self.clear()
        self.pagina_actual = 1
        self.items_por_pagina = 50

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 10))

        ctk.CTkLabel(header, text="Gestión de Inventario", font=("Arial", 24, "bold")).pack(side="left")

        self.ver_inactivos_var = ctk.BooleanVar(value=False)
        self.sw_inactivos = ctk.CTkSwitch(
            header,
            text="Ver Equipos de Baja (Inactivos)",
            variable=self.ver_inactivos_var,
            command=self.reset_y_actualizar_inventario,
        )
        self.sw_inactivos.pack(side="right", padx=20)

        self.filtro_cat = ctk.CTkComboBox(
            header,
            values=LISTA_FILTROS,
            command=lambda _: self.reset_y_actualizar_inventario(),
        )
        self.filtro_cat.set("Todos")
        self.filtro_cat.pack(side="right", padx=10)

        f_busqueda = ctk.CTkFrame(self, fg_color="transparent")
        f_busqueda.pack(fill="x", padx=20, pady=(0, 10))

        self.entry_buscador = ctk.CTkEntry(
            f_busqueda,
            placeholder_text="🔍 Buscar ítem por nombre...",
            width=300,
        )
        self.entry_buscador.pack(side="left")
        self.entry_buscador.bind(
            "<KeyRelease>",
            lambda e: self.controller.busqueda_inteligente(e, self.reset_y_actualizar_inventario),
        )

        self.paginacion_frame = ctk.CTkFrame(self, fg_color="transparent", height=40)
        self.paginacion_frame.pack(side="bottom", fill="x", pady=10)

        self.tabla_container = ctk.CTkScrollableFrame(self, fg_color="#1d1d1d")
        self.tabla_container.pack(fill="both", expand=True, padx=20, pady=10)

        self.actualizar_tabla_inventario()

    def reset_y_actualizar_inventario(self, *args):
        """Reinicia la página y actualiza la tabla cuando cambia un filtro o búsqueda."""
        self.pagina_actual = 1
        self.actualizar_tabla_inventario()

    def pagina_anterior_inv(self):
        if self.pagina_actual > 1:
            self.pagina_actual -= 1
            self.actualizar_tabla_inventario()

    def pagina_siguiente_inv(self, total_paginas):
        if self.pagina_actual < total_paginas:
            self.pagina_actual += 1
            self.actualizar_tabla_inventario()

    def dibujar_controles_paginacion(self, total_paginas):
        """Dibuja los controles de paginación en la parte inferior de la vista."""
        for w in self.paginacion_frame.winfo_children():
            w.destroy()

        if total_paginas <= 1:
            return

        btn_prev = ctk.CTkButton(
            self.paginacion_frame,
            text="< Anterior",
            width=100,
            fg_color="#34495e",
            hover_color="#2c3e50",
            state="normal" if self.pagina_actual > 1 else "disabled",
            command=self.pagina_anterior_inv,
        )
        btn_prev.pack(side="left", padx=20)

        lbl_pag = ctk.CTkLabel(
            self.paginacion_frame,
            text=f"Página {self.pagina_actual} de {total_paginas}",
            font=("Arial", 14, "bold"),
        )
        lbl_pag.pack(side="left", expand=True)

        btn_next = ctk.CTkButton(
            self.paginacion_frame,
            text="Siguiente >",
            width=100,
            fg_color="#34495e",
            hover_color="#2c3e50",
            state="normal" if self.pagina_actual < total_paginas else "disabled",
            command=lambda: self.pagina_siguiente_inv(total_paginas),
        )
        btn_next.pack(side="right", padx=20)

    def generar_pdf_etiquetas(self):
        """Genera un PDF con etiquetas de los artículos en inventario."""
        try:
            logger.info("Iniciando generación de etiquetas PDF")
            items = database.obtener_articulos_inventario_completo("Todos")
            if not items:
                show_info(Config.WINDOW_TITLE, "No hay artículos en el inventario.")
                return

            nombre_pdf = Config.ETIQUETAS_PDF_NAME
            c = canvas.Canvas(nombre_pdf, pagesize=letter)
            ancho_pagina, alto_pagina = letter

            ancho_etiqueta = Config.PDF_LABEL_WIDTH_MM * mm
            alto_etiqueta = Config.PDF_LABEL_HEIGHT_MM * mm
            margen_x = Config.PDF_MARGIN_MM * mm
            margen_y = Config.PDF_MARGIN_MM * mm
            espacio_entre_columnas = 5 * mm
            espacio_entre_filas = 5 * mm

            x_actual = margen_x
            y_actual = alto_pagina - margen_y - alto_etiqueta
            columna_actual = 0

            if not os.path.exists("temp_barcodes"):
                os.makedirs("temp_barcodes")

            nombre_pdf = os.path.abspath(Config.ETIQUETAS_PDF_NAME)
            for it in items:
                cod, nom, cat, est, ubi, cant, resp, dest, fecha = it
                try:
                    COD = barcode.get_barcode_class(Config.BARCODE_TYPE)
                    mi_barcode = COD(cod, writer=ImageWriter())
                    ruta_img = os.path.join("temp_barcodes", cod)
                    mi_barcode.save(ruta_img, options={"write_text": Config.BARCODE_TEXT, "module_height": Config.BARCODE_MODULE_HEIGHT})
                    ruta_full = f"{ruta_img}.png"

                    c.setStrokeColorRGB(0.8, 0.8, 0.8)
                    c.rect(x_actual, y_actual, ancho_etiqueta, alto_etiqueta)

                    c.setFillColorRGB(0, 0, 0)
                    c.setFont("Helvetica-Bold", 8)
                    c.drawCentredString(x_actual + ancho_etiqueta / 2, y_actual + alto_etiqueta - 10, f"{nom[:25]}")
                    c.drawImage(ruta_full, x_actual + 5 * mm, y_actual + 10, width=ancho_etiqueta - 10 * mm, height=alto_etiqueta - 18 * mm, mask="auto")
                    c.setFont("Helvetica", 7)
                    c.drawCentredString(x_actual + ancho_etiqueta / 2, y_actual + 3, f"ID: {cod}")

                    columna_actual += 1
                    if columna_actual < Config.PDF_LABELS_PER_ROW:
                        x_actual += ancho_etiqueta + espacio_entre_columnas
                    else:
                        columna_actual = 0
                        x_actual = margen_x
                        y_actual -= alto_etiqueta + espacio_entre_filas

                    if y_actual < margen_y:
                        c.showPage()
                        y_actual = alto_pagina - margen_y - alto_etiqueta
                        x_actual = margen_x

                except Exception as e:
                    logger.error(f"Error generando código de barras para {cod}: {e}")
                    raise BarcodeGenerationError(f"Error generando código de barras para {cod}")

            c.save()
            clean_temp_files("temp_barcodes")

            # Abrir el PDF automáticamente
            try:
                os.startfile(nombre_pdf)
                show_info(Config.WINDOW_TITLE, f"PDF generado correctamente: {nombre_pdf}")
                logger.info(f"PDF de etiquetas generado exitosamente: {nombre_pdf}")
            except Exception as e:
                logger.warning(f"No se pudo abrir automáticamente el PDF: {e}")
                show_info(Config.WINDOW_TITLE, f"PDF generado correctamente: {nombre_pdf}")

        except BarcodeGenerationError as e:
            logger.error(f"Error de código de barras: {e}")
            show_error(Config.WINDOW_TITLE, str(e))
        except Exception as e:
            logger.error(f"Error generando PDF de etiquetas: {e}")
            show_error(Config.WINDOW_TITLE, f"No se pudo generar PDF de etiquetas: {e}")

    def actualizar_tabla_inventario(self):
        """Dibuja la tabla de inventario actualizada con filtros y acciones."""
        try:
            for w in self.tabla_container.winfo_children():
                w.destroy()

            categoria = self.filtro_cat.get() if self.filtro_cat else "Todos"
            ver_de_baja = self.ver_inactivos_var.get()
            texto_busqueda = self.entry_buscador.get() if self.entry_buscador else ""

            h_frame = ctk.CTkFrame(self.tabla_container, fg_color="#333333")
            h_frame.pack(fill="x", pady=(0, 5))

            if ver_de_baja:
                ctk.CTkLabel(h_frame, text="FECHA BAJA", width=90, anchor="w", font=("Arial", 11, "bold")).pack(side="left", padx=5, pady=5)
                ctk.CTkLabel(h_frame, text="CÓDIGO", width=70, anchor="w", font=("Arial", 11, "bold")).pack(side="left", padx=5, pady=5)
                ctk.CTkLabel(h_frame, text="NOMBRE", width=180, anchor="w", font=("Arial", 11, "bold")).pack(side="left", padx=5, pady=5)
                ctk.CTkLabel(h_frame, text="MOTIVO Y RESPONSABLE", width=250, anchor="w", font=("Arial", 11, "bold")).pack(side="left", padx=5, pady=5)
                ctk.CTkLabel(h_frame, text="CANT.", width=50, font=("Arial", 11, "bold")).pack(side="left", padx=5, pady=5)
                ctk.CTkLabel(h_frame, text="ACCIONES", width=90, font=("Arial", 11, "bold")).pack(side="left", padx=5, pady=5)
            else:
                ctk.CTkLabel(h_frame, text="CÓDIGO", width=80, anchor="w", font=("Arial", 11, "bold")).pack(side="left", padx=5, pady=5)
                ctk.CTkLabel(h_frame, text="NOMBRE", width=200, anchor="w", font=("Arial", 11, "bold")).pack(side="left", padx=5, pady=5)
                ctk.CTkLabel(h_frame, text="UBICACIÓN", width=120, anchor="w", font=("Arial", 11, "bold")).pack(side="left", padx=5, pady=5)
                ctk.CTkLabel(h_frame, text="TOTAL", width=70, font=("Arial", 11, "bold")).pack(side="left", padx=5, pady=5)
                ctk.CTkLabel(h_frame, text="PRÉSTAMO", width=80, font=("Arial", 11, "bold")).pack(side="left", padx=5, pady=5)
                ctk.CTkLabel(h_frame, text="DISPONIBLE", width=80, font=("Arial", 11, "bold")).pack(side="left", padx=5, pady=5)
                ctk.CTkLabel(h_frame, text="ACCIONES", width=80, font=("Arial", 11, "bold")).pack(side="left", padx=5, pady=5)

            offset = (self.pagina_actual - 1) * self.items_por_pagina
            if ver_de_baja:
                total_items = database.contar_articulos_inactivos()
                items = database.obtener_articulos_inactivos_reporte(self.items_por_pagina, offset)
            else:
                total_items = database.contar_articulos_con_stock(texto_busqueda, categoria)
                items = database.obtener_articulos_con_stock(texto_busqueda, categoria, self.items_por_pagina, offset)

            total_paginas = max(1, (total_items + self.items_por_pagina - 1) // self.items_por_pagina)
            self.dibujar_controles_paginacion(total_paginas)

            for idx, it in enumerate(items, start=1):
                color_fila = "#2b2b2b" if idx % 2 == 0 else "transparent"
                f = ctk.CTkFrame(self.tabla_container, fg_color=color_fila, corner_radius=4)
                f.pack(fill="x", pady=1, padx=2)

                if ver_de_baja:
                    cod, nom, motivo_y_responsable, cant, fecha = it
                    fecha_corta = fecha[:10] if fecha else "N/A"
                    ctk.CTkLabel(f, text=fecha_corta, width=90, anchor="w", bg_color=color_fila).pack(side="left", padx=5, pady=2)
                    ctk.CTkLabel(f, text=cod, width=70, anchor="w", bg_color=color_fila).pack(side="left", padx=5, pady=2)
                    ctk.CTkLabel(f, text=nom, width=180, anchor="w", wraplength=170, bg_color=color_fila).pack(side="left", padx=5, pady=2)
                    ctk.CTkLabel(f, text=motivo_y_responsable, width=250, anchor="w", text_color="#e74c3c", wraplength=240, bg_color=color_fila).pack(side="left", padx=5, pady=2)
                    ctk.CTkLabel(f, text=str(cant), width=50, font=("Arial", 13, "bold"), bg_color=color_fila).pack(side="left", padx=5, pady=2)
                    btn_frame = ctk.CTkFrame(f, fg_color=color_fila, bg_color=color_fila)
                    btn_frame.pack(side="left", padx=5, pady=2)
                    ctk.CTkButton(
                        btn_frame,
                        text="🔄 Reactivar",
                        width=80,
                        height=24,
                        fg_color="#9b59b6",
                        hover_color="#8e44ad",
                        command=lambda c=cod, n=nom, s=cant: self.reactivar_equipo(c, n, s),
                    ).pack(pady=2)
                else:
                    cod, nom, ubi, stock_tot, prestados, disponibles = it
                    ctk.CTkLabel(f, text=cod, width=80, anchor="w", bg_color=color_fila).pack(side="left", padx=5, pady=2)
                    ctk.CTkLabel(f, text=nom, width=200, anchor="w", wraplength=190, bg_color=color_fila).pack(side="left", padx=5, pady=2)
                    ctk.CTkLabel(f, text=ubi, width=120, anchor="w", bg_color=color_fila).pack(side="left", padx=5, pady=2)
                    ctk.CTkLabel(f, text=str(stock_tot), width=70, font=("Arial", 13, "bold"), bg_color=color_fila).pack(side="left", padx=5, pady=2)
                    color_prestamo = "#e67e22" if prestados > 0 else "white"
                    ctk.CTkLabel(f, text=str(prestados), width=80, text_color=color_prestamo, font=("Arial", 13, "bold"), bg_color=color_fila).pack(side="left", padx=5, pady=2)
                    color_disp = "#2ecc71" if disponibles > 0 else "#e74c3c"
                    ctk.CTkLabel(f, text=str(disponibles), width=80, text_color=color_disp, font=("Arial", 13, "bold"), bg_color=color_fila).pack(side="left", padx=5, pady=2)
                    btn_frame = ctk.CTkFrame(f, fg_color=color_fila, bg_color=color_fila)
                    btn_frame.pack(side="left", padx=5, pady=2)
                    ctk.CTkButton(
                        btn_frame,
                        text="✎",
                        width=30,
                        height=24,
                        fg_color="#3498db",
                        hover_color="#2980b9",
                        command=lambda a=it: self.abrir_ventana_edicion(a),
                    ).pack(side="left", padx=2)
                    ctk.CTkButton(
                        btn_frame,
                        text="🗑",
                        width=30,
                        height=24,
                        fg_color="#e74c3c",
                        hover_color="#c0392b",
                        command=lambda c=cod, n=nom, s=stock_tot: self.dar_de_baja(c, n, s),
                    ).pack(side="left", padx=2)
        except Exception as e:
            print(f"Error en actualizar_tabla_inventario: {e}")

    def reactivar_equipo(self, codigo, nombre, stock_inactivo):
        dialogo = ctk.CTkInputDialog(
            text=f"¿Cuántas unidades de '{nombre}' desea reactivar?\n(En baja: {stock_inactivo})",
            title="Reactivar",
        )
        entrada = dialogo.get_input()
        if not entrada:
            return

        try:
            cantidad = int(entrada)
            if cantidad > stock_inactivo:
                messagebox.showwarning("Sistema de Inventario Escolar", f"Solo puedes reactivar hasta {stock_inactivo} unidades.")
                return

            exito, msj = database.reactivar_item_db(codigo, cantidad)
            if exito:
                messagebox.showinfo("Éxito", msj)
                self.actualizar_tabla_inventario()
            else:
                messagebox.showerror("Error", msj)
        except ValueError:
            messagebox.showerror("Error", "Ingrese un número válido.")

    def dar_de_baja(self, codigo, nombre, stock_actual):
        dialogo = ctk.CTkToplevel(self)
        dialogo.title("Reporte Técnico de Baja")
        center_window(dialogo, 450, 450)
        dialogo.grab_set()

        ctk.CTkLabel(dialogo, text="⚠️ Dar de Baja Equipo", font=("Arial", 18, "bold"), text_color="#e74c3c").pack(pady=10)
        ctk.CTkLabel(dialogo, text=f"{nombre}\n(ID: {codigo})", font=("Arial", 12)).pack(pady=5)

        ctk.CTkLabel(dialogo, text="Cantidad a dar de baja:").pack(pady=(10, 0))
        ent_cant = ctk.CTkEntry(dialogo, width=300)
        ent_cant.insert(0, "1")
        ent_cant.pack(pady=5)

        ctk.CTkLabel(dialogo, text="Diagnóstico / Motivo Principal:").pack(pady=(5, 0))
        combo_motivo = ctk.CTkComboBox(
            dialogo,
            values=["Pantalla Rota", "No Enciende", "Extraviado por Usuario", "Obsoleto", "Páginas rotas/rayadas", "Otro (Especificar)"],
            width=300,
        )
        combo_motivo.pack(pady=5)

        ctk.CTkLabel(dialogo, text="Observaciones del Técnico:").pack(pady=(5, 0))
        ent_detalle = ctk.CTkEntry(dialogo, placeholder_text="Ej: Teclas faltantes, lomo despegado...", width=300)
        ent_detalle.pack(pady=5)

        ctk.CTkLabel(dialogo, text="Responsable del Daño (Opcional):").pack(pady=(5, 0))
        ent_responsable = ctk.CTkEntry(dialogo, placeholder_text="Nombre (Dejar en blanco si fue en bodega)", width=300)
        ent_responsable.pack(pady=5)

        def confirmar():
            cant = ent_cant.get()
            motivo_base = combo_motivo.get()
            detalle = ent_detalle.get().strip()
            responsable = ent_responsable.get().strip()
            motivo_final = motivo_base
            if detalle:
                motivo_final += f" - {detalle}"
            if responsable:
                motivo_final += f" | Culpable: {responsable}"
            else:
                motivo_final += " | Daño en Bodega"

            if not cant.isdigit() or int(cant) <= 0 or int(cant) > stock_actual:
                messagebox.showerror("Error", "Cantidad inválida o superior al stock disponible.")
                return

            exito, msj = database.dar_de_baja_db(codigo, int(cant), motivo_final)
            if exito:
                dialogo.destroy()
                self.actualizar_tabla_inventario()
            else:
                messagebox.showerror("Error", msj)

        ctk.CTkButton(dialogo, text="Confirmar Baja Definitiva", fg_color="#e74c3c", hover_color="#c0392b", command=confirmar).pack(pady=15)

    def abrir_ventana_edicion(self, item):
        modal = ctk.CTkToplevel(self)
        modal.title(f"Editando: {item[0]}")
        center_window(modal, 400, 450)
        modal.attributes("-topmost", True)
        modal.grab_set()

        ctk.CTkLabel(modal, text="Modificar Información", font=("Arial", 18, "bold"), text_color="#FFFA03").pack(pady=20)

        ctk.CTkLabel(modal, text="Nombre / Modelo:").pack(pady=(10, 0))
        ent_nom = ctk.CTkEntry(modal, width=300)
        ent_nom.insert(0, item[1])
        ent_nom.pack(pady=5)

        ctk.CTkLabel(modal, text="Categoría:").pack(pady=(10, 0))
        cb_cat = ctk.CTkComboBox(modal, values=["Tablet", "Notebook", "Libro", "Material Didáctico", "Impresora"], width=300)
        cb_cat.set(item[2])
        cb_cat.pack(pady=5)

        ctk.CTkLabel(modal, text="Ubicación Base:").pack(pady=(10, 0))
        ent_ubi = ctk.CTkEntry(modal, width=300)
        ent_ubi.insert(0, item[4])
        ent_ubi.pack(pady=5)

        ctk.CTkLabel(modal, text="Stock Total:").pack(pady=(10, 0))
        ent_cant = ctk.CTkEntry(modal, width=300)
        ent_cant.insert(0, str(item[5]))
        ent_cant.pack(pady=5)

        def confirmar_cambios():
            try:
                nueva_cant = int(ent_cant.get())
                if database.actualizar_articulo_db(item[0], ent_nom.get(), cb_cat.get(), ent_ubi.get(), nueva_cant):
                    messagebox.showinfo("Éxito", "Datos actualizados correctamente.")
                    modal.destroy()
                    self.actualizar_tabla_inventario()
                else:
                    messagebox.showerror("Error", "No se pudo actualizar la base de datos.")
            except ValueError:
                messagebox.showerror("Error", "La cantidad debe ser un número válido.")

        ctk.CTkButton(modal, text="💾 GUARDAR CAMBIOS", fg_color="#27ae60", command=confirmar_cambios).pack(pady=30)

    def show_alta_equipo(self):
        """Muestra el formulario de alta de nuevo artículo y usa la lógica del módulo."""
        self.clear()

        ctk.CTkLabel(self, text="Registro de Inventario", font=("Arial", 26, "bold"), text_color="#FFFA03").pack(pady=(30, 20))

        form_frame = ctk.CTkFrame(self, fg_color="transparent")
        form_frame.pack(pady=10, padx=50)

        try:
            opciones_cat = list(database.CATEGORIAS_PREFIJOS.keys())
        except Exception:
            opciones_cat = ["Tablet", "Notebook", "PC", "Libro", "Material Didáctico", "Impresora", "Proyector"]

        def al_cambiar_categoria(seleccion):
            siguiente_cod = database.generar_siguiente_codigo(seleccion)
            ent_cod.delete(0, "end")
            ent_cod.insert(0, siguiente_cod)

            if seleccion in ["Tablet", "Notebook", "PC", "Impresora", "Proyector"]:
                ent_cant.configure(state="normal")
                ent_cant.delete(0, "end")
                ent_cant.insert(0, "1")
                ent_cant.configure(state="disabled")
            else:
                ent_cant.configure(state="normal")

        ctk.CTkLabel(form_frame, text="Categoría:").grid(row=0, column=0, padx=20, pady=15, sticky="e")
        combo_cat = ctk.CTkComboBox(form_frame, values=opciones_cat, command=al_cambiar_categoria, width=350)
        combo_cat.grid(row=0, column=1)

        ctk.CTkLabel(form_frame, text="Código:").grid(row=1, column=0, padx=20, pady=15, sticky="e")
        ent_cod = ctk.CTkEntry(form_frame, width=350)
        ent_cod.grid(row=1, column=1)

        ctk.CTkLabel(form_frame, text="Nombre:").grid(row=2, column=0, padx=20, pady=15, sticky="e")
        ent_nom = ctk.CTkEntry(form_frame, width=350)
        ent_nom.grid(row=2, column=1)

        ctk.CTkLabel(form_frame, text="Estante / Detalle:").grid(row=3, column=0, padx=20, pady=15, sticky="e")
        ent_estante = ctk.CTkEntry(form_frame, placeholder_text="Ej: Estante 1-1.1", width=350)
        ent_estante.grid(row=3, column=1)

        ctk.CTkLabel(form_frame, text="Stock:").grid(row=4, column=0, padx=20, pady=15, sticky="e")
        ent_cant = ctk.CTkEntry(form_frame, width=350)
        ent_cant.insert(0, "1")
        ent_cant.grid(row=4, column=1)

        def guardar():
            detalle = ent_estante.get().strip()
            ubicacion_final = f"Bodega ({detalle})" if detalle else "Bodega"
            exito, mensaje = database.guardar_item_db(ent_cod.get(), ent_nom.get(), combo_cat.get(), ubicacion_final, int(ent_cant.get()))
            if exito:
                messagebox.showinfo("Éxito", mensaje)
                self.show_alta_equipo()
            else:
                messagebox.showerror("Error", mensaje)

        ctk.CTkButton(self, text="📥 REGISTRAR", command=guardar, fg_color="#27ae60").pack(pady=40)

        if opciones_cat:
            combo_cat.set(opciones_cat[0])
            al_cambiar_categoria(opciones_cat[0])

    def show_libros(self):
        """Muestra la vista de gestión de libros con copias individuales."""
        self.clear()
        
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 10))
        
        ctk.CTkLabel(header, text="📚 Gestión de Libros (Copias Individuales)", font=("Arial", 24, "bold")).pack(side="left")
        
        f_busqueda = ctk.CTkFrame(self, fg_color="transparent")
        f_busqueda.pack(fill="x", padx=20, pady=(0, 10))
        
        ent_busqueda = ctk.CTkEntry(f_busqueda, placeholder_text="🔍 Buscar por título, código o autor...", width=400)
        ent_busqueda.pack(side="left", padx=5)
        
        btn_agregar = ctk.CTkButton(f_busqueda, text="➕ Agregar Nuevo Libro", fg_color="#27ae60", command=self.show_alta_libro, width=150)
        btn_agregar.pack(side="right", padx=5)
        
        tabla_frame = ctk.CTkScrollableFrame(self, fg_color="#1d1d1d")
        tabla_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        def actualizar_tabla_libros(busqueda=""):
            for w in tabla_frame.winfo_children():
                w.destroy()
            
            libros = database.obtener_libros_db(busqueda)
            
            if not libros:
                ctk.CTkLabel(tabla_frame, text="No hay libros registrados", text_color="#888888").pack(pady=20)
                return
            
            # Encabezado
            h_frame = ctk.CTkFrame(tabla_frame, fg_color="#333333")
            h_frame.pack(fill="x", pady=(0, 5))
            
            ctk.CTkLabel(h_frame, text="CÓDIGO", width=80, anchor="w", font=("Arial", 11, "bold")).pack(side="left", padx=5, pady=5)
            ctk.CTkLabel(h_frame, text="TÍTULO", width=220, anchor="w", font=("Arial", 11, "bold")).pack(side="left", padx=5, pady=5)
            ctk.CTkLabel(h_frame, text="AUTOR", width=150, anchor="w", font=("Arial", 11, "bold")).pack(side="left", padx=5, pady=5)
            ctk.CTkLabel(h_frame, text="TOTAL", width=60, font=("Arial", 11, "bold")).pack(side="left", padx=5, pady=5)
            ctk.CTkLabel(h_frame, text="DISPONIBLES", width=80, font=("Arial", 11, "bold")).pack(side="left", padx=5, pady=5)
            ctk.CTkLabel(h_frame, text="PRESTADAS", width=80, font=("Arial", 11, "bold")).pack(side="left", padx=5, pady=5)
            ctk.CTkLabel(h_frame, text="ACCIONES", width=100, font=("Arial", 11, "bold")).pack(side="left", padx=5, pady=5)
            
            for idx, libro in enumerate(libros, start=1):
                cod_libro, nombre, autor, total_copias, disponibles, prestadas = libro
                
                color_fila = "#2b2b2b" if idx % 2 == 0 else "transparent"
                f = ctk.CTkFrame(tabla_frame, fg_color=color_fila, corner_radius=4)
                f.pack(fill="x", pady=1, padx=2)
                
                ctk.CTkLabel(f, text=cod_libro, width=80, anchor="w", bg_color=color_fila).pack(side="left", padx=5, pady=2)
                ctk.CTkLabel(f, text=nombre[:30], width=220, anchor="w", wraplength=210, bg_color=color_fila).pack(side="left", padx=5, pady=2)
                ctk.CTkLabel(f, text=autor[:20] if autor else "N/A", width=150, anchor="w", wraplength=140, bg_color=color_fila).pack(side="left", padx=5, pady=2)
                ctk.CTkLabel(f, text=str(total_copias or 0), width=60, font=("Arial", 12, "bold"), bg_color=color_fila).pack(side="left", padx=5, pady=2)
                
                color_disp = "#2ecc71" if (disponibles or 0) > 0 else "#e74c3c"
                ctk.CTkLabel(f, text=str(disponibles or 0), width=80, text_color=color_disp, font=("Arial", 12, "bold"), bg_color=color_fila).pack(side="left", padx=5, pady=2)
                
                color_prest = "#e67e22" if (prestadas or 0) > 0 else "white"
                ctk.CTkLabel(f, text=str(prestadas or 0), width=80, text_color=color_prest, font=("Arial", 12, "bold"), bg_color=color_fila).pack(side="left", padx=5, pady=2)
                
                btn_frame = ctk.CTkFrame(f, fg_color=color_fila, bg_color=color_fila)
                btn_frame.pack(side="left", padx=5, pady=2)
                
                ctk.CTkButton(
                    btn_frame,
                    text="📖",
                    width=30,
                    height=24,
                    fg_color="#3498db",
                    hover_color="#2980b9",
                    command=lambda c=cod_libro, n=nombre: self.ver_copias_libro(c, n)
                ).pack(side="left", padx=2)
                
                ctk.CTkButton(
                    btn_frame,
                    text="➕",
                    width=30,
                    height=24,
                    fg_color="#27ae60",
                    hover_color="#229954",
                    command=lambda c=cod_libro, n=nombre: self.agregar_copias_libro(c, n)
                ).pack(side="left", padx=2)
        
        def al_escribir_busqueda(*args):
            actualizar_tabla_libros(ent_busqueda.get())
        
        ent_busqueda.bind("<KeyRelease>", al_escribir_busqueda)
        actualizar_tabla_libros()
    
    def ver_copias_libro(self, codigo_libro, nombre_libro):
        """Muestra un modal con todas las copias de un libro."""
        modal = ctk.CTkToplevel(self)
        modal.title(f"Copias de: {nombre_libro}")
        center_window(modal, 900, 500)
        modal.grab_set()
        
        ctk.CTkLabel(modal, text=f"📚 Copias de '{nombre_libro}'", font=("Arial", 18, "bold"), text_color="#f1c40f").pack(pady=10)
        
        tabla = ctk.CTkScrollableFrame(modal, fg_color="#1d1d1d")
        tabla.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Encabezado
        h_frame = ctk.CTkFrame(tabla, fg_color="#333333")
        h_frame.pack(fill="x", pady=(0, 5))
        
        ctk.CTkLabel(h_frame, text="NÚMERO DE SERIE", width=150, anchor="w", font=("Arial", 11, "bold")).pack(side="left", padx=5, pady=5)
        ctk.CTkLabel(h_frame, text="ESTADO", width=100, anchor="w", font=("Arial", 11, "bold")).pack(side="left", padx=5, pady=5)
        ctk.CTkLabel(h_frame, text="RESPONSABLE", width=200, anchor="w", font=("Arial", 11, "bold")).pack(side="left", padx=5, pady=5)
        ctk.CTkLabel(h_frame, text="FECHA PRÉSTAMO", width=150, anchor="w", font=("Arial", 11, "bold")).pack(side="left", padx=5, pady=5)
        
        copias = database.obtener_copias_libro_db(codigo_libro)
        
        if not copias:
            ctk.CTkLabel(tabla, text="No hay copias registradas", text_color="#888888").pack(pady=20)
        else:
            for idx, copia in enumerate(copias, start=1):
                numero_serie, estado, responsable, fecha_prestamo = copia
                
                color_fila = "#2b2b2b" if idx % 2 == 0 else "transparent"
                f = ctk.CTkFrame(tabla, fg_color=color_fila, corner_radius=4)
                f.pack(fill="x", pady=1, padx=2)
                
                color_estado = "#2ecc71" if estado == "Disponible" else "#e67e22"
                ctk.CTkLabel(f, text=numero_serie, width=150, anchor="w", text_color="#3498db", font=("Arial", 11, "bold"), bg_color=color_fila).pack(side="left", padx=5, pady=2)
                ctk.CTkLabel(f, text=estado, width=100, anchor="w", text_color=color_estado, font=("Arial", 11, "bold"), bg_color=color_fila).pack(side="left", padx=5, pady=2)
                ctk.CTkLabel(f, text=responsable, width=200, anchor="w", bg_color=color_fila).pack(side="left", padx=5, pady=2)
                ctk.CTkLabel(f, text=str(fecha_prestamo)[:10] if fecha_prestamo != "N/A" else "N/A", width=150, anchor="w", bg_color=color_fila).pack(side="left", padx=5, pady=2)
    
    def agregar_copias_libro(self, codigo_libro, nombre_libro):
        """Abre un diálogo para agregar más copias a un libro."""
        dialogo = ctk.CTkInputDialog(
            text=f"¿Cuántas copias adicionales desea agregar a '{nombre_libro}'?",
            title="Agregar Copias"
        )
        cantidad = dialogo.get_input()
        
        if not cantidad:
            return
        
        try:
            cantidad = int(cantidad)
            if cantidad <= 0:
                messagebox.showerror("Error", "La cantidad debe ser mayor que 0.")
                return
            
            exito, mensaje, nuevas_copias = database.agregar_copias_libro_db(codigo_libro, cantidad)
            if exito:
                messagebox.showinfo("Éxito", f"{mensaje}\n\nNuevos números de serie:\n{', '.join(nuevas_copias)}")
                self.show_libros()
            else:
                messagebox.showerror("Error", mensaje)
        except ValueError:
            messagebox.showerror("Error", "Ingrese un número válido.")
    
    def show_alta_libro(self):
        """Muestra el formulario para registrar un nuevo libro."""
        self.clear()
        
        ctk.CTkLabel(self, text="📖 Registrar Nuevo Libro", font=("Arial", 26, "bold"), text_color="#f1c40f").pack(pady=(30, 20))
        
        form_frame = ctk.CTkFrame(self, fg_color="transparent")
        form_frame.pack(pady=10, padx=50)
        
        # Código
        ctk.CTkLabel(form_frame, text="Código del Libro:").grid(row=0, column=0, padx=20, pady=15, sticky="e")
        ent_cod = ctk.CTkEntry(form_frame, width=350)
        cod_autogenerado = database.generar_codigo_libro("Libro")
        ent_cod.insert(0, cod_autogenerado)
        ent_cod.grid(row=0, column=1)
        
        # Título
        ctk.CTkLabel(form_frame, text="Título del Libro:").grid(row=1, column=0, padx=20, pady=15, sticky="e")
        ent_titulo = ctk.CTkEntry(form_frame, width=350)
        ent_titulo.grid(row=1, column=1)
        
        # Autor
        ctk.CTkLabel(form_frame, text="Autor:").grid(row=2, column=0, padx=20, pady=15, sticky="e")
        ent_autor = ctk.CTkEntry(form_frame, width=350)
        ent_autor.grid(row=2, column=1)
        
        # Ubicación
        ctk.CTkLabel(form_frame, text="Estante / Ubicación:").grid(row=3, column=0, padx=20, pady=15, sticky="e")
        ent_ubicacion = ctk.CTkEntry(form_frame, placeholder_text="Ej: Estante A-1", width=350)
        ent_ubicacion.grid(row=3, column=1)
        
        # Cantidad de copias
        ctk.CTkLabel(form_frame, text="Cantidad de Copias:").grid(row=4, column=0, padx=20, pady=15, sticky="e")
        ent_cantidad = ctk.CTkEntry(form_frame, width=350)
        ent_cantidad.insert(0, "1")
        ent_cantidad.grid(row=4, column=1)
        
        def guardar():
            codigo = ent_cod.get().strip()
            titulo = ent_titulo.get().strip()
            autor = ent_autor.get().strip()
            ubicacion = ent_ubicacion.get().strip() or "Bodega"
            
            try:
                cantidad = int(ent_cantidad.get())
                if cantidad <= 0:
                    messagebox.showerror("Error", "La cantidad debe ser mayor que 0.")
                    return
            except ValueError:
                messagebox.showerror("Error", "La cantidad debe ser un número válido.")
                return
            
            if not codigo or not titulo:
                messagebox.showerror("Error", "Código y Título son obligatorios.")
                return
            
            exito, mensaje = database.registrar_libro_db(codigo, titulo, autor, ubicacion, cantidad)
            if exito:
                messagebox.showinfo("Éxito", mensaje)
                self.show_libros()
            else:
                messagebox.showerror("Error", mensaje)
        
        ctk.CTkButton(self, text="💾 GUARDAR LIBRO", command=guardar, fg_color="#27ae60", font=("Arial", 14, "bold")).pack(pady=40)
        
        btn_volver = ctk.CTkButton(self, text="← Volver a Libros", command=self.show_libros, fg_color="#34495e")
        btn_volver.pack(pady=10)
