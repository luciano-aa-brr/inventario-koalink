from tkinter import messagebox
import customtkinter as ctk
import database


class DevolucionesModule(ctk.CTkFrame):
    """Frame del módulo de devoluciones.

    Gestiona la selección de artículos en devolución y la recepción al inventario.
    """

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.lista_devolucion_temp = []
        self.ent_busqueda_dev = None
        self.tabla_dev = None
        self.carrito_dev_lista = None

    def clear(self):
        """Elimina todos los widgets del módulo."""
        for widget in self.winfo_children():
            widget.destroy()

    def show_devoluciones(self):
        """Muestra la vista de recepción de devoluciones."""
        self.clear()
        self.lista_devolucion_temp = []

        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(0, weight=1)

        izq_frame = ctk.CTkFrame(self, fg_color="#1d1d1d", corner_radius=15)
        izq_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        ctk.CTkLabel(izq_frame, text="📥 Buscar Equipos para Devolver", font=("Arial", 18, "bold"), text_color="#FFFA03").pack(pady=10)

        self.ent_busqueda_dev = ctk.CTkEntry(izq_frame, placeholder_text="Escriba nombre del equipo o responsable...")
        self.ent_busqueda_dev.pack(fill="x", padx=20, pady=5)
        self.ent_busqueda_dev.bind("<KeyRelease>", lambda e: self.refrescar_tabla_devoluciones())

        self.tabla_dev = ctk.CTkScrollableFrame(izq_frame, fg_color="transparent")
        self.tabla_dev.pack(fill="both", expand=True, padx=10, pady=10)

        der_frame = ctk.CTkFrame(self, corner_radius=15)
        der_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        ctk.CTkLabel(der_frame, text="🛒 Recepción de Materiales", font=("Arial", 18, "bold"), text_color="#FFFA03").pack(pady=20)

        self.carrito_dev_lista = ctk.CTkScrollableFrame(der_frame, fg_color="#1a1a1a", height=400)
        self.carrito_dev_lista.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkButton(der_frame, text="📥 CONFIRMAR RECEPCIÓN", fg_color="#27ae60", height=50, font=("Arial", 14, "bold"), command=self.confirmar_recepcion_total).pack(pady=20, padx=20, fill="x")

        self.refrescar_tabla_devoluciones()

    def confirmar_recepcion_total(self):
        """Registra todas las devoluciones del carrito contra la base de datos."""
        if not self.lista_devolucion_temp:
            messagebox.showwarning("Atención", "No hay elementos en el carrito de devolución.")
            return

        exitos = 0
        for item in self.lista_devolucion_temp:
            exito, msj = database.registrar_devolucion_item_db(item["id_detalle"], item["codigo"], item["cantidad"])
            if exito:
                exitos += 1
            else:
                print(f"Error al devolver {item['nombre']}: {msj}")

        if exitos > 0:
            messagebox.showinfo("Éxito", f"Se han reingresado {exitos} artículos al inventario correctamente.")
        else:
            messagebox.showerror("Error", "No se pudo procesar ninguna devolución. Verifique los datos.")

        self.show_devoluciones()

    def refrescar_tabla_devoluciones(self):
        """Muestra los detalles de los artículos actualmente prestados para devolver."""
        for w in self.tabla_dev.winfo_children():
            w.destroy()

        busqueda = self.ent_busqueda_dev.get().lower()
        items_prestados = database.obtener_detalles_prestados(busqueda)

        for it in items_prestados:
            id_det, cod, nom, resp, dest, cant = it
            f = ctk.CTkFrame(self.tabla_dev, fg_color="#2b2b2b", corner_radius=8)
            f.pack(fill="x", pady=3, padx=5)

            txt_info = f"{nom} (x{cant})\n👤 {resp} | 📍 {dest}"
            ctk.CTkLabel(f, text=txt_info, font=("Arial", 11), anchor="w", justify="left").pack(side="left", padx=15, pady=8)
            ctk.CTkButton(f, text="📥 Recibir", width=70, height=30, command=lambda d=id_det, c=cod, n=nom, q=cant: self.agregar_a_devolucion(d, c, n, q)).pack(side="right", padx=10)

    def agregar_a_devolucion(self, id_detalle, codigo, nombre, cantidad_max):
        """Añade un artículo al carrito de devolución, preguntando cantidad si es necesario."""
        if any(i["id_detalle"] == id_detalle for i in self.lista_devolucion_temp):
            return

        cantidad_a_regresar = cantidad_max
        if cantidad_max > 1:
            dialogo = ctk.CTkInputDialog(text=f"¿Cuántas unidades de '{nombre}' devuelve?\n(Máximo: {cantidad_max})", title="Devolución Parcial")
            try:
                entrada = dialogo.get_input()
                if not entrada:
                    return
                cantidad_a_regresar = int(entrada)
                if cantidad_a_regresar <= 0 or cantidad_a_regresar > cantidad_max:
                    messagebox.showwarning("Error", "Cantidad no válida.")
                    return
            except ValueError:
                messagebox.showerror("Error", "Debe ingresar un número.")
                return

        self.lista_devolucion_temp.append({
            "id_detalle": id_detalle,
            "codigo": codigo,
            "nombre": nombre,
            "cantidad": cantidad_a_regresar,
            "es_parcial": cantidad_a_regresar < cantidad_max,
        })
        self.refrescar_visual_carrito_dev()

    def refrescar_visual_carrito_dev(self):
        """Redibuja la lista temporal de devoluciones."""
        for w in self.carrito_dev_lista.winfo_children():
            w.destroy()

        for item in self.lista_devolucion_temp:
            f = ctk.CTkFrame(self.carrito_dev_lista, fg_color="#2b2b2b", corner_radius=5)
            f.pack(fill="x", pady=2, padx=5)

            ctk.CTkLabel(f, text=f"• {item['nombre']} (x{item['cantidad']})", font=("Arial", 11)).pack(side="left", padx=10)
            ctk.CTkButton(f, text="X", width=25, height=20, fg_color="#c0392b", command=lambda c=item["id_detalle"]: self.quitar_de_devolucion(c)).pack(side="right", padx=5)

    def quitar_de_devolucion(self, id_detalle):
        """Elimina un artículo del carrito de devolución."""
        self.lista_devolucion_temp = [i for i in self.lista_devolucion_temp if i["id_detalle"] != id_detalle]
        self.refrescar_visual_carrito_dev()
