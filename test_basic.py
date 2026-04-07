import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock

# Agregar el directorio raíz al path para importar módulos
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import validate_not_empty, validate_numeric, get_chile_time
from constants import Constants
from exceptions import ValidationError, InventarioError, DatabaseError

class TestUtils(unittest.TestCase):
    """Pruebas para las funciones de utilidad."""

    def test_validate_not_empty_valid(self):
        """Prueba validación de campo no vacío válido."""
        result = validate_not_empty("test value", "test field")
        self.assertEqual(result, "test value")

    def test_validate_not_empty_invalid(self):
        """Prueba validación de campo vacío."""
        with self.assertRaises(ValueError):
            validate_not_empty("", "test field")

        with self.assertRaises(ValueError):
            validate_not_empty("   ", "test field")

        with self.assertRaises(ValueError):
            validate_not_empty(None, "test field")

    def test_validate_numeric_valid(self):
        """Prueba validación numérica válida."""
        result = validate_numeric("42", "test field")
        self.assertEqual(result, 42)

    def test_validate_numeric_invalid(self):
        """Prueba validación numérica inválida."""
        with self.assertRaises(ValueError):
            validate_numeric("not_a_number", "test field")

    def test_validate_numeric_with_range(self):
        """Prueba validación numérica con rango."""
        result = validate_numeric("50", "test field", 0, 100)
        self.assertEqual(result, 50)

        with self.assertRaises(ValueError):
            validate_numeric("150", "test field", 0, 100)

    def test_get_chile_time(self):
        """Prueba obtención de hora chilena."""
        dt = get_chile_time()
        # Verificar que es un datetime con zona horaria UTC-3
        self.assertIsNotNone(dt)
        self.assertEqual(dt.tzinfo, get_chile_time().tzinfo)

class TestConstants(unittest.TestCase):
    """Pruebas para las constantes de la aplicación."""

    def test_app_title(self):
        """Prueba que el título de la app esté definido."""
        self.assertEqual(Constants.APP_TITLE, "Sistema de Inventario Escolar")

    def test_colors_defined(self):
        """Prueba que los colores estén definidos."""
        self.assertTrue(hasattr(Constants, 'COLOR_ACCENT'))
        self.assertTrue(hasattr(Constants, 'COLOR_SUCCESS'))
        self.assertTrue(hasattr(Constants, 'COLOR_ERROR'))

    def test_validation_limits(self):
        """Prueba que los límites de validación estén definidos."""
        self.assertGreater(Constants.MAX_ITEM_NAME_LENGTH, 0)
        self.assertGreater(Constants.MAX_QUANTITY, 0)

class TestExceptions(unittest.TestCase):
    """Pruebas para las excepciones personalizadas."""

    def test_inventario_error(self):
        """Prueba la excepción base."""
        error = InventarioError("Test error")
        self.assertEqual(str(error), "Test error")

    def test_validation_error(self):
        """Prueba la excepción de validación."""
        error = ValidationError("Invalid data")
        self.assertIsInstance(error, InventarioError)
        self.assertEqual(str(error), "Invalid data")

    def test_database_error(self):
        """Prueba la excepción de base de datos."""
        error = DatabaseError("DB connection failed")
        self.assertIsInstance(error, InventarioError)

if __name__ == '__main__':
    # Crear suite de pruebas
    unittest.main(verbosity=2)