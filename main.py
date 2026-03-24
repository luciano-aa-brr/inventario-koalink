from email import errors
from tkinter import messagebox

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm
import barcode
from barcode.writer import ImageWriter
import customtkinter as ctk
import database
import os

import sys

# --- CONFIGURACIÓN GLOBAL DE TEMA ---
# Esto obliga a la App a ser siempre oscura, ignorando el modo de Windows
ctk.set_appearance_mode("Dark")  ## AÑADIR ESTO: Fuerza Modo Oscuro
# Opcionalmente, puedes setear el color de acento (blue, green, dark-blue)
ctk.set_default_color_theme("dark-blue") ## AÑADIR ESTO: Tema de color por defecto

def recurso_ruta(relative_path):
    """ 
    Obtiene la ruta absoluta para recursos (imágenes, bases de datos).
    Funciona tanto en modo desarrollo (Python) como en el ejecutable (.exe).
    """
    try:
        # PyInstaller crea una carpeta temporal y guarda la ruta en _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # Si no es un ejecutable, usa la ruta normal de la carpeta actual
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)
# Configuración de colores
COLOR_AMARILLO = "#FFFA03"

class AppKoaLink(ctk.CTk):
    def __init__(self):
        super().__init__()

        # 1. Título y Pantalla Completa Automática
        self.title("KoaLink - Escuela Araucanía")

        try:
            ruta_icono = recurso_ruta("assets/logo.ico")
            if os.path.exists(ruta_icono):
                self.iconbitmap(ruta_icono)
        except Exception as e:
            print(f"No se pudo cargar el icono: {e}")

            
        self.after(0, lambda: self.state('zoomed')) 
        

        database.crear_tabla_bajas()
        # 2. Inicializar Base de Datos
        database.inicializar_tablas()
      
        # 3. Configuración de Layout (Grid)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- SIDEBAR (Menú Lateral) ---
        self.sidebar = ctk.CTkFrame(self, width=240, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        
        ctk.CTkLabel(self.sidebar, text="KoaLink", font=("Arial", 28, "bold"), 
                     text_color=COLOR_AMARILLO).pack(pady=30)
        
        
        # --- SIDEBAR (Menú Lateral) ---
        self.sidebar = ctk.CTkFrame(self, width=240, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        ctk.CTkLabel(self.sidebar, text="Koalink", font=("Arial", 28, "bold"), 
                     text_color="#FFFA03").pack(pady=30)
    
        # Botones de Navegación 
        self.btn_inv = ctk.CTkButton(self.sidebar, text="📋 Inventario", command=self.mostrar_inventario)
        self.btn_inv.pack(pady=10, padx=20, fill="x")
 
        self.btn_nuevo = ctk.CTkButton(self.sidebar, text="➕ Nuevo Ingreso", command=self.mostrar_alta_equipo)
        self.btn_nuevo.pack(pady=10, padx=20, fill="x")

        # ESTE ES EL BOTÓN QUE FALTA:
        self.btn_prestamo = ctk.CTkButton(self.sidebar, text="📤 Préstamo", command=self.mostrar_prestamos)
        self.btn_prestamo.pack(pady=10, padx=20, fill="x")
        
        # Botón para Devoluciones (lo dejaremos listo)
        self.btn_devolucion = ctk.CTkButton(self.sidebar, text="📥 Devolución", command=self.mostrar_devoluciones)
        self.btn_devolucion.pack(pady=10, padx=20, fill="x")

        # Botón para Historial de Préstamos (lo dejaremos listo, aunque no lo implementemos aún)
        self.btn_historial = ctk.CTkButton(self.sidebar, text="📋 Historial", command=self.mostrar_historial_activos)
        self.btn_historial.pack(pady="10", padx=20, fill="x")

        # En tu función mostrar_inventario, antes de crear la tabla:
        self.btn_generar_todo = ctk.CTkButton(self.sidebar, text="📄 Generar Etiquetas", fg_color="#e67e22", hover_color="#d35400", command=self.generar_pdf_etiquetas)
        self.btn_generar_todo.pack(pady="10", padx=20, fill="x")

        # --- PANEL CENTRAL ---
        self.main_frame = ctk.CTkFrame(self, corner_radius=15)
        self.main_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")

        # Cargar Dashboard al inicio
        self.mostrar_inventario()

    def limpiar_panel(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def generar_pdf_etiquetas(self):
        # 1. Obtener todos los artículos
        items = database.obtener_articulos_inventario_completo("Todos")
        if not items:
            messagebox.showwarning("KoaLink", "No hay artículos en el inventario.")
            return

        # 2. Configuración del PDF
        nombre_pdf = "etiquetas_koalink.pdf"
        c = canvas.Canvas(nombre_pdf, pagesize=letter)
        ancho_pagina, alto_pagina = letter

        # Medidas de la etiqueta (ajustadas para libros/elementos pequeños)
        ancho_etiqueta = 60 * mm
        alto_etiqueta = 35 * mm
        margen_x = 10 * mm
        margen_y = 15 * mm
        espacio_entre_columnas = 5 * mm
        espacio_entre_filas = 5 * mm

        x_actual = margen_x
        y_actual = alto_pagina - margen_y - alto_etiqueta
        columna_actual = 0

        if not os.path.exists("temp_barcodes"):
            os.makedirs("temp_barcodes")

        for it in items:
            cod, nom, cat, est, ubi, cant, resp, dest, fecha = it
            
            # --- GENERAR CÓDIGO DE BARRAS TEMPORAL ---
            COD = barcode.get_barcode_class('code128')
            # Configuramos para que no tenga texto abajo (lo pondremos nosotros con ReportLab)
            mi_barcode = COD(cod, writer=ImageWriter())
            ruta_img = f"temp_barcodes/{cod}"
            mi_barcode.save(ruta_img, options={"write_text": False, "module_height": 5.0})
            ruta_full = f"{ruta_img}.png"

            # --- DIBUJAR EN EL PDF ---
            # Recuadro de corte (gris suave)
            c.setStrokeColorRGB(0.8, 0.8, 0.8)
            c.rect(x_actual, y_actual, ancho_etiqueta, alto_etiqueta)

            # Texto: Nombre del artículo (Arriba)
            c.setFillColorRGB(0, 0, 0)
            c.setFont("Helvetica-Bold", 8)
            c.drawCentredString(x_actual + ancho_etiqueta/2, y_actual + alto_etiqueta - 10, f"{nom[:25]}")

            # Imagen del código de barras (Centro)
            c.drawImage(ruta_full, x_actual + 5*mm, y_actual + 10, width=ancho_etiqueta - 10*mm, height=alto_etiqueta - 18*mm, mask='auto')

            # Texto: Código ID (Abajo)
            c.setFont("Helvetica", 7)
            c.drawCentredString(x_actual + ancho_etiqueta/2, y_actual + 3, f"ID: {cod}")

            # --- LÓGICA DE POSICIONAMIENTO (3 COLUMNAS) ---
            columna_actual += 1
            if columna_actual < 3:
                x_actual += ancho_etiqueta + espacio_entre_columnas
            else:
                columna_actual = 0
                x_actual = margen_x
                y_actual -= (alto_etiqueta + espacio_entre_filas)

            # Si llegamos al final de la hoja, crear nueva página
            if y_actual < margen_y:
                c.showPage()
                y_actual = alto_pagina - margen_y - alto_etiqueta
                x_actual = margen_x

        c.save()
        
        # Limpieza de imágenes temporales
        for f in os.listdir("temp_barcodes"):
            os.remove(os.path.join("temp_barcodes", f))
        
        if os.path.exists("temp_barcodes"):
            os.rmdir("temp_barcodes")

        messagebox.showinfo("KoaLink", f"PDF generado con éxito: {nombre_pdf}")
        os.startfile(nombre_pdf)


    def mostrar_inventario(self):
        self.limpiar_panel()

        header = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkLabel(header, text="Gestión de Inventario", font=("Arial", 24, "bold")).pack(side="left")

        # --- SWITCH PARA INACTIVOS ---
        self.ver_inactivos_var = ctk.BooleanVar(value=False)
        self.sw_inactivos = ctk.CTkSwitch(header, text="Ver Equipos de Baja (Inactivos)", 
                                          variable=self.ver_inactivos_var,
                                          command=self.actualizar_tabla_inventario)
        self.sw_inactivos.pack(side="right", padx=20)

        # Filtro de Categoría (ya lo tenías)
        self.filtro_cat = ctk.CTkComboBox(header, values=["Todos", "Tablet", "Notebook", "Libro", "Material Didáctico"], 
                                          command=lambda _: self.actualizar_tabla_inventario())
        self.filtro_cat.set("Todos")
        self.filtro_cat.pack(side="right", padx=10)

        self.tabla_container = ctk.CTkScrollableFrame(self.main_frame, fg_color="#1d1d1d")
        self.tabla_container.pack(fill="both", expand=True, padx=20, pady=10)

        self.actualizar_tabla_inventario()

    def actualizar_tabla_inventario(self):
        """Dibuja las filas de la tabla con soporte para la nueva lógica de bajas parciales."""
        # 1. Limpiar filas anteriores
        for w in self.tabla_container.winfo_children():
            w.destroy()

        # 2. Encabezados de la tabla
        headers = ["CÓDIGO", "ARTÍCULO", "ESTADO", "STOCK", "UBICACIÓN / INFO", "ACCIONES"]
        for i, h in enumerate(headers):
            ctk.CTkLabel(self.tabla_container, text=h, font=("Arial", 12, "bold"), 
                         text_color="#aaaaaa").grid(row=0, column=i, padx=10, pady=10)

        # 3. Obtener parámetros de los filtros
        categoria = self.filtro_cat.get()
        ver_de_baja = self.ver_inactivos_var.get()

        # 4. Cargar datos según el modo (Normal o Bajas)
        if ver_de_baja:
            # Nueva consulta que suma lo que hay en la tabla 'bajas'
            items = database.obtener_articulos_inactivos_reporte()
        else:
            # Consulta normal a la tabla 'articulos'
            items = database.obtener_articulos_inventario_completo(categoria)

        # 5. Bucle para construir las filas
        for idx, it in enumerate(items, start=1):
            if ver_de_baja:
                # Si viene de 'obtener_articulos_inactivos_reporte', el orden es:
                # cod, nom, est, cant, ubi
                cod, nom, est, cant, info_extra = it
                color_est = "#95a5a6" # Gris para inactivos
                info_ubicacion = f"📍 {info_extra}"
            else:
                # Si viene de 'inventario_completo', el orden es el estándar:
                cod, nom, cat, est, ubi, cant, resp, dest, fecha = it
                color_est = "#2ecc71" if est == "Disponible" else "#e67e22"
                info_ubicacion = f"{ubi}" if est == "Disponible" else f"👤 {resp} ({dest})"

            # Dibujar celdas de información
            ctk.CTkLabel(self.tabla_container, text=cod).grid(row=idx, column=0, padx=10, pady=5)
            ctk.CTkLabel(self.tabla_container, text=nom, wraplength=200).grid(row=idx, column=1, padx=10, pady=5)
            ctk.CTkLabel(self.tabla_container, text=est, text_color=color_est, font=("Arial", 11, "bold")).grid(row=idx, column=2, padx=10, pady=5)
            
            # Aquí 'cant' mostrará el stock disponible (si es normal) o el stock en baja (si es inactivo)
            ctk.CTkLabel(self.tabla_container, text=str(cant)).grid(row=idx, column=3, padx=10, pady=5)
            ctk.CTkLabel(self.tabla_container, text=info_ubicacion, font=("Arial", 11)).grid(row=idx, column=4, padx=10, pady=5)

            # --- BOTONES DE ACCIÓN ---
            btn_frame = ctk.CTkFrame(self.tabla_container, fg_color="transparent")
            btn_frame.grid(row=idx, column=5, padx=10, pady=5)

            if ver_de_baja:
                # BOTÓN REACTIVAR: Pasamos código, nombre y la cantidad que hay en baja
                ctk.CTkButton(btn_frame, text="🔄 Reactivar", width=80, fg_color="#9b59b6", 
                              hover_color="#8e44ad",
                              command=lambda c=cod, n=nom, s=cant: self.reactivar_equipo(c, n, s)).pack(side="left", padx=2)
            else:
                # BOTONES NORMALES
                ctk.CTkButton(btn_frame, text="✎", width=30, fg_color="#3498db", 
                              hover_color="#2980b9",
                              command=lambda a=it: self.abrir_ventana_edicion(a)).pack(side="left", padx=2)
                
                # BOTÓN BAJA: Pasamos código, nombre y el stock actual para validar la resta
                ctk.CTkButton(btn_frame, text="🗑", width=30, fg_color="#e74c3c", 
                              hover_color="#c0392b",
                              command=lambda c=cod, n=nom, s=cant: self.dar_de_baja(c, n, s)).pack(side="left", padx=2)
            
    def reactivar_equipo(self, codigo, nombre, stock_inactivo):
        dialogo = ctk.CTkInputDialog(
            text=f"¿Cuántas unidades de '{nombre}' desea reactivar?\n(En baja: {stock_inactivo})",
            title="Reactivar"
        )
        entrada = dialogo.get_input()
        
        # Estas líneas deben estar alineadas con 'dialogo'
        if not entrada: 
            return # <-- Ahora sí está dentro de la función

        try:
            cantidad = int(entrada)
            if cantidad > stock_inactivo:
                messagebox.showwarning("KoaLink", f"Solo puedes reactivar hasta {stock_inactivo} unidades.")
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
        """Mantiene el nombre original pero añade lógica de cantidad parcial."""
        
        cantidad_a_retirar = 1 # Por defecto
        
        # Si hay más de una unidad, preguntamos cuántas se eliminan
        if stock_actual > 1:
            dialogo = ctk.CTkInputDialog(
                text=f"¿Cuántas unidades de '{nombre}' desea dar de baja?\n(Stock disponible: {stock_actual})",
                title="Baja de Inventario"
            )
            entrada = dialogo.get_input()
            
            if not entrada: return # Cancelar si cierra la ventana
            
            try:
                cantidad_a_retirar = int(entrada)
                if cantidad_a_retirar <= 0 or cantidad_a_retirar > stock_actual:
                    messagebox.showwarning("Atención", f"Cantidad inválida. Debe ser entre 1 y {stock_actual}")
                    return
            except ValueError:
                messagebox.showerror("Error", "Ingrese un número entero válido.")
                return
        else:
            # Confirmación simple para un solo elemento
            if not messagebox.askyesno("Confirmar", f"¿Seguro que desea dar de baja: {nombre}?"):
                return

        # Llamada a la base de datos (asegúrate de que en database.py reciba estos 2 parámetros)
        exito, msj = database.dar_de_baja_db(codigo, cantidad_a_retirar)
        
        if exito:
            messagebox.showinfo("KoaLink", msj)
            self.mostrar_inventario() # Refresca la lista automáticamente
        else:
            messagebox.showerror("Error", msj)

    def abrir_ventana_edicion(self, item):
        """Abre una ventana flotante para editar los datos del artículo seleccionado."""
        # item viene con: (cod, nom, cat, est, ubi, cant, resp, dest, fecha)
        
        modal = ctk.CTkToplevel(self)
        modal.title(f"Editando: {item[0]}")
        modal.geometry("400x500")
        modal.attributes("-topmost", True) # Mantener al frente
        modal.grab_set() # Bloquea la ventana principal hasta cerrar esta

        ctk.CTkLabel(modal, text="Modificar Información", font=("Arial", 18, "bold"), text_color="#FFFA03").pack(pady=20)

        # Campos de edición
        ctk.CTkLabel(modal, text="Nombre / Modelo:").pack(pady=(10,0))
        ent_nom = ctk.CTkEntry(modal, width=300)
        ent_nom.insert(0, item[1])
        ent_nom.pack(pady=5)

        ctk.CTkLabel(modal, text="Categoría:").pack(pady=(10,0))
        cb_cat = ctk.CTkComboBox(modal, values=["Tablet", "Notebook", "Libro", "Material Didáctico", "Impresora"], width=300)
        cb_cat.set(item[2])
        cb_cat.pack(pady=5)

        ctk.CTkLabel(modal, text="Ubicación Base:").pack(pady=(10,0))
        ent_ubi = ctk.CTkEntry(modal, width=300)
        ent_ubi.insert(0, item[4])
        ent_ubi.pack(pady=5)

        ctk.CTkLabel(modal, text="Stock Total:").pack(pady=(10,0))
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

    def mostrar_alta_equipo(self):
        self.limpiar_panel() # <--- ¡Ahora sí encontrará la función!
        
        ctk.CTkLabel(self.main_frame, text="Registro de Inventario", 
                     font=("Arial", 26, "bold"), text_color="#FFFA03").pack(pady=(30, 20))

        form_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        form_frame.pack(pady=10, padx=50)

        # Lógica de cambio de categoría
        def al_cambiar_categoria(seleccion):
            siguiente_cod = database.generar_siguiente_codigo(seleccion)
            ent_cod.delete(0, 'end')
            ent_cod.insert(0, siguiente_cod)

            if seleccion in ["Tablet", "Notebook", "Impresora"]:
                ent_cant.delete(0, 'end')
                ent_cant.insert(0, "1")
                ent_cant.configure(state="disabled") # Bloqueado para equipos únicos
            else:
                ent_cant.configure(state="normal")

        # Campos
        ctk.CTkLabel(form_frame, text="Categoría:").grid(row=0, column=0, padx=20, pady=15, sticky="e")
        combo_cat = ctk.CTkComboBox(form_frame, values=["Tablet", "Notebook", "Libro", "Material Didáctico"], 
                                    command=al_cambiar_categoria, width=350)
        combo_cat.grid(row=0, column=1)

        ctk.CTkLabel(form_frame, text="Código:").grid(row=1, column=0, padx=20, pady=15, sticky="e")
        ent_cod = ctk.CTkEntry(form_frame, width=350)
        ent_cod.grid(row=1, column=1)

        ctk.CTkLabel(form_frame, text="Nombre:").grid(row=2, column=0, padx=20, pady=15, sticky="e")
        ent_nom = ctk.CTkEntry(form_frame, width=350)
        ent_nom.grid(row=2, column=1)

        ctk.CTkLabel(form_frame, text="Stock:").grid(row=3, column=0, padx=20, pady=15, sticky="e")
        ent_cant = ctk.CTkEntry(form_frame, width=350)
        ent_cant.insert(0, "1")
        ent_cant.grid(row=3, column=1)

        def guardar():
            exito, mensaje = database.guardar_item_db(ent_cod.get(), ent_nom.get(), combo_cat.get(), "Bodega", int(ent_cant.get()))
            if exito:
                messagebox.showinfo("Éxito", mensaje)
                self.mostrar_alta_equipo() # Refrescar formulario
            else:
                messagebox.showerror("Error", mensaje)

        ctk.CTkButton(self.main_frame, text="📥 REGISTRAR", command=guardar, fg_color="#27ae60").pack(pady=40)
        
        # Carga inicial
        al_cambiar_categoria("Tablet")

    def mostrar_prestamos(self):
        self.limpiar_panel()
        
        # --- NUEVA VARIABLE: EL CARRITO DE PRÉSTAMOS ---
        # Lista temporal para guardar los ítems seleccionados antes de confirmar
        self.lista_items_seleccionados = [] 

        # Diseño dividido (Grid)
        self.main_frame.grid_columnconfigure(0, weight=3) # Inventario (Izquierda)
        self.main_frame.grid_columnconfigure(1, weight=2) # Formulario y Carrito (Derecha)
        self.main_frame.grid_rowconfigure(0, weight=1)

        # =========================================================
        # --- COLUMNA IZQUIERDA: BUSCADOR DE INVENTARIO ---
        # =========================================================
        izq_frame = ctk.CTkFrame(self.main_frame, fg_color="#1d1d1d", corner_radius=15)
        izq_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        ctk.CTkLabel(izq_frame, text="🔍 Buscar en Inventario Disponible", font=("Arial", 18, "bold"), text_color="#FFFA03").pack(pady=10)
        
        # Buscador en tiempo real
        self.ent_busqueda_p = ctk.CTkEntry(izq_frame, placeholder_text="Escriba nombre, código o categoría...")
        self.ent_busqueda_p.pack(fill="x", padx=20, pady=5)
        self.ent_busqueda_p.bind("<KeyRelease>", lambda e: self.refrescar_tabla_prestamos())

        # Tabla de selección rápida (Scrollable)
        self.tabla_p = ctk.CTkScrollableFrame(izq_frame, fg_color="transparent")
        self.tabla_p.pack(fill="both", expand=True, padx=10, pady=10)
        
        # =========================================================
        # --- COLUMNA DERECHA: FORMULARIO Y CARRITO ---
        # =========================================================
        der_frame = ctk.CTkFrame(self.main_frame, corner_radius=15)
        der_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        # 1. DATOS DEL RESPONSABLE (Parte Superior)
        resp_frame = ctk.CTkFrame(der_frame, fg_color="transparent")
        resp_frame.pack(fill="x", pady=10, padx=10)
        
        ctk.CTkLabel(resp_frame, text="👤 Datos del Responsable", font=("Arial", 16, "bold"), text_color="#FFFA03").pack(pady=(0,10))
        
        # Combo Tipo de Persona
        self.combo_tipo_p = ctk.CTkComboBox(resp_frame, values=["Estudiante", "Funcionario"], width=300)
        self.combo_tipo_p.set("Estudiante") # Por defecto Estudiante
        self.combo_tipo_p.pack(pady=5)

        self.ent_resp_p = ctk.CTkEntry(resp_frame, placeholder_text="Nombre Completo del Responsable", width=300)
        self.ent_resp_p.pack(pady=5)

        self.ent_dest_p = ctk.CTkEntry(resp_frame, placeholder_text="Sala o Oficina de Destino", width=300)
        self.ent_dest_p.pack(pady=5)

        # Separador visual
        ctk.CTkFrame(der_frame, height=2, fg_color="#333333").pack(fill="x", padx=10, pady=15)

        # 2. EL CARRITO DE PRÉSTAMOS (Parte Inferior)
        carrito_frame = ctk.CTkFrame(der_frame, fg_color="transparent")
        carrito_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(carrito_frame, text="🛒 Elementos Seleccionados", font=("Arial", 16, "bold")).pack(pady=(0,10))
        
        # Área scrollable donde se irán listando los ítems agregados
        self.carrito_lista = ctk.CTkScrollableFrame(carrito_frame, fg_color="#1a1a1a", height=200)
        self.carrito_lista.pack(fill="both", expand=True, padx=5, pady=5)

        # Botón Final de Confirmación (usando la lógica de stock que definimos antes)
        def confirmar_todo_el_prestamo():
            resp = self.ent_resp_p.get()
            dest = self.ent_dest_p.get()
            tipo = self.combo_tipo_p.get()
            
            if not resp or not dest or not self.lista_items_seleccionados:
                messagebox.showwarning("Atención", "Complete los datos del responsable y agregue elementos al carrito.")
                return

            # LLAMADA CORREGIDA: Ahora enviamos todo el carrito de una vez
            exito, msj = database.registrar_prestamo_multiple(
                resp, dest, tipo, self.lista_items_seleccionados
            )
            
            if exito:
                messagebox.showinfo("Éxito", msj)
                self.mostrar_prestamos() # Recargar para limpiar
            else:
                messagebox.showerror("Error", msj)
            
            # Resumen final
            mensaje_final = f"Préstamo exitoso de {exito} artículos."
            if errors:
                mensaje_final += "\n\nProblemas encontrados:\n" + "\n".join(errors)
                messagebox.showwarning("Resumen", mensaje_final)
            else:
                messagebox.showinfo("Éxito", mensaje_final)
                # Volvemos a cargar el módulo para limpiar todo
                self.mostrar_prestamos()

        ctk.CTkButton(der_frame, text="📤 CONFIRMAR PRÉSTAMO TOTAL", 
                      fg_color="#27ae60", hover_color="#2ecc71", font=("Arial", 14, "bold"),
                      height=45, command=confirmar_todo_el_prestamo).pack(pady=20, padx=20, fill="x")

        # Iniciar tabla de inventario
        self.refrescar_tabla_prestamos()

    # --- FUNCIÓN 1: Actualizar la tabla del Inventario (Izquierda) ---
    def refrescar_tabla_prestamos(self):
        """Filtra y muestra los elementos disponibles para prestar en la izquierda."""
        # 1. Limpiamos la lista visual actual para redibujar
        for w in self.tabla_p.winfo_children(): 
            w.destroy()
        
        # 2. Obtenemos el texto del buscador (en minúsculas)
        busqueda = self.ent_busqueda_p.get().lower()
        
        # 3. Traemos todos los artículos desde la base de datos
        items = database.obtener_articulos_inventario_completo("Todos")

        # Encabezado simple para la lista
        ctk.CTkLabel(self.tabla_p, text="Resultados de búsqueda:", 
                     font=("Arial", 11, "italic"), text_color="#aaaaaa").pack(anchor="w", padx=10, pady=5)

        for it in items:
            # Estructura: cod, nom, cat, est, ubi, cant, resp, dest, fecha
            cod, nom, cat, est, ubi, cant, resp, dest, fecha = it
            
            # --- LÓGICA DEL FILTRO ---
            # Buscamos coincidencias en Nombre, Código o Categoría
            coincide = (busqueda in nom.lower() or 
                        busqueda in cod.lower() or 
                        busqueda in cat.lower())
            
            # Solo procesamos si coincide con la búsqueda o si el buscador está vacío
            if busqueda == "" or coincide:
                # Determinamos si el ítem es "Prestable" (Stock > 0 y no está Inactivo)
                es_prestable = cant > 0 and est != "Inactivo"

                # Creamos el contenedor de la tarjeta
                # Si no hay stock, usamos un fondo más oscuro
                color_fondo = "#2b2b2b" if es_prestable else "#1a1a1a"
                f = ctk.CTkFrame(self.tabla_p, fg_color=color_fondo, corner_radius=8)
                f.pack(fill="x", pady=3, padx=5)
                
                # --- INFORMACIÓN DEL ARTÍCULO (Lado Izquierdo de la tarjeta) ---
                txt_frame = ctk.CTkFrame(f, fg_color="transparent")
                txt_frame.pack(side="left", padx=15, pady=8)
                
                # Nombre del artículo
                color_texto = "#ffffff" if es_prestable else "#555555"
                ctk.CTkLabel(txt_frame, text=nom, font=("Arial", 13, "bold"), 
                             text_color=color_texto, anchor="w").pack(anchor="w")
                
                # Detalles (Código y Stock disponible)
                detalle_txt = f"ID: {cod} | Disponible: {cant} | Cat: {cat}"
                ctk.CTkLabel(txt_frame, text=detalle_txt, font=("Arial", 10), 
                             text_color="#888888", anchor="w").pack(anchor="w")

                # --- BOTÓN DE ACCIÓN (Lado Derecho de la tarjeta) ---
                if es_prestable:
                    # Botón activo si hay stock
                    btn_add = ctk.CTkButton(f, text="➕ Agregar", width=80, height=30,
                                           fg_color="#3498db", hover_color="#2980b9",
                                           font=("Arial", 11, "bold"),
                                           command=lambda c=cod, n=nom, ct=cat, s=cant: self.agregar_al_carrito(c, n, ct, s))
                    btn_add.pack(side="right", padx=15)
                else:
                    # Etiqueta de "Sin Stock" o "Prestado" si no hay unidades
                    estado_msj = "AGOTADO" if cant <= 0 else "INACTIVO"
                    ctk.CTkLabel(f, text=estado_msj, font=("Arial", 10, "bold"), 
                                 text_color="#e74c3c", width=80).pack(side="right", padx=15)

    # --- FUNCIÓN 2: Agregar un ítem al Carrito de Préstamos ---
    def agregar_al_carrito(self, codigo, nombre, categoria, stock_max):
        """Añade un ítem a la lista temporal y lo muestra en el carrito derecho."""
        
        # Validación de cantidad para ítems con stock (Libros/Materiales)
        cantidad_a_prestar = 1
        if categoria not in ["Tablet", "Notebook", "Impresora"]:
            # Usamos un InputDialog simple para preguntar cantidad si es stock masivo
            dialogo = ctk.CTkInputDialog(text=f"¿Cuántos de '{nombre}' desea prestar? (Máx: {stock_max})", title="Cantidad")
            try:
                entrada_cant = dialogo.get_input()
                if not entrada_cant: return # Cancelado
                cantidad_a_prestar = int(entrada_cant)
                if cantidad_a_prestar <= 0 or cantidad_a_prestar > stock_max:
                    messagebox.showwarning("Atención", "Cantidad inválida o superior al stock disponible.")
                    return
            except ValueError:
                messagebox.showerror("Error", "La cantidad debe ser un número.")
                return

        # Revisamos si el ítem ya está en el carrito para no duplicarlo (opcional, podrías sumarlo)
        for item in self.lista_items_seleccionados:
            if item["codigo"] == codigo:
                messagebox.showwarning("Atención", "Este elemento ya está en el carrito.")
                return

        # Agregamos a la lista de datos
        self.lista_items_seleccionados.append({
            "codigo": codigo,
            "nombre": nombre,
            "cantidad": cantidad_a_prestar
        })

        # Refrescamos visualmente la lista del carrito
        self.refrescar_visual_del_carrito()

    # --- FUNCIÓN 3: Refrescar la lista visual del Carrito (Derecha) ---
    def refrescar_visual_del_carrito(self):
        """Redibuja la lista del carrito con el botón de eliminar (X) para cada ítem."""
        for w in self.carrito_lista.winfo_children(): w.destroy()
        
        for item in self.lista_items_seleccionados:
            f = ctk.CTkFrame(self.carrito_lista, fg_color="#2b2b2b", corner_radius=5)
            f.pack(fill="x", pady=2, padx=5)
            
            # Detalle del ítem: Nombre xCantidad
            ctk.CTkLabel(f, text=f"• {item['nombre']} x{item['cantidad']}", font=("Arial", 11), text_color="#2ecc71").pack(side="left", padx=10, pady=2)
            
            # Botón de eliminar (X) para quitar del carrito
            ctk.CTkButton(f, text="X", width=25, height=20, font=("Arial", 10, "bold"),
                          fg_color="#c0392b", hover_color="#e74c3c",
                          command=lambda c=item["codigo"]: self.quitar_del_carrito(c)).pack(side="right", padx=5)

    # --- FUNCIÓN 4: Quitar un ítem del Carrito ---
    def quitar_del_carrito(self, codigo):
        """Elimina un ítem de la lista temporal basándose en su código."""
        # Filtramos la lista para dejar fuera el ítem con ese código
        self.lista_items_seleccionados = [i for i in self.lista_items_seleccionados if i["codigo"] != codigo]
        # Volvemos a dibujar
        self.refrescar_visual_del_carrito()
        
    def mostrar_devoluciones(self):
        self.limpiar_panel()
        self.lista_devolucion_temp = [] # Carrito de devolución

        self.main_frame.grid_columnconfigure(0, weight=3)
        self.main_frame.grid_columnconfigure(1, weight=2)
        self.main_frame.grid_rowconfigure(0, weight=1)

        # --- IZQUIERDA: BUSCADOR DE EQUIPOS FUERA ---
        izq_frame = ctk.CTkFrame(self.main_frame, fg_color="#1d1d1d", corner_radius=15)
        izq_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        ctk.CTkLabel(izq_frame, text="📥 Buscar Equipos para Devolver", font=("Arial", 18, "bold"), text_color="#FFFA03").pack(pady=10)
        
        self.ent_busqueda_dev = ctk.CTkEntry(izq_frame, placeholder_text="Escriba nombre del equipo o responsable...")
        self.ent_busqueda_dev.pack(fill="x", padx=20, pady=5)
        self.ent_busqueda_dev.bind("<KeyRelease>", lambda e: self.refrescar_tabla_devoluciones())

        self.tabla_dev = ctk.CTkScrollableFrame(izq_frame, fg_color="transparent")
        self.tabla_dev.pack(fill="both", expand=True, padx=10, pady=10)

        # --- DERECHA: CARRITO DE RECEPCIÓN ---
        der_frame = ctk.CTkFrame(self.main_frame, corner_radius=15)
        der_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        ctk.CTkLabel(der_frame, text="🛒 Recepción de Materiales", font=("Arial", 18, "bold"), text_color="#FFFA03").pack(pady=20)
        
        self.carrito_dev_lista = ctk.CTkScrollableFrame(der_frame, fg_color="#1a1a1a", height=400)
        self.carrito_dev_lista.pack(fill="both", expand=True, padx=10, pady=10)

        def confirmar_recepcion_total():
            # 1. Verificamos que el carrito no esté vacío
            if not self.lista_devolucion_temp:
                messagebox.showwarning("Atención", "No hay elementos en el carrito de devolución.")
                return

            exitos = 0
            # 2. Recorremos el carrito temporal
            for item in self.lista_devolucion_temp:
                # CAMBIO CLAVE: Usamos 'registrar_devolucion_item_db' 
                # enviando el id_detalle, el código y la cantidad
                exito, msj = database.registrar_devolucion_item_db(
                    item["id_detalle"], 
                    item["codigo"], 
                    item["cantidad"]
                )
                
                if exito:
                    exitos += 1
                else:
                    # Imprimimos en consola por si algún ítem falla para debuggear
                    print(f"Error al devolver {item['nombre']}: {msj}")
            
            # 3. Mensaje final con el conteo real de éxitos
            if exitos > 0:
                messagebox.showinfo("Éxito", f"Se han reingresado {exitos} artículos al inventario correctamente.")
            else:
                messagebox.showerror("Error", "No se pudo procesar ninguna devolución. Verifique los datos.")
            
            # 4. Refrescamos la pantalla completa para limpiar carritos y tablas
            self.mostrar_devoluciones()

        # El botón se mantiene igual, pero ahora ejecutará la lógica nueva
        ctk.CTkButton(der_frame, text="📥 CONFIRMAR RECEPCIÓN", fg_color="#27ae60", 
                      height=50, font=("Arial", 14, "bold"), 
                      command=confirmar_recepcion_total).pack(pady=20, padx=20, fill="x")

        self.refrescar_tabla_devoluciones()

    def refrescar_tabla_devoluciones(self):
        """Muestra los artículos individuales que están fuera (detalle_prestamo)."""
        for w in self.tabla_dev.winfo_children(): w.destroy()
        
        busqueda = self.ent_busqueda_dev.get().lower()
        # Usamos la nueva función de database.py
        items_prestados = database.obtener_detalles_prestados(busqueda)

        for it in items_prestados:
            id_det, cod, nom, resp, dest, cant = it
            
            f = ctk.CTkFrame(self.tabla_dev, fg_color="#2b2b2b", corner_radius=8)
            f.pack(fill="x", pady=3, padx=5)
            
            # Información clara de quién tiene qué
            txt_info = f"{nom} (x{cant})\n👤 {resp} | 📍 {dest}"
            ctk.CTkLabel(f, text=txt_info, font=("Arial", 11), anchor="w", justify="left").pack(side="left", padx=15, pady=8)
            
            # Al agregar al carrito de devolución, incluimos el ID del detalle
            ctk.CTkButton(f, text="📥 Recibir", width=70, height=30,
                          command=lambda d=id_det, c=cod, n=nom, q=cant: self.agregar_a_devolucion(d, c, n, q)).pack(side="right", padx=10)

    def agregar_a_devolucion(self, id_detalle, codigo, nombre, cantidad_max):
        """Agrega el ítem al carrito y pregunta cantidad si es necesario."""
        # Evitar duplicados
        if any(i["id_detalle"] == id_detalle for i in self.lista_devolucion_temp): 
            return

        cantidad_a_regresar = cantidad_max
        
        # Si hay más de 1 unidad (ej. Libros), preguntamos cuántas devuelve
        if cantidad_max > 1:
            dialogo = ctk.CTkInputDialog(
                text=f"¿Cuántas unidades de '{nombre}' devuelve?\n(Máximo: {cantidad_max})", 
                title="Devolución Parcial"
            )
            try:
                entrada = dialogo.get_input()
                if not entrada: return # Cancelar
                cantidad_a_regresar = int(entrada)
                if cantidad_a_regresar <= 0 or cantidad_a_regresar > cantidad_max:
                    messagebox.showwarning("Error", "Cantidad no válida.")
                    return
            except ValueError:
                messagebox.showerror("Error", "Debe ingresar un número.")
                return

        # Agregamos al carrito con la cantidad elegida
        self.lista_devolucion_temp.append({
            "id_detalle": id_detalle, 
            "codigo": codigo, 
            "nombre": nombre, 
            "cantidad": cantidad_a_regresar,
            "es_parcial": cantidad_a_regresar < cantidad_max # Marca si sobran unidades fuera
        })
        self.refrescar_visual_carrito_dev()

    def refrescar_visual_carrito_dev(self):
        """Redibuja el carrito derecho."""
        for w in self.carrito_dev_lista.winfo_children(): w.destroy()
        for item in self.lista_devolucion_temp:
            f = ctk.CTkFrame(self.carrito_dev_lista, fg_color="#2b2b2b", corner_radius=5)
            f.pack(fill="x", pady=2, padx=5)
            
            # Texto con cantidad
            ctk.CTkLabel(f, text=f"• {item['nombre']} (x{item['cantidad']})", font=("Arial", 11)).pack(side="left", padx=10)
            
            ctk.CTkButton(f, text="X", width=25, height=20, fg_color="#c0392b", 
                          command=lambda c=item["id_detalle"]: self.quitar_de_devolucion(c)).pack(side="right", padx=5)

    def quitar_de_devolucion(self, codigo):
        self.lista_devolucion_temp = [i for i in self.lista_devolucion_temp if i["codigo"] != codigo]
        self.refrescar_visual_carrito_dev()

    def mostrar_historial_activos(self):
        """Muestra una lista detallada de todo lo que está actualmente fuera de la escuela."""
        self.limpiar_panel()
        
        ctk.CTkLabel(self.main_frame, text="📋 Control de Préstamos Activos", 
                     font=("Arial", 24, "bold"), text_color="#FFFA03").pack(pady=20)
        
        # Buscador interno para el historial
        busqueda_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        busqueda_frame.pack(fill="x", padx=30)
        
        self.ent_buscar_historial = ctk.CTkEntry(busqueda_frame, placeholder_text="Buscar por profesor, alumno o equipo...", width=400)
        self.ent_buscar_historial.pack(side="left", padx=5)
        self.ent_buscar_historial.bind("<KeyRelease>", lambda e: self.actualizar_tabla_historial())

        # Contenedor de la tabla
        self.tabla_historial = ctk.CTkScrollableFrame(self.main_frame, fg_color="#1d1d1d", corner_radius=15)
        self.tabla_historial.pack(fill="both", expand=True, padx=30, pady=15)

        self.actualizar_tabla_historial()

    def actualizar_tabla_historial(self):
        """Refresca los datos del historial basándose en el buscador."""
        for w in self.tabla_historial.winfo_children(): w.destroy()
        
        termino = self.ent_buscar_historial.get().lower()
        registros = database.obtener_historial_activos_db()

        # Encabezados visuales
        h_frame = ctk.CTkFrame(self.tabla_historial, fg_color="#333333")
        h_frame.pack(fill="x", pady=2)
        ctk.CTkLabel(h_frame, text="ARTÍCULO", width=200, font=("Arial", 11, "bold")).pack(side="left", padx=5)
        ctk.CTkLabel(h_frame, text="RESPONSABLE", width=180, font=("Arial", 11, "bold")).pack(side="left", padx=5)
        ctk.CTkLabel(h_frame, text="CANT.", width=50, font=("Arial", 11, "bold")).pack(side="left", padx=5)
        ctk.CTkLabel(h_frame, text="FECHA SALIDA", width=150, font=("Arial", 11, "bold")).pack(side="left", padx=5)

        for reg in registros:
            nom, resp, dest, tipo, cant, fecha, cod = reg
            
            # Filtro de búsqueda
            if termino in nom.lower() or termino in resp.lower() or termino in cod.lower():
                f = ctk.CTkFrame(self.tabla_historial, fg_color="#2b2b2b")
                f.pack(fill="x", pady=1)
                
                ctk.CTkLabel(f, text=nom, width=200, anchor="w").pack(side="left", padx=5)
                ctk.CTkLabel(f, text=f"{resp}\n({dest})", width=180, anchor="w", font=("Arial", 10)).pack(side="left", padx=5)
                ctk.CTkLabel(f, text=str(cant), width=50, text_color="#2ecc71", font=("Arial", 11, "bold")).pack(side="left", padx=5)
                ctk.CTkLabel(f, text=fecha[:16], width=150, text_color="#888888").pack(side="left", padx=5)


if __name__ == "__main__":
    app = AppKoaLink()
    app.mainloop()