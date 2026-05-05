from tkinter import messagebox
import customtkinter as ctk
import database

# Importar las nuevas utilidades
from config import Config
from utils import center_window, validate_not_empty, validate_numeric, show_error, show_info, show_question
from constants import Constants
from exceptions import ValidationError, LoanError
from logger import logger


class PrestamosModule(ctk.CTkFrame):
    """Frame del módulo de préstamos.

    Contiene la lógica de selección de artículos, carrito de préstamo y la
    confirmación de préstamos múltiples.
    """

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.lista_items_seleccionados = []
        self.ent_busqueda_p = None
        self.tabla_p = None
        self.carrito_lista = None
        self.combo_tipo_p = None
        self.combo_curso_p = None
        self.ent_resp_p = None
        self.ent_dest_p = None

    def clear(self):
        """Elimina todos los widgets del módulo."""
        for widget in self.winfo_children():
            widget.destroy()

    def show_prestamos(self):
        """Muestra la vista de préstamos con buscador y carrito."""
        self.clear()
        self.lista_items_seleccionados = []

        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(0, weight=1)

        izq_frame = ctk.CTkFrame(self, fg_color="#1d1d1d", corner_radius=15)
        izq_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        ctk.CTkLabel(izq_frame, text="🔍 Buscar en Inventario Disponible", font=("Arial", 18, "bold"), text_color="#f1c40f").pack(pady=10)

        self.ent_busqueda_p = ctk.CTkEntry(izq_frame, placeholder_text="Escriba nombre, código o categoría...")
        self.ent_busqueda_p.pack(fill="x", padx=20, pady=5)
        self.ent_busqueda_p.bind("<KeyRelease>", lambda e: self.controller.busqueda_inteligente(e, self.refrescar_tabla_prestamos))

        self.tabla_p = ctk.CTkScrollableFrame(izq_frame, fg_color="transparent")
        self.tabla_p.pack(fill="both", expand=True, padx=10, pady=10)

        der_frame = ctk.CTkFrame(self, corner_radius=15)
        der_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        resp_frame = ctk.CTkFrame(der_frame, fg_color="transparent")
        resp_frame.pack(fill="x", pady=10, padx=10)

        ctk.CTkLabel(resp_frame, text="👤 Datos del Responsable", font=("Arial", 16, "bold"), text_color="#f1c40f").pack(pady=(0,10))

        def al_cambiar_tipo(seleccion):
            if seleccion == "Estudiante":
                self.combo_curso_p.configure(state="normal")
                self.combo_curso_p.set("Seleccione un curso...")
            else:
                self.combo_curso_p.set("")
                self.combo_curso_p.configure(state="disabled")

        self.combo_tipo_p = ctk.CTkComboBox(resp_frame, values=["Estudiante", "Funcionario"], width=300, command=al_cambiar_tipo)
        self.combo_tipo_p.set("Estudiante")
        self.combo_tipo_p.pack(pady=5)

        self.ent_resp_p = ctk.CTkEntry(resp_frame, placeholder_text="Nombre Completo del Responsable", width=300)
        self.ent_resp_p.pack(pady=5)

        lista_cursos = ["1ro", "2do", "3ro", "4to", "5to", "6to", "7mo", "8vo"]
        self.combo_curso_p = ctk.CTkComboBox(resp_frame, values=lista_cursos, width=300)
        self.combo_curso_p.pack(pady=5)

        self.ent_dest_p = ctk.CTkEntry(resp_frame, placeholder_text="Sala o Oficina de Destino", width=300)
        self.ent_dest_p.pack(pady=5)

        al_cambiar_tipo("Estudiante")

        ctk.CTkFrame(der_frame, height=2, fg_color="#333333").pack(fill="x", padx=10, pady=15)

        carrito_frame = ctk.CTkFrame(der_frame, fg_color="transparent")
        carrito_frame.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(carrito_frame, text="🛒 Elementos Seleccionados", font=("Arial", 16, "bold")).pack(pady=(0,10))

        self.carrito_lista = ctk.CTkScrollableFrame(carrito_frame, fg_color="#1a1a1a", height=200)
        self.carrito_lista.pack(fill="both", expand=True, padx=5, pady=5)

        ctk.CTkButton(der_frame, text="📤 CONFIRMAR PRÉSTAMO TOTAL", fg_color="#27ae60", hover_color="#2ecc71", font=("Arial", 14, "bold"), height=45, command=self.confirmar_todo_el_prestamo).pack(pady=20, padx=20, fill="x")

        self.refrescar_tabla_prestamos()

    def confirmar_todo_el_prestamo(self):
        """Valida los datos y registra el préstamo múltiple en la base de datos."""
        resp_base = self.ent_resp_p.get().strip()
        dest = self.ent_dest_p.get().strip()
        tipo = self.combo_tipo_p.get()

        if tipo == "Estudiante":
            curso = self.combo_curso_p.get()
            if not curso or curso == "Seleccione un curso...":
                messagebox.showwarning("Faltan Datos", "Debe seleccionar el curso del estudiante.")
                return
            resp_final = f"{resp_base} (Curso: {curso})"
        else:
            resp_final = resp_base

        if not resp_base or not dest or not self.lista_items_seleccionados:
            messagebox.showwarning("Atención", "Complete los datos del responsable y agregue elementos al carrito.")
            return

        exito, msj = database.registrar_prestamo_multiple(resp_final, dest, tipo, self.lista_items_seleccionados)
        if exito:
            messagebox.showinfo("Éxito", msj)
            self.show_prestamos()
        else:
            messagebox.showerror("Error", msj)

    def editar_info_prestamo(self, id_prestamo, equipo, resp_actual, dest_actual, tipo_actual, cant, fecha):
        """Abre un modal para editar la información de un préstamo activo."""
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
                self.controller.current_view.actualizar_tabla_historial()
            else:
                messagebox.showerror("Error", msj)

        ctk.CTkButton(dialogo, text="💾 Guardar Cambios", fg_color="#27ae60", hover_color="#2ecc71", command=confirmar).pack(pady=20)

    def refrescar_tabla_prestamos(self):
        """Filtra y muestra los artículos disponibles para préstamo."""
        for w in self.tabla_p.winfo_children():
            w.destroy()

        busqueda = self.ent_busqueda_p.get().lower()
        items = database.obtener_articulos_inventario_completo("Todos")

        ctk.CTkLabel(self.tabla_p, text="Resultados de búsqueda:", font=("Arial", 11, "italic"), text_color="#aaaaaa").pack(anchor="w", padx=10, pady=5)

        for it in items:
            cod, nom, cat, est, ubi, cant, resp, dest, fecha = it
            coincide = (busqueda in nom.lower() or busqueda in cod.lower() or busqueda in cat.lower())
            if busqueda == "" or coincide:
                es_prestable = cant > 0 and est != "Inactivo"
                color_fondo = "#2b2b2b" if es_prestable else "#1a1a1a"
                f = ctk.CTkFrame(self.tabla_p, fg_color=color_fondo, corner_radius=8)
                f.pack(fill="x", pady=3, padx=5)

                txt_frame = ctk.CTkFrame(f, fg_color="transparent")
                txt_frame.pack(side="left", padx=15, pady=8)

                color_texto = "#ffffff" if es_prestable else "#555555"
                ctk.CTkLabel(txt_frame, text=nom, font=("Arial", 13, "bold"), text_color=color_texto, anchor="w").pack(anchor="w")

                detalle_txt = f"ID: {cod} | Disponible: {cant} | Cat: {cat}"
                ctk.CTkLabel(txt_frame, text=detalle_txt, font=("Arial", 10), text_color="#888888", anchor="w").pack(anchor="w")

                if es_prestable:
                    ctk.CTkButton(f, text="➕ Agregar", width=80, height=30, fg_color="#3498db", hover_color="#2980b9", font=("Arial", 11, "bold"), command=lambda c=cod, n=nom, ct=cat, s=cant: self.agregar_al_carrito(c, n, ct, s)).pack(side="right", padx=15)
                else:
                    estado_msj = "AGOTADO" if cant <= 0 else "INACTIVO"
                    ctk.CTkLabel(f, text=estado_msj, font=("Arial", 10, "bold"), text_color="#e74c3c", width=80).pack(side="right", padx=15)

    def agregar_al_carrito(self, codigo, nombre, categoria, stock_max):
        """Agrega un artículo al carrito temporal de préstamo."""
        cantidad_a_prestar = 1
        if categoria not in ["Tablet", "Notebook", "Impresora"]:
            dialogo = ctk.CTkInputDialog(text=f"¿Cuántos de '{nombre}' desea prestar? (Máx: {stock_max})", title="Cantidad")
            try:
                entrada_cant = dialogo.get_input()
                if not entrada_cant:
                    return
                cantidad_a_prestar = int(entrada_cant)
                if cantidad_a_prestar <= 0 or cantidad_a_prestar > stock_max:
                    messagebox.showwarning("Atención", "Cantidad inválida o superior al stock disponible.")
                    return
            except ValueError:
                messagebox.showerror("Error", "La cantidad debe ser un número.")
                return

        for item in self.lista_items_seleccionados:
            if item["codigo"] == codigo:
                messagebox.showwarning("Atención", "Este elemento ya está en el carrito.")
                return

        self.lista_items_seleccionados.append({
            "codigo": codigo,
            "nombre": nombre,
            "cantidad": cantidad_a_prestar,
        })
        self.refrescar_visual_del_carrito()

    def refrescar_visual_del_carrito(self):
        """Redibuja el carrito de préstamos con la lista de artículos seleccionados."""
        for w in self.carrito_lista.winfo_children():
            w.destroy()

        for item in self.lista_items_seleccionados:
            f = ctk.CTkFrame(self.carrito_lista, fg_color="#2b2b2b", corner_radius=5)
            f.pack(fill="x", pady=2, padx=5)

            ctk.CTkLabel(f, text=f"• {item['nombre']} x{item['cantidad']}", font=("Arial", 11), text_color="#2ecc71").pack(side="left", padx=10, pady=2)
            ctk.CTkButton(f, text="X", width=25, height=20, font=("Arial", 10, "bold"), fg_color="#c0392b", hover_color="#e74c3c", command=lambda c=item["codigo"]: self.quitar_del_carrito(c)).pack(side="right", padx=5)

    def quitar_del_carrito(self, codigo):
        """Elimina un artículo del carrito de préstamo."""
        self.lista_items_seleccionados = [i for i in self.lista_items_seleccionados if i["codigo"] != codigo]
        self.refrescar_visual_del_carrito()

    def show_prestamos_libros(self):
        """Muestra una interfaz para prestar copias individuales de libros por número de serie."""
        self.clear()
        
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 10))
        
        ctk.CTkLabel(header, text="📚 Prestar Copia de Libro (Por Número de Serie)", font=("Arial", 22, "bold"), text_color="#f1c40f").pack(side="left")
        
        # Frame de búsqueda
        search_frame = ctk.CTkFrame(self, fg_color="transparent")
        search_frame.pack(fill="x", padx=20, pady=(0, 10))
        
        ctk.CTkLabel(search_frame, text="Número de Serie:", font=("Arial", 12)).pack(side="left", padx=(0, 10))
        ent_serie = ctk.CTkEntry(search_frame, placeholder_text="Ej: LIB-001-01", width=200)
        ent_serie.pack(side="left", padx=5)
        
        info_frame = ctk.CTkFrame(self, fg_color="#1d1d1d", corner_radius=8)
        info_frame.pack(fill="both", expand=False, padx=20, pady=10)
        
        label_info = ctk.CTkLabel(info_frame, text="Ingrese un número de serie y presione Enter para buscar...", text_color="#aaaaaa", font=("Arial", 11))
        label_info.pack(padx=15, pady=15)
        
        # Frame para datos del responsable
        datos_frame = ctk.CTkFrame(self, fg_color="transparent")
        datos_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(datos_frame, text="👤 Datos del Responsable", font=("Arial", 14, "bold"), text_color="#f1c40f").pack(anchor="w", pady=(0, 10))
        
        ctk.CTkLabel(datos_frame, text="Tipo de Usuario:").pack(anchor="w", pady=(5, 0))
        combo_tipo = ctk.CTkComboBox(datos_frame, values=["Estudiante", "Funcionario"], width=300)
        combo_tipo.set("Estudiante")
        combo_tipo.pack(anchor="w", pady=5)
        
        ctk.CTkLabel(datos_frame, text="Nombre Completo:").pack(anchor="w", pady=(5, 0))
        ent_responsable = ctk.CTkEntry(datos_frame, width=300)
        ent_responsable.pack(anchor="w", pady=5)
        
        ctk.CTkLabel(datos_frame, text="Sala / Oficina de Destino:").pack(anchor="w", pady=(5, 0))
        ent_destino = ctk.CTkEntry(datos_frame, width=300)
        ent_destino.pack(anchor="w", pady=5)
        
        # Frame de botones
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=20)
        
        btn_prestar = ctk.CTkButton(btn_frame, text="📤 PRESTAR COPIA", fg_color="#27ae60", hover_color="#2ecc71", state="disabled", font=("Arial", 13, "bold"), height=40)
        btn_prestar.pack(side="left", padx=5, fill="x", expand=True)
        
        btn_limpiar = ctk.CTkButton(btn_frame, text="Limpiar", fg_color="#34495e", hover_color="#2c3e50", font=("Arial", 12))
        btn_limpiar.pack(side="left", padx=5)
        
        def buscar_copia(*args):
            numero_serie = ent_serie.get().strip()
            if not numero_serie:
                label_info.configure(text="Ingrese un número de serie...")
                btn_prestar.configure(state="disabled")
                return
            
            info = database.buscar_copia_por_numero_serie_db(numero_serie)
            if info['encontrado']:
                estado = info['estado']
                nombre_libro = info['nombre_libro']
                responsable_actual = info['responsable']
                estado_color = "#2ecc71" if estado == "Disponible" else "#e67e22"
                
                texto_info = f"✓ Libro: {nombre_libro}\n"
                texto_info += f"  Estado: {estado}\n"
                texto_info += f"  Autor: {info['autor']}\n"
                if estado == "Prestado":
                    texto_info += f"  Actualmente con: {responsable_actual}\n"
                    btn_prestar.configure(state="disabled")
                    label_info.configure(text=texto_info, text_color="#e67e22")
                else:
                    btn_prestar.configure(state="normal")
                    label_info.configure(text=texto_info, text_color=estado_color)
            else:
                label_info.configure(text=f"✗ Número de serie '{numero_serie}' no encontrado", text_color="#e74c3c")
                btn_prestar.configure(state="disabled")
        
        def prestar():
            numero_serie = ent_serie.get().strip()
            responsable = ent_responsable.get().strip()
            destino = ent_destino.get().strip()
            tipo = combo_tipo.get()
            
            if not numero_serie or not responsable or not destino:
                messagebox.showwarning("Faltan Datos", "Complete todos los campos requeridos.")
                return
            
            exito, mensaje = database.prestar_copia_libro_db(numero_serie, responsable, destino, tipo)
            if exito:
                messagebox.showinfo("Éxito", f"{mensaje}\n\nCopia: {numero_serie}\nResponsable: {responsable}")
                ent_serie.delete(0, "end")
                ent_responsable.delete(0, "end")
                ent_destino.delete(0, "end")
                label_info.configure(text="Ingrese un número de serie y presione Enter para buscar...", text_color="#aaaaaa")
                btn_prestar.configure(state="disabled")
            else:
                messagebox.showerror("Error", mensaje)
        
        def limpiar():
            ent_serie.delete(0, "end")
            ent_responsable.delete(0, "end")
            ent_destino.delete(0, "end")
            label_info.configure(text="Ingrese un número de serie y presione Enter para buscar...", text_color="#aaaaaa")
            btn_prestar.configure(state="disabled")
        
        ent_serie.bind("<Return>", buscar_copia)
        btn_prestar.configure(command=prestar)
        btn_limpiar.configure(command=limpiar)
