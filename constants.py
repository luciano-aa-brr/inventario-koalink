# Constantes de la aplicación
class Constants:
    # Mensajes de la aplicación
    APP_TITLE = "Sistema de Inventario Escolar"
    APP_VERSION = "1.0.0"

    # Mensajes de error
    ERROR_DB_CONNECTION = "Error al conectar con la base de datos"
    ERROR_SINGLE_INSTANCE = "El sistema ya se encuentra abierto"
    ERROR_INVALID_DATA = "Los datos ingresados no son válidos"
    ERROR_PERMISSION_DENIED = "No tiene permisos para realizar esta acción"
    ERROR_FILE_NOT_FOUND = "Archivo no encontrado"
    ERROR_BACKUP_FAILED = "Error al crear la copia de seguridad"

    # Mensajes informativos
    INFO_BACKUP_SUCCESS = "Copia de seguridad creada exitosamente"
    INFO_ITEM_ADDED = "Artículo agregado correctamente"
    INFO_LOAN_SUCCESS = "Préstamo registrado correctamente"
    INFO_RETURN_SUCCESS = "Devolución procesada correctamente"
    INFO_PDF_GENERATED = "PDF generado correctamente"

    # Mensajes de confirmación
    CONFIRM_DELETE_ITEM = "¿Está seguro de que desea eliminar este artículo?"
    CONFIRM_LOAN_MULTIPLE = "¿Confirmar el préstamo de todos los artículos seleccionados?"
    CONFIRM_RETURN_ITEMS = "¿Confirmar la recepción de estos artículos?"

    # Etiquetas de UI
    LABEL_INVENTORY = "📋 Inventario"
    LABEL_NEW_ITEM = "➕ Nuevo Ingreso"
    LABEL_LOAN = "📤 Préstamo"
    LABEL_RETURN = "📥 Devolución"
    LABEL_HISTORY = "📋 Historial"
    LABEL_GENERATE_LABELS = "📄 Generar Etiquetas"

    # Placeholders
    PLACEHOLDER_SEARCH_INVENTORY = "🔍 Buscar ítem por nombre..."
    PLACEHOLDER_SEARCH_LOANS = "Buscar por profesor, alumno o equipo..."
    PLACEHOLDER_RESPONSIBLE = "Nombre Completo del Responsable"
    PLACEHOLDER_DESTINATION = "Sala o Oficina de Destino"

    # Colores
    COLOR_ACCENT = "#FFFA03"
    COLOR_SUCCESS = "#27ae60"
    COLOR_WARNING = "#f39c12"
    COLOR_ERROR = "#e74c3c"
    COLOR_INFO = "#3498db"

    # Configuración de paginación
    DEFAULT_ITEMS_PER_PAGE = 50
    MAX_ITEMS_PER_PAGE = 100

    # Configuración de búsqueda
    SEARCH_DEBOUNCE_MS = 500
    MIN_SEARCH_LENGTH = 2

    # Límites de validación
    MAX_ITEM_NAME_LENGTH = 100
    MAX_RESPONSIBLE_NAME_LENGTH = 100
    MAX_DESTINATION_LENGTH = 50
    MAX_QUANTITY = 1000

    # Estados de artículos
    STATUS_ACTIVE = "Activo"
    STATUS_INACTIVE = "Inactivo"
    STATUS_LOANED = "Prestado"
    STATUS_AVAILABLE = "Disponible"

    # Tipos de usuario
    USER_TYPE_STUDENT = "Estudiante"
    USER_TYPE_STAFF = "Funcionario"

    # Cursos disponibles
    COURSES = ["1ro", "2do", "3ro", "4to", "5to", "6to", "7mo", "8vo"]

    # Extensiones de archivo permitidas
    ALLOWED_IMAGE_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.gif', '.bmp']
    ALLOWED_DOCUMENT_EXTENSIONS = ['.pdf', '.doc', '.docx', '.xls', '.xlsx']

    # Configuración de PDF
    PDF_PAGE_SIZE = "letter"
    PDF_MARGIN_MM = 10
    PDF_LABEL_WIDTH_MM = 60
    PDF_LABEL_HEIGHT_MM = 35
    PDF_LABELS_PER_ROW = 3

    # Configuración de códigos de barras
    BARCODE_TYPE = "code128"
    BARCODE_MODULE_HEIGHT = 5.0
    BARCODE_TEXT = False

    # Configuración de backup
    BACKUP_PREFIX = "Respaldo_"
    BACKUP_DATE_FORMAT = "%d-%m-%Y_%H-%M-%S"
    BACKUP_EXTENSION = ".db"

    # Configuración de logging
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
    LOG_FILENAME_PREFIX = "inventario_"
    LOG_FILENAME_DATE_FORMAT = "%Y%m%d"