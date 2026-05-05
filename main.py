from tkinter import messagebox
import customtkinter as ctk
import database
from modules import InventarioModule, PrestamosModule, DevolucionesModule, HistorialModule
import os
import socket
import sys

# nuevas importaciones de utilidades y configuración
from config import Config
from utils import center_window, get_resource_path
from constants import Constants
from exceptions import InventarioError
from logger import logger

def verificar_instancia_unica():
    """Evita que el programa se abra más de una vez."""
    global lock_socket  # Mantiene el puerto abierto mientras viva la app
    lock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        lock_socket.bind(("127.0.0.1", Config.SINGLE_INSTANCE_PORT))
        logger.info("Instancia única verificada correctamente")
    except socket.error:
        logger.warning("Intento de abrir segunda instancia bloqueado")
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()  # Oculta la ventana principal de tkinter
        messagebox.showerror(Constants.APP_TITLE, Constants.ERROR_SINGLE_INSTANCE)
        sys.exit()  # Cierra este nuevo intento

verificar_instancia_unica()
# --- CONFIGURACIÓN GLOBAL DE TEMA ---
# Obliga a la App a ser siempre oscura, ignorando el modo de Windows
ctk.set_appearance_mode(Config.THEME_MODE)  # Fuerza Modo Oscuro

ctk.set_default_color_theme(Config.THEME_COLOR)  

# Configuración de colores
COLOR_AMARILLO = Config.ACCENT_COLOR

class AppInventario(ctk.CTk):
    def __init__(self):
        super().__init__()

        logger.info("Inicializando aplicación de inventario")

        # 1. Título y Pantalla Completa Automática
        self.title(Config.WINDOW_TITLE)

        # Temporizador global para búsquedas inteligentes (Debounce)
        self.timer_busqueda = None

        try:
            ruta_icono = get_resource_path("assets/logo.ico")
            if os.path.exists(ruta_icono):
                self.iconbitmap(ruta_icono)
                logger.info("Icono de aplicación cargado correctamente")
        except Exception as e:
            logger.warning(f"No se pudo cargar el icono: {e}")

        self.after(0, lambda: self.state('zoomed'))

        # Asegurar que existan los directorios necesarios
        Config.ensure_directories()

        # 2. Inicializar Base de Datos
        try:
            database.crear_tabla_bajas()
            database.inicializar_tablas()
            logger.info("Base de datos inicializada correctamente")
        except Exception as e:
            logger.error(f"Error al inicializar base de datos: {e}")
            messagebox.showerror(Config.WINDOW_TITLE, Constants.ERROR_DB_CONNECTION)
            sys.exit(1)

        # 3. Configuración de Layout (Grid)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- SIDEBAR (Menú Lateral) ---
        self.sidebar = ctk.CTkFrame(self, width=240, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        ctk.CTkLabel(self.sidebar, text="Sistema Escolar", font=("Arial", 28, "bold"),
                     text_color=Config.ACCENT_COLOR).pack(pady=30)

        # Botones de Navegación
        self.btn_inv = ctk.CTkButton(self.sidebar, text=Constants.LABEL_INVENTORY, command=self.mostrar_inventario)
        self.btn_inv.pack(pady=10, padx=20, fill="x")

        self.btn_nuevo = ctk.CTkButton(self.sidebar, text=Constants.LABEL_NEW_ITEM, command=self.mostrar_alta_equipo)
        self.btn_nuevo.pack(pady=10, padx=20, fill="x")

        # ESTE ES EL BOTÓN QUE FALTA:
        self.btn_prestamo = ctk.CTkButton(self.sidebar, text=Constants.LABEL_LOAN, command=self.mostrar_prestamos)
        self.btn_prestamo.pack(pady=10, padx=20, fill="x")

        # Botón para Devoluciones (lo dejaremos listo)
        self.btn_devolucion = ctk.CTkButton(self.sidebar, text=Constants.LABEL_RETURN, command=self.mostrar_devoluciones)
        self.btn_devolucion.pack(pady=10, padx=20, fill="x")

        # Botón para Historial de Préstamos (lo dejaremos listo, aunque no lo implementemos aún)
        self.btn_historial = ctk.CTkButton(self.sidebar, text=Constants.LABEL_HISTORY, command=self.mostrar_historial_activos)
        self.btn_historial.pack(pady="10", padx=20, fill="x")

        # En tu función mostrar_inventario, antes de crear la tabla:
        self.btn_generar_todo = ctk.CTkButton(self.sidebar, text=Constants.LABEL_GENERATE_LABELS, fg_color="#e67e22", hover_color="#d35400", command=self.generar_pdf_etiquetas)
        self.btn_generar_todo.pack(pady="10", padx=20, fill="x")

        # --- PANEL CENTRAL ---
        self.main_frame = ctk.CTkFrame(self, corner_radius=15)
        self.main_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.current_view = None

        # Cargar Dashboard al inicio
        self.mostrar_inventario()

    def centrar_ventana(self, ventana, ancho, alto):
        """Calcula el centro de la pantalla y posiciona la ventana ahí."""
        center_window(ventana, ancho, alto)

    def busqueda_inteligente(self, evento, funcion_a_ejecutar):
        """Aplica el efecto 'Debounce' para no saturar la BD y la Interfaz al escribir."""
        # Si el usuario presionó una tecla y ya había un cronómetro corriendo, lo cancelamos
        if self.timer_busqueda is not None:
            self.after_cancel(self.timer_busqueda)

        # Iniciamos un nuevo cronómetro de 500 milisegundos (0.5 segundos).
        # Si no se presiona ninguna tecla nueva en ese tiempo, se dispara la búsqueda real.
        self.timer_busqueda = self.after(Config.SEARCH_DEBOUNCE_MS, funcion_a_ejecutar)

    def limpiar_panel(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        self.current_view = None

    def generar_pdf_etiquetas(self):
        """Genera etiquetas PDF delegando al módulo actual."""
        try:
            if hasattr(self, 'current_view') and self.current_view is not None:
                self.current_view.generar_pdf_etiquetas()
                logger.info("Etiquetas PDF generadas exitosamente")
            else:
                messagebox.showwarning(Config.WINDOW_TITLE, "Abra la vista de inventario antes de generar etiquetas.")
                logger.warning("Intento de generar etiquetas sin vista activa")
        except Exception as e:
            logger.error(f"Error al generar etiquetas PDF: {e}")
            messagebox.showerror(Config.WINDOW_TITLE, f"No se pudo generar etiquetas: {e}")

    def mostrar_inventario(self):
        self.limpiar_panel()
        inventario = InventarioModule(self.main_frame, self)
        inventario.pack(fill="both", expand=True)
        inventario.show_inventario()
        self.current_view = inventario

    def mostrar_alta_equipo(self):
        self.limpiar_panel()
        inventario = InventarioModule(self.main_frame, self)
        inventario.pack(fill="both", expand=True)
        inventario.show_alta_equipo()
        self.current_view = inventario

    def mostrar_prestamos(self):
        self.limpiar_panel()
        prestamos = PrestamosModule(self.main_frame, self)
        prestamos.pack(fill="both", expand=True)
        prestamos.show_prestamos()
        self.current_view = prestamos

    def mostrar_devoluciones(self):
        self.limpiar_panel()
        devoluciones = DevolucionesModule(self.main_frame, self)
        devoluciones.pack(fill="both", expand=True)
        devoluciones.show_devoluciones()
        self.current_view = devoluciones

    def mostrar_historial_activos(self):
        self.limpiar_panel()
        historial = HistorialModule(self.main_frame, self)
        historial.pack(fill="both", expand=True)
        historial.show_historial()
        self.current_view = historial



if __name__ == "__main__":
    app = AppInventario()
    app.mainloop()