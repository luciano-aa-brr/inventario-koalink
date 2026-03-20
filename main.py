import customtkinter as ctk
from tkinter import messagebox
from PIL import Image
import pandas as pd
import database
import os
from datetime import datetime

# --- CONFIGURACIÓN DE IDENTIDAD VISUAL (ESCUELA ARAUCANÍA) ---
COLOR_AMARILLO_ESCUELA = "#FFFA03"
COLOR_GRIS_VENTANA = "#A2A2A1"
COLOR_NEGRO_FONDO = "#1a1a1a"
COLOR_BLANCO = "#FFFFFF"

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class AppKoaLink(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("KoaLink - Escuela Araucanía 510 Labranza")
        self.after(0, lambda: self.state('zoomed'))

        # Inicializar base de datos
        database.inicializar_tablas()

        self.lista_items_seleccionados = [] # Lista temporal para el carrito de préstamo

        # Lista temporal de equipos antes de confirmar
        self.carrito_prestamo = [] 

        # Layout Principal
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- BARRA LATERAL (SIDEBAR) ---
        self.sidebar_frame = ctk.CTkFrame(self, width=240, corner_radius=0, fg_color=COLOR_NEGRO_FONDO)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")

        # Cargar Logo
        try:
            ruta_logo = os.path.join(os.path.dirname(__file__), 'assets', 'logo.png')
            logo_pil = Image.open(ruta_logo)
            self.logo_image = ctk.CTkImage(light_image=logo_pil, dark_image=logo_pil, size=(110, 140))
            self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="", image=self.logo_image)
            self.logo_label.pack(pady=(20, 10))
        except:
            ctk.CTkLabel(self.sidebar_frame, text="ESC. ARAUCANÍA", font=("Arial", 18, "bold"), text_color=COLOR_AMARILLO_ESCUELA).pack(pady=20)

        ctk.CTkLabel(self.sidebar_frame, text="KoaLink", font=("Arial", 24, "bold"), text_color=COLOR_AMARILLO_ESCUELA).pack(pady=(0, 20))

        # Botones de Navegación
        self.crear_boton_menu("🏠 Inicio / Consulta", self.mostrar_inicio)
        self.crear_boton_menu("➕ Nuevo Ingreso", self.mostrar_alta_equipo)
        self.crear_boton_menu("📋 Gestión Inventario", self.mostrar_inventario_total)
        self.crear_boton_menu("📤 Préstamo Rápido", self.mostrar_prestamos)
        self.crear_boton_menu("📥 Devolución", self.mostrar_devoluciones)

        # Botón de Reporte (Abajo)
        self.btn_reporte = ctk.CTkButton(self.sidebar_frame, text="📊 Reporte Jefatura", 
                                         fg_color="#1f538d", hover_color="#3374c2",
                                         command=self.generar_reporte_excel)
        self.btn_reporte.pack(side="bottom", pady=30, padx=20, fill="x")

        # --- PANEL CENTRAL ---
        self.main_frame = ctk.CTkFrame(self, corner_radius=15)
        self.main_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")

        self.mostrar_inicio()

    def crear_boton_menu(self, texto, comando):
        btn = ctk.CTkButton(self.sidebar_frame, text=texto, command=comando,
                             fg_color="transparent", text_color=COLOR_BLANCO, 
                             hover_color="#333333", anchor="w", height=40)
        btn.pack(pady=5, padx=20, fill="x")

    def limpiar_panel(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    # --- VISTA: INICIO ---
    def mostrar_inicio(self):
        self.limpiar_panel()
        ctk.CTkLabel(self.main_frame, text="Buscador de Equipos", font=("Arial", 22, "bold"), text_color=COLOR_AMARILLO_ESCUELA).pack(pady=(60, 10))
        
        self.entry_consulta = ctk.CTkEntry(self.main_frame, placeholder_text="Escanee código para consultar...", 
                                             width=400, height=45, border_color=COLOR_AMARILLO_ESCUELA)
        self.entry_consulta.pack(pady=20)
        self.entry_consulta.bind("<Return>", self.consultar_item)
        self.entry_consulta.focus_set()

    def consultar_item(self, event):
        codigo = self.entry_consulta.get()
        if not codigo: return

        # 1. Limpiar cualquier resultado anterior si existe (buscamos el frame_resultados)
        if hasattr(self, 'frame_resultados'):
            self.frame_resultados.destroy()

        # 2. Consultar a la Base de Datos
        info = database.obtener_info_individual(codigo)

        # 3. Crear el contenedor de resultados
        self.frame_resultados = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.frame_resultados.pack(pady=20, fill="x", padx=40)

        if info["encontrado"]:
            # --- Diseño de la Ficha del Artículo ---
            
            # Título: Nombre del Equipo
            ctk.CTkLabel(self.frame_resultados, text=info["nombre"], 
                         font=("Arial", 22, "bold"), text_color=COLOR_AMARILLO_ESCUELA).pack(anchor="w", pady=(0,15))

            # Definimos colores según el estado
            color_estado = "#32a852" if info["estado"] == "Disponible" else "#f5a623" # Verde o Naranja

            # Reutilizamos función auxiliar para filas de datos
            self._crear_fila_info(self.frame_resultados, "Categoría:", info["categoria"])
            self._crear_fila_info(self.frame_resultados, "Estado Actual:", info["estado"], color_valor=color_estado)
            self._crear_fila_info(self.frame_resultados, "Ubicación Base:", info["ubicacion_base"])
            
            # Línea divisoria si está prestado
            if info["estado"] == "Prestado":
                ctk.CTkFrame(self.frame_resultados, height=2, fg_color="#444444").pack(fill="x", pady=15)
                ctk.CTkLabel(self.frame_resultados, text="Detalles del Préstamo Activo", 
                             font=("Arial", 14, "italic"), text_color=COLOR_GRIS_VENTANA).pack(anchor="w")
                
                self._crear_fila_info(self.frame_resultados, "Responsable:", info["quien_lo_tiene"])
                self._crear_fila_info(self.frame_resultados, "Ubicación de Uso:", info["donde_esta"])
                self._crear_fila_info(self.frame_resultados, "Prestado desde:", info["desde_cuando"])

        else:
            # Mensaje de error si no existe
            ctk.CTkLabel(self.frame_resultados, text=f"❌ El código '{codigo}'\nno está registrado en el inventario.", 
                         font=("Arial", 16), text_color="#a83232").pack(pady=20)

        # Limpiar campo y mantener foco
        self.entry_consulta.delete(0, 'end')
        self.entry_consulta.focus_set()

    def _crear_fila_info(self, master, etiqueta, valor, color_valor="white"):
        """Función auxiliar para crear filas de datos uniformes (Etiqueta: Valor)."""
        f = ctk.CTkFrame(master, fg_color="transparent")
        f.pack(fill="x", pady=2)
        ctk.CTkLabel(f, text=etiqueta, font=("Arial", 13, "bold"), text_color=COLOR_GRIS_VENTANA, width=120, anchor="w").pack(side="left")
        ctk.CTkLabel(f, text=valor, font=("Arial", 13), text_color=color_valor, anchor="w").pack(side="left", padx=10)

    # --- VISTA: ALTA ---
    def mostrar_alta_equipo(self):
        self.limpiar_panel()
        ctk.CTkLabel(self.main_frame, text="Registro de Inventario y Stock", 
                     font=("Arial", 24, "bold"), text_color=COLOR_AMARILLO_ESCUELA).pack(pady=20)

        # Contenedor central para el formulario
        form_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        form_frame.pack(pady=10)

        # --- CATEGORÍA (Mover arriba para que defina el comportamiento) ---
        ctk.CTkLabel(form_frame, text="Categoría del Bien:").grid(row=0, column=0, padx=20, pady=5, sticky="w")
        self.cat_var = ctk.StringVar(value="Tablet")
        self.combo_cat = ctk.CTkComboBox(form_frame, 
                                         values=["Tablet", "Notebook", "Libro", "Impresora", "Material Didáctico"], 
                                         variable=self.cat_var, width=300,
                                         command=self.ajustar_interfaz_por_categoria)
        self.combo_cat.grid(row=0, column=1, pady=5)

        # --- CÓDIGO (Automático) ---
        ctk.CTkLabel(form_frame, text="Código de Inventario:").grid(row=1, column=0, padx=20, pady=5, sticky="w")
        self.ent_cod = ctk.CTkEntry(form_frame, width=300, state="readonly", fg_color="#2b2b2b")
        self.ent_cod.grid(row=1, column=1, pady=5)

        # --- NOMBRE ---
        ctk.CTkLabel(form_frame, text="Nombre / Título:").grid(row=2, column=0, padx=20, pady=5, sticky="w")
        self.ent_nom = ctk.CTkEntry(form_frame, placeholder_text="Ej: Papelucho / Lenovo K10", width=300)
        self.ent_nom.grid(row=2, column=1, pady=5)

        # --- CANTIDAD (STOCK) ---
        ctk.CTkLabel(form_frame, text="Cantidad / Unidades:").grid(row=3, column=0, padx=20, pady=5, sticky="w")
        self.ent_cant = ctk.CTkEntry(form_frame, width=300)
        self.ent_cant.insert(0, "1")
        self.ent_cant.grid(row=3, column=1, pady=5)

        # --- UBICACIÓN ---
        ctk.CTkLabel(form_frame, text="Ubicación Base:").grid(row=4, column=0, padx=20, pady=5, sticky="w")
        self.ubi_var = ctk.StringVar(value="Sala de Informática")
        ctk.CTkComboBox(form_frame, values=["Sala de Informática", "Biblioteca", "Bodega", "Oficina"], 
                        variable=self.ubi_var, width=300).grid(row=4, column=1, pady=5)

        # Botón Guardar
        ctk.CTkButton(self.main_frame, text="📥 Registrar en Sistema", 
                      fg_color="#1e7e34", hover_color="#155d27",
                      command=self.ejecutar_guardado_completo, height=45, width=250).pack(pady=40)

        # Inicializar el primer código
        self.actualizar_codigo_sugerido("Tablet")

    def ajustar_interfaz_por_categoria(self, seleccion):
        """Cambia el foco y el código según lo que se va a ingresar."""
        self.actualizar_codigo_sugerido(seleccion)
        
        # Si es libro o material, ponemos el foco en cantidad y sugerimos que puede ser > 1
        if seleccion in ["Libro", "Material Didáctico"]:
            self.ent_cant.configure(fg_color="#3d3d3d") # Un color que resalte que es editable
        else:
            self.ent_cant.delete(0, 'end')
            self.ent_cant.insert(0, "1")
            self.ent_cant.configure(fg_color="#2b2b2b")

    def actualizar_codigo_sugerido(self, seleccion):
        """Genera y muestra el código automáticamente al cambiar categoría."""
        nuevo_cod = database.generar_siguiente_codigo(seleccion)
        self.ent_cod.configure(state="normal") # Desbloquear para escribir
        self.ent_cod.delete(0, 'end')
        self.ent_cod.insert(0, nuevo_cod)
        self.ent_cod.configure(state="readonly") # Volver a bloquear

    def ejecutar_guardado_completo(self):
        cod = self.ent_cod.get()
        nom = self.ent_nom.get()
        cat = self.cat_var.get()
        ubi = self.ubi_var.get()
        
        try:
            cant = int(self.ent_cant.get())
            if cant <= 0: raise ValueError
        except ValueError:
            messagebox.showwarning("Error de Cantidad", "Por favor ingresa un número válido (mayor a 0).")
            return

        if not nom:
            messagebox.showwarning("Faltan Datos", "El nombre del artículo es obligatorio.")
            return

        # Llamada a database.py (asegúrate de que acepte el parámetro 'cantidad')
        if database.guardar_item_db(cod, nom, cat, ubi, cant):
            messagebox.showinfo("Éxito", f"Registrado: {nom}\nStock: {cant} unidades.")
            self.mostrar_alta_equipo() # Limpiar para el siguiente
        else:
            messagebox.showerror("Error", "No se pudo guardar en la base de datos.")
        
    def guardar_item_db(self):
        c, n, cat, u = self.ent_cod.get(), self.ent_nom.get(), self.cat_var.get(), self.ubi_var.get()
        if c and n:
            if database.registrar_item(c, n, cat, u):
                messagebox.showinfo("Éxito", f"Articulo {c} guardado.")
                self.mostrar_alta_equipo()
            else:
                messagebox.showerror("Error", "El código ya existe.")
        else:
            messagebox.showwarning("Atención", "Complete los campos obligatorios.")

    # --- VISTA: GESTIÓN TOTAL ---
    def mostrar_inventario_total(self):
        self.limpiar_panel()
        
        # Frame superior para Título y Botón PDF
        header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(header_frame, text="Gestión de Inventario", 
                     font=("Arial", 22, "bold"), text_color=COLOR_AMARILLO_ESCUELA).pack(side="left")

        # BOTÓN GENERAR PDF
        btn_pdf = ctk.CTkButton(header_frame, text="📄 Imprimir Etiquetas", 
                             fg_color="#d35400", command=self.accion_imprimir_etiquetas)
        btn_pdf.pack(side="right", padx=10)

        # --- CONTENEDOR DE FILTROS ---
        self.frame_filtros = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.frame_filtros.pack(fill="x", padx=20, pady=5)

        # Filtro Categoría
        ctk.CTkLabel(self.frame_filtros, text="Categoría:").pack(side="left", padx=5)
        self.f_cat = ctk.CTkComboBox(self.frame_filtros, values=["Todos", "Tablet", "Notebook", "Libro"], 
                                     command=lambda _: self.actualizar_tabla_inventario())
        self.f_cat.pack(side="left", padx=5)

        # Filtro Estado
        ctk.CTkLabel(self.frame_filtros, text="Ver:").pack(side="left", padx=5)
        self.f_est = ctk.CTkComboBox(self.frame_filtros, values=["Activos", "Inactivos", "Todos"], 
                                     command=lambda _: self.actualizar_tabla_inventario())
        self.f_est.pack(side="left", padx=5)

        btn_filtrar = ctk.CTkButton(self.frame_filtros, text="🔍 Filtrar", width=80, 
                                     fg_color=COLOR_AMARILLO_ESCUELA, text_color="black",
                                     command=self.actualizar_tabla_inventario)
        btn_filtrar.pack(side="left", padx=15)

        # --- CONTENEDOR DE TABLA ---
        self.tabla_container = ctk.CTkScrollableFrame(self.main_frame, fg_color="transparent")
        self.tabla_container.pack(fill="both", expand=True, padx=10, pady=10)

        self.actualizar_tabla_inventario()

    def accion_imprimir_etiquetas(self):
        exito, msj = database.generar_pdf_etiquetas_reales1607611
        1607611
        1607611
        1607611
        1607611
        ()
        if not exito:
            messagebox.showerror("Error", msj)

    def actualizar_tabla_inventario(self):
        # Limpiar tabla actual
        for widget in self.tabla_container.winfo_children():
            widget.destroy()

        # --- ENCABEZADOS (Añadimos CANTIDAD) ---
        encabezados = ["CÓDIGO", "NOMBRE", "CATEGORÍA", "ESTADO", "UBICACIÓN", "CANT.", "ACCIONES"]
        for i, texto in enumerate(encabezados):
            ctk.CTkLabel(self.tabla_container, text=texto, font=("Arial", 12, "bold")).grid(row=0, column=i, padx=10, pady=5)

        # Obtener datos de la DB
        articulos = database.obtener_articulos_inventario(self.f_cat.get(), self.f_est.get())

        for row_idx, art in enumerate(articulos, start=1):
            # art[0]=cod, art[1]=nom, art[2]=cat, art[3]=est, art[4]=ubi, art[5]=cant
            
            ctk.CTkLabel(self.tabla_container, text=art[0]).grid(row=row_idx, column=0, padx=10)
            ctk.CTkLabel(self.tabla_container, text=art[1]).grid(row=row_idx, column=1, padx=10)
            ctk.CTkLabel(self.tabla_container, text=art[2]).grid(row=row_idx, column=2, padx=10)
            ctk.CTkLabel(self.tabla_container, text=art[3]).grid(row=row_idx, column=3, padx=10)
            ctk.CTkLabel(self.tabla_container, text=art[4]).grid(row=row_idx, column=4, padx=10)
            
            # NUEVA COLUMNA: CANTIDAD
            ctk.CTkLabel(self.tabla_container, text=str(art[5]), font=("Arial", 12, "bold"), 
                         text_color=COLOR_AMARILLO_ESCUELA).grid(row=row_idx, column=5, padx=10)

            # Botones de Acción (estos se mueven a la columna 6)
            btn_edit = ctk.CTkButton(self.tabla_container, text="✎", width=30, command=lambda a=art: self.editar_item(a))
            btn_edit.grid(row=row_idx, column=6, padx=2, pady=2)

    def ejecutar_baja_logica(self, codigo):
        if messagebox.askyesno("Confirmar", f"¿Desea marcar el equipo {codigo} como INACTIVO?\nSeguirá apareciendo en reportes pero no podrá prestarse."):
            if database.dar_de_baja_logica(codigo):
                self.actualizar_tabla_inventario()

    def dar_de_baja(self, codigo):
        if messagebox.askyesno("Baja", f"¿Dar de baja definitiva al equipo {codigo}?"):
            # Lógica para cambiar estado a 'Baja' en database.py podría ir aquí
            messagebox.showinfo("Info", f"Equipo {codigo} marcado para baja.")
            self.mostrar_inventario_total()

    # --- VISTA: PRÉSTAMOS ---
    def mostrar_prestamos(self):
        self.limpiar_panel()
        self.carrito_prestamo = []
        
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(1, weight=1)
        
        # --- COLUMNA 1: BÚSQUEDA Y FILTROS ---
        frame_seleccion = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        frame_seleccion.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        ctk.CTkLabel(frame_seleccion, text="🔍 Buscar Equipos", font=("Arial", 16, "bold"), text_color=COLOR_AMARILLO_ESCUELA).pack(pady=5)
        
        # Frame para agrupar Buscador + Categoría
        frame_filtros_p = ctk.CTkFrame(frame_seleccion, fg_color="transparent")
        frame_filtros_p.pack(pady=5, fill="x", padx=20)

        # Buscador por texto
        self.entry_busqueda_p = ctk.CTkEntry(frame_filtros_p, placeholder_text="Nombre o código...", width=200)
        self.entry_busqueda_p.pack(side="left", padx=5, expand=True, fill="x")
        self.entry_busqueda_p.bind("<KeyRelease>", lambda e: self.actualizar_lista_disponibles())

        # Filtro por Categoría
        self.cat_filtro_p = ctk.CTkComboBox(frame_filtros_p, values=["Todas", "Tablet", "Notebook", "Libro", "Material Didáctico"], 
                                            width=140, command=lambda _: self.actualizar_lista_disponibles())
        self.cat_filtro_p.set("Todas")
        self.cat_filtro_p.pack(side="left", padx=5)

        # Lista de disponibles
        self.scroll_disponibles = ctk.CTkScrollableFrame(frame_seleccion, width=350, height=450)
        self.scroll_disponibles.pack(fill="both", expand=True, pady=10, padx=20)

        # --- COLUMNA 2: FORMULARIO Y CONFIRMACIÓN ---
        frame_confirmar = ctk.CTkFrame(self.main_frame)
        frame_confirmar.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        ctk.CTkLabel(frame_confirmar, text="📋 Resumen de Préstamo", font=("Arial", 16, "bold")).pack(pady=10)

        # Tipo de Solicitante
        self.tipo_solicitante = ctk.CTkSegmentedButton(frame_confirmar, values=["Funcionario", "Alumno"], 
                                                      selected_color=COLOR_AMARILLO_ESCUELA, text_color_disabled="black")
        self.tipo_solicitante.set("Funcionario")
        self.tipo_solicitante.pack(pady=5)

        self.ent_responsable = ctk.CTkEntry(frame_confirmar, placeholder_text="Nombre del Solicitante", width=300)
        self.ent_responsable.pack(pady=5)

        self.ent_destino = ctk.CTkEntry(frame_confirmar, placeholder_text="Ubicación/Sala destino", width=300)
        self.ent_destino.pack(pady=5)

        # Lista de lo que se va agregando (El Carrito)
        ctk.CTkLabel(frame_confirmar, text="Equipos seleccionados:").pack(pady=(10,0))
        self.frame_lista_carrito = ctk.CTkScrollableFrame(frame_confirmar, height=200, fg_color="#2b2b2b")
        self.frame_lista_carrito.pack(fill="x", padx=20, pady=10)

        self.btn_confirmar_todo = ctk.CTkButton(frame_confirmar, text="CONFIRMAR PRÉSTAMO", 
                                                fg_color="green", font=("Arial", 14, "bold"),
                                                command=self.finalizar_prestamo_masivo)
        self.btn_confirmar_todo.pack(pady=20, fill="x", padx=40)

        self.actualizar_lista_disponibles()

        self.entry_busqueda_p.focus_set()

    def actualizar_lista_disponibles(self):
        # Limpiar lista anterior
        for widget in self.scroll_disponibles.winfo_children():
            widget.destroy()

        termino = self.entry_busqueda_p.get().lower()
        categoria_sel = self.cat_filtro_p.get()
        
        todos = database.obtener_todo_el_inventario()
        
        # Lógica de filtrado combinada
        filtrados = []
        for i in todos:
            # Condición 1: Que esté Disponible
            if i[3] == "Disponible":
                # Condición 2: Que el código no esté ya en el carrito
                if i[0] not in [c[0] for c in self.carrito_prestamo]:
                    # Condición 3: Filtro por texto (nombre o código)
                    match_texto = termino in i[0].lower() or termino in i[1].lower()
                    # Condición 4: Filtro por categoría
                    match_cat = (categoria_sel == "Todas" or i[2] == categoria_sel)
                    
                    if match_texto and match_cat:
                        filtrados.append(i)

        # Crear los botones en la lista
        for item in filtrados:
            btn = ctk.CTkButton(self.scroll_disponibles, 
                                text=f"{item[1]} \n({item[0]})", 
                                font=("Arial", 12),
                                fg_color="#333333", 
                                hover_color="#444444",
                                anchor="w", 
                                height=50,
                                command=lambda i=item: self.agregar_al_carrito(i))
            btn.pack(fill="x", pady=3, padx=5)

    def agregar_al_carrito(self, item):
        self.carrito_prestamo.append(item)
        self.refrescar_vista_carrito()
        self.actualizar_lista_disponibles()

    def refrescar_vista_carrito(self):
        for widget in self.frame_lista_carrito.winfo_children():
            widget.destroy()
        
        for i, item in enumerate(self.carrito_prestamo):
            f = ctk.CTkFrame(self.frame_lista_carrito, fg_color="transparent")
            f.pack(fill="x")
            ctk.CTkLabel(f, text=f"• {item[1]}", font=("Arial", 12)).pack(side="left")
            ctk.CTkButton(f, text="❌", width=20, height=20, fg_color="red", 
                          command=lambda idx=i: self.quitar_del_carrito(idx)).pack(side="right", padx=5)

    def quitar_del_carrito(self, indice):
        self.carrito_prestamo.pop(indice)
        self.refrescar_vista_carrito()
        self.actualizar_lista_disponibles()

    def cargar_codigo_manual(self, codigo):
        self.ent_scan.delete(0, 'end')
        self.ent_scan.insert(0, codigo)
        self.proceso_prestamo(None) # Ejecuta el préstamo como si hubieras presionado Enter

    def finalizar_prestamo_masivo(self):
        responsable = self.ent_responsable.get()
        destino = self.ent_destino.get()
        tipo = self.tipo_solicitante.get()

        if not responsable or not destino or not self.carrito_prestamo:
            messagebox.showwarning("Atención", "Debe ingresar responsable, destino y al menos un equipo.")
            return

        if messagebox.askyesno("Confirmar", f"¿Registrar préstamo de {len(self.carrito_prestamo)} equipos a {responsable}?"):
            errores = 0
            for item in self.carrito_prestamo:
                # Modificamos el nombre para guardar el tipo (Funcionario/Alumno) si quieres
                nombre_final = f"[{tipo}] {responsable}"
                exito, msj = database.registrar_prestamo_masivo(item[0], nombre_final, destino)
                if not exito: errores += 1
            
            if errores == 0:
                messagebox.showinfo("Éxito", "Todos los equipos han sido prestados correctamente.")
                self.mostrar_prestamos() # Reiniciar pantalla
            else:
                messagebox.showerror("Error", f"Hubo problemas con {errores} equipos.")

    def proceso_prestamo(self, event):
        codigo = self.ent_scan.get()
        responsable = self.ent_res.get()
        destino = self.ent_dest.get()

        if not codigo or not responsable:
            messagebox.showwarning("Atención", "Complete el responsable y escanee un código.")
            return

        # Consultamos qué tipo de artículo es
        item = database.obtener_item_base(codigo)
        if not item:
            messagebox.showerror("Error", "El código no existe en el sistema.")
            return

        # item[2] es la CATEGORÍA, item[4] es la CANTIDAD actual en DB
        if item[2] in ["Libro", "Material Didáctico"]:
            self.abrir_modal_cantidad(item, responsable, destino)
        else:
            # Préstamo normal de 1 unidad (Tablets/Notebooks)
            exito, msj = database.registrar_prestamo(codigo, responsable, destino)
            self.finalizar_escaneo(exito, msj)

    def abrir_modal_cantidad(self, item, responsable, destino):
        """Ventana emergente para elegir cuántas unidades prestar."""
        modal = ctk.CTkToplevel(self)
        modal.title("Cantidad de Préstamo")
        modal.geometry("300x250")
        modal.attributes('-topmost', True)
        modal.grab_set()
        
        # Centrar modal
        x = (self.winfo_screenwidth() // 2) - 150
        y = (self.winfo_screenheight() // 2) - 125
        modal.geometry(f"+{x}+{y}")

        ctk.CTkLabel(modal, text=f"{item[1]}", font=("Arial", 14, "bold")).pack(pady=10)
        ctk.CTkLabel(modal, text=f"Stock disponible: {item[4]}").pack()

        ent_cant_prestar = ctk.CTkEntry(modal, placeholder_text="¿Cuántos?", width=100)
        ent_cant_prestar.insert(0, "1")
        ent_cant_prestar.pack(pady=20)
        ent_cant_prestar.focus_set()

        def confirmar():
            try:
                cant = int(ent_cant_prestar.get())
                exito, msj = database.registrar_prestamo_stock(item[0], responsable, destino, cant)
                modal.destroy()
                self.finalizar_escaneo(exito, msj)
            except ValueError:
                messagebox.showerror("Error", "Ingrese un número válido.")

        ctk.CTkButton(modal, text="Confirmar Préstamo", command=confirmar).pack(pady=10)

    def finalizar_escaneo(self, exito, msj):
        """Limpia el campo de escaneo y muestra el resultado en el log."""
        color = "green" if exito else "red"
        ctk.CTkLabel(self.log_prestamo, text=f"• {msj}", text_color=color).pack(anchor="w")
        self.ent_scan.delete(0, 'end')
        self.ent_scan.focus_set()

    # --- VISTA: DEVOLUCIÓN ---
    def mostrar_devoluciones(self):
        self.limpiar_panel()
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(1, weight=1)

        # --- COLUMNA IZQUIERDA: ESCANEO Y LOG ---
        frame_izq = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        frame_izq.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)

        ctk.CTkLabel(frame_izq, text="Recepción Rápida", font=("Arial", 20, "bold"), text_color=COLOR_AMARILLO_ESCUELA).pack(pady=10)
        
        ctk.CTkLabel(frame_izq, text="¿Dónde se guarda físicamente?").pack()
        self.ubi_retorno = ctk.CTkComboBox(frame_izq, values=["Sala de Informática", "Biblioteca", "Bodega"], width=300)
        self.ubi_retorno.pack(pady=10)

        self.ent_scan_dev = ctk.CTkEntry(frame_izq, placeholder_text="Escanee aquí para devolver...", 
                                         width=300, height=45, border_color="orange")
        self.ent_scan_dev.pack(pady=10)
        self.ent_scan_dev.bind("<Return>", self.proceso_devolucion)
        self.ent_scan_dev.focus_set()

        # Historial de la sesión actual de devolución
        self.log_recepcion = ctk.CTkScrollableFrame(frame_izq, height=300, label_text="Recibidos en esta sesión")
        self.log_recepcion.pack(fill="both", expand=True, pady=10)

        # --- COLUMNA DERECHA: LISTA DE EQUIPOS FUERA (PRÉSTAMOS ACTIVOS) ---
        frame_der = ctk.CTkFrame(self.main_frame)
        frame_der.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

        ctk.CTkLabel(frame_der, text="Equipos actualmente prestados", font=("Arial", 16, "bold")).pack(pady=10)
        
        # Buscador para la lista de prestados
        self.entry_busqueda_dev = ctk.CTkEntry(frame_der, placeholder_text="Filtrar por docente o equipo...", width=250)
        self.entry_busqueda_dev.pack(pady=5)
        self.entry_busqueda_dev.bind("<KeyRelease>", lambda e: self.actualizar_lista_prestados())

        self.scroll_prestados = ctk.CTkScrollableFrame(frame_der)
        self.scroll_prestados.pack(fill="both", expand=True, padx=10, pady=10)

        self.actualizar_lista_prestados()

    def actualizar_lista_prestados(self):
        # Limpiar lista
        for widget in self.scroll_prestados.winfo_children():
            widget.destroy()

        termino = self.entry_busqueda_dev.get().lower()
        # Obtenemos datos combinados de la DB (articulos + movimientos activos)
        # Necesitaremos una pequeña función en database.py para esto
        prestados = database.obtener_prestamos_activos() 

        filtrados = [p for p in prestados if termino in p[1].lower() or termino in p[5].lower()]

        for p in filtrados:
            # p[0]=codigo, p[1]=nombre_equipo, p[5]=responsable
            btn = ctk.CTkButton(self.scroll_prestados, 
                                text=f"{p[1]}\n📍 {p[5]}", 
                                fg_color="#333333", hover_color="#f5a623",
                                anchor="w", height=60,
                                command=lambda c=p[0]: self.devolver_manual(c))
            btn.pack(fill="x", pady=3, padx=5)

    def devolver_manual(self, codigo):
        self.ent_scan_dev.delete(0, 'end')
        self.ent_scan_dev.insert(0, codigo)
        self.proceso_devolucion(None)

    def proceso_devolucion(self, event):
        cod = self.ent_scan_dev.get()
        ubi = self.ubi_retorno.get()
        
        if not cod: return

        exito, msj = database.registrar_devolucion(cod, ubi)
        
        # Feedback visual en el LOG de la izquierda
        color = "green" if exito else "red"
        ctk.CTkLabel(self.log_recepcion, text=f"• {cod}: {msj}", text_color=color).pack(anchor="w", padx=10)
        
        # LIMPIEZA Y ACTUALIZACIÓN
        self.ent_scan_dev.delete(0, 'end')
        self.actualizar_lista_prestados() # <--- Crucial para ver el cambio al instante
        self.ent_scan_dev.focus_set()

    # --- REPORTE EXCEL ---
    def generar_reporte_excel(self):
        try:
            if not os.path.exists('reportes'):
                os.makedirs('reportes')
            
            df = database.obtener_datos_para_reporte()
            fecha = datetime.now().strftime("%Y-%m-%d_%H-%M")
            nombre_archivo = f"reportes/Inventario_Araucania_{fecha}.xlsx"
            
            df.to_excel(nombre_archivo, index=False)
            messagebox.showinfo("Reporte OK", f"Reporte generado en:\n{nombre_archivo}")
            os.startfile('reportes')
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo crear el Excel: {e}")

    def abrir_ventana_edicion(self, datos_fila):
        """Abre la ventana de edición cargando los datos reales de la DB."""
        
        # 1. Obtener la información real (Ubicación Base) antes de abrir
        datos_reales = database.obtener_item_base(datos_fila[0])
        if not datos_reales:
            messagebox.showerror("Error", "No se encontró la información del equipo.")
            return

        # 2. Crear y Centrar Ventana (Lógica anterior)
        self.edit_window = ctk.CTkToplevel(self)
        self.edit_window.title(f"Editar Equipo: {datos_reales[0]}")
        
        ancho_modal, alto_modal = 450, 550
        x = (self.winfo_screenwidth() / 2) - (ancho_modal / 2)
        y = (self.winfo_screenheight() / 2) - (alto_modal / 2)
        self.edit_window.geometry(f"{ancho_modal}x{alto_modal}+{int(x)}+{int(y)}")
        
        self.edit_window.attributes('-topmost', True)
        self.edit_window.grab_set()

        # --- CONTENIDO ---
        ctk.CTkLabel(self.edit_window, text=f"Modificando: {datos_reales[0]}", 
                     font=("Arial", 18, "bold"), text_color=COLOR_AMARILLO_ESCUELA).pack(pady=(30, 10))

        # Estado visual (Informativo)
        color_est = "#32a852" if datos_reales[3] == "Disponible" else "#f5a623"
        ctk.CTkLabel(self.edit_window, text=f"Estado actual: {datos_reales[3]}", text_color=color_est).pack()

        # Input Nombre
        ctk.CTkLabel(self.edit_window, text="Nombre / Descripción:").pack(pady=(20,0))
        ent_nom = ctk.CTkEntry(self.edit_window, width=320)
        ent_nom.insert(0, datos_reales[1]) # Nombre real
        ent_nom.pack(pady=5)

        # Combo Categoría
        ctk.CTkLabel(self.edit_window, text="Categoría:").pack(pady=(10,0))
        cat_var = ctk.StringVar(value=datos_reales[2])
        ctk.CTkComboBox(self.edit_window, values=["Tablet", "Notebook", "Libro", "Impresora", "Material Didáctico"], 
                        variable=cat_var, width=320).pack(pady=5)

        # Combo Ubicación BASE (Aquí está el cambio clave)
        ctk.CTkLabel(self.edit_window, text="Ubicación Base (Hogar del equipo):").pack(pady=(10,0))
        ubi_var = ctk.StringVar(value=datos_reales[4]) # Ubicación real de la tabla articulos
        ctk.CTkComboBox(self.edit_window, values=["Sala de Informática", "Biblioteca", "Bodega", "Oficina"], 
                        variable=ubi_var, width=320).pack(pady=5)

        # Botón Guardar
        def guardar():
            if database.actualizar_item_db(datos_reales[0], ent_nom.get(), cat_var.get(), ubi_var.get()):
                messagebox.showinfo("Éxito", "Cambios guardados correctamente.", parent=self.edit_window)
                self.edit_window.destroy()
                self.actualizar_tabla_inventario()
            else:
                messagebox.showerror("Error", "No se pudo actualizar.", parent=self.edit_window)

        ctk.CTkButton(self.edit_window, text="Guardar Cambios", fg_color="green", 
                      command=guardar, height=45).pack(pady=40)

if __name__ == "__main__":
    app = AppKoaLink()
    app.mainloop()