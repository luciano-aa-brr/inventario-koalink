import os
import sys

# Configuración de la aplicación
class Config:
    # Base de datos
    DB_PATH = "data/inventario.db"
    BACKUP_DIR = "backups"

    # UI
    WINDOW_TITLE = "Sistema de Inventario Escolar"
    THEME_MODE = "Dark"
    THEME_COLOR = "dark-blue"
    ACCENT_COLOR = "#FFFA03"

    # Funcionalidades
    SINGLE_INSTANCE_PORT = 54321
    SEARCH_DEBOUNCE_MS = 500
    ITEMS_PER_PAGE = 50

    # Categorías de artículos
    CATEGORIAS_PREFIJOS = {
        "Tablet": "TAB",
        "Notebook": "NOTE",
        "PC": "PC",
        "Libro": "LIB",
        "Material Didáctico": "MAT",
        "Impresora": "IMP",
        "Proyector": "PROY"
    }

    # Etiquetas PDF
    ETIQUETAS_PDF_NAME = "etiquetas_inventario_escolar.pdf"
    ETIQUETA_WIDTH_MM = 60
    ETIQUETA_HEIGHT_MM = 35
    ETIQUETAS_POR_FILA = 3

    # Aliases para compatibilidad con módulos actuales
    PDF_LABEL_WIDTH_MM = ETIQUETA_WIDTH_MM
    PDF_LABEL_HEIGHT_MM = ETIQUETA_HEIGHT_MM
    PDF_LABELS_PER_ROW = ETIQUETAS_POR_FILA
    PDF_MARGIN_MM = 10

    # Código de barras
    BARCODE_TYPE = "code128"
    BARCODE_MODULE_HEIGHT = 5.0
    BARCODE_TEXT = False

    # Zona horaria
    TIMEZONE_OFFSET = -3  # UTC-3 para Chile

    @classmethod
    def get_resource_path(cls, relative_path):
        """Obtiene la ruta absoluta para recursos."""
        try:
            # PyInstaller crea una carpeta temporal
            base_path = sys._MEIPASS
        except (NameError, AttributeError):
            # Modo desarrollo
            base_path = os.path.abspath(".")

        return os.path.join(base_path, relative_path)

    @classmethod
    def ensure_directories(cls):
        """Asegura que existan los directorios necesarios."""
        os.makedirs("data", exist_ok=True)
        os.makedirs("backups", exist_ok=True)
        os.makedirs("temp_barcodes", exist_ok=True)
        os.makedirs("reportes", exist_ok=True)