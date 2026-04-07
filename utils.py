import os
import sys
from datetime import datetime, timezone, timedelta
from tkinter import messagebox
import customtkinter as ctk

def get_resource_path(relative_path):
    """
    Obtiene la ruta absoluta para recursos (imágenes, bases de datos).
    Funciona tanto en modo desarrollo como en ejecutable.
    """
    try:
        # PyInstaller crea una carpeta temporal y guarda la ruta en _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # Si no es un ejecutable, usa la ruta normal de la carpeta actual
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def get_chile_time():
    """Genera la hora exacta de Chile (UTC-3)."""
    zona_chile = timezone(timedelta(hours=-3))
    return datetime.now(zona_chile)

def format_chile_time(dt=None):
    """Formatea una fecha para Chile."""
    if dt is None:
        dt = get_chile_time()
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def center_window(window, width, height):
    """Calcula el centro de la pantalla y posiciona la ventana ahí."""
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()

    x = int((screen_width / 2) - (width / 2))
    y = int((screen_height / 2) - (height / 2))

    window.geometry(f"{width}x{height}+{x}+{y}")

def show_error(title, message):
    """Muestra un mensaje de error estandarizado."""
    messagebox.showerror(title, message)

def show_info(title, message):
    """Muestra un mensaje informativo estandarizado."""
    messagebox.showinfo(title, message)

def show_warning(title, message):
    """Muestra un mensaje de advertencia estandarizado."""
    messagebox.showwarning(title, message)

def show_question(title, message):
    """Muestra un diálogo de confirmación."""
    return messagebox.askyesno(title, message)

def validate_not_empty(value, field_name):
    """Valida que un campo no esté vacío."""
    if not value or not value.strip():
        raise ValueError(f"El campo '{field_name}' no puede estar vacío.")
    return value.strip()

def validate_numeric(value, field_name, min_value=None, max_value=None):
    """Valida que un valor sea numérico y esté en rango."""
    try:
        num = int(value)
        if min_value is not None and num < min_value:
            raise ValueError(f"El campo '{field_name}' debe ser al menos {min_value}.")
        if max_value is not None and num > max_value:
            raise ValueError(f"El campo '{field_name}' no puede ser mayor a {max_value}.")
        return num
    except ValueError:
        raise ValueError(f"El campo '{field_name}' debe ser un número válido.")

def create_backup(source_path, backup_dir="backups"):
    """Crea una copia de seguridad de un archivo."""
    import shutil

    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.basename(source_path)
    name, ext = os.path.splitext(filename)
    backup_name = f"{name}_backup_{timestamp}{ext}"
    backup_path = os.path.join(backup_dir, backup_name)

    try:
        shutil.copy2(source_path, backup_path)
        return True, backup_path
    except Exception as e:
        return False, str(e)

def ensure_directory(path):
    """Asegura que un directorio exista."""
    if not os.path.exists(path):
        os.makedirs(path)

def clean_temp_files(temp_dir="temp_barcodes"):
    """Limpia archivos temporales."""
    import shutil
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)