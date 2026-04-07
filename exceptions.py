class InventarioError(Exception):
    """Excepción base para errores del sistema de inventario."""
    pass

class DatabaseError(InventarioError):
    """Errores relacionados con la base de datos."""
    pass

class ValidationError(InventarioError):
    """Errores de validación de datos."""
    pass

class PermissionError(InventarioError):
    """Errores de permisos."""
    pass

class FileOperationError(InventarioError):
    """Errores en operaciones de archivos."""
    pass

class PDFGenerationError(InventarioError):
    """Errores en la generación de PDFs."""
    pass

class BarcodeGenerationError(InventarioError):
    """Errores en la generación de códigos de barras."""
    pass

class LoanError(InventarioError):
    """Errores en operaciones de préstamo."""
    pass

class ReturnError(InventarioError):
    """Errores en operaciones de devolución."""
    pass

class ItemNotFoundError(InventarioError):
    """Error cuando un artículo no se encuentra."""
    pass

class InsufficientStockError(InventarioError):
    """Error cuando no hay suficiente stock disponible."""
    pass

class DuplicateEntryError(InventarioError):
    """Error cuando se intenta crear una entrada duplicada."""
    pass