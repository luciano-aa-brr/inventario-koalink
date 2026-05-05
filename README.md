# Sistema de Inventario Escolar

Un sistema completo de gestión de inventario escolar desarrollado con Python y CustomTkinter. Diseñado para ser portable y ejecutable desde USB sin instalación.

## Características

- 📋 **Gestión de Inventario**: Control completo de artículos escolares con paginación y búsqueda inteligente
- 📤 **Sistema de Préstamos**: Préstamos múltiples con carrito de compras y códigos de barras
- 📥 **Devoluciones**: Recepción y gestión de devoluciones con validación automática
- 📋 **Historial**: Seguimiento de préstamos activos con edición en tiempo real
- 📄 **Etiquetas PDF**: Generación automática de etiquetas con códigos de barras Code128
- 🔍 **Búsqueda Inteligente**: Búsqueda en tiempo real con debounce (500ms)
- 🎨 **Interfaz Moderna**: Tema oscuro con CustomTkinter y colores personalizables
- 🔒 **Instancia Única**: Previene múltiples instancias abiertas simultáneamente
- 💾 **Base de Datos SQLite**: Almacenamiento local portable
- 📊 **Reportes**: Sistema de reportes y backups automáticos
- 🚀 **Ejecutable Portable**: Funciona desde USB sin instalación

## Tecnologías y Versiones

### Entorno de Desarrollo
- **Python**: 3.14.2
- **Sistema Operativo**: Windows 11
- **IDE**: Visual Studio Code con extensiones Python y Git

### Librerías Principales
| Librería | Versión | Propósito |
|----------|---------|-----------|
| `customtkinter` | 5.2.2 | Interfaz gráfica moderna |
| `pillow` | 12.1.1 | Procesamiento de imágenes |
| `reportlab` | 4.4.10 | Generación de PDFs |
| `python-barcode` | 0.16.1 | Generación de códigos de barras |
| `numpy` | 2.4.3 | Cálculos matemáticos |
| `pandas` | 3.0.1 | Manipulación de datos |
| `openpyxl` | 3.1.5 | Soporte para Excel |
| `fpdf` | 1.7.2 | Generación alternativa de PDFs |
| `darkdetect` | 0.8.0 | Detección automática de tema del sistema |

### Herramientas de Desarrollo
| Herramienta | Versión | Propósito |
|-------------|---------|-----------|
| `pyinstaller` | 6.19.0 | Creación de ejecutables |
| `pyinstaller-hooks-contrib` | 2026.3 | Hooks adicionales para PyInstaller |

## Arquitectura del Sistema

### Estructura Modular
```
inventario-Koalink/
├── main.py                 # Controlador principal y aplicación
├── database.py             # Capa de datos SQLite
├── config.py               # Configuraciones centralizadas
├── constants.py            # Constantes de la aplicación
├── exceptions.py           # Excepciones personalizadas
├── logger.py               # Sistema de logging
├── utils.py                # Utilidades compartidas
├── compilar.py             # Script de compilación PyInstaller
├── modules/                # Módulos de interfaz de usuario
│   ├── __init__.py
│   ├── inventario.py       # Gestión de inventario
│   ├── prestamos.py        # Sistema de préstamos
│   ├── devoluciones.py     # Gestión de devoluciones
│   └── historial.py        # Historial de préstamos
├── assets/                 # Recursos gráficos e íconos
├── data/                   # Base de datos y archivos de datos
├── logs/                   # Archivos de logging
├── backups/                # Copias de seguridad
├── reportes/               # PDFs generados
├── build/                  # Archivos temporales de PyInstaller
└── dist/                   # Ejecutable final generado
```

### Patrón Arquitectónico
- **MVC Simplificado**: Separación entre lógica de negocio (database.py), interfaz (modules/), y controlador (main.py)
- **Configuración Centralizada**: Todas las configuraciones en `config.py`
- **Manejo de Errores**: Excepciones personalizadas en `exceptions.py`
- **Logging Estructurado**: Sistema de logs en `logger.py`
- **Utilidades Compartidas**: Funciones comunes en `utils.py`

## Funciones Principales

### main.py - Controlador Principal
- `verificar_instancia_unica()`: Evita múltiples instancias usando sockets
- `center_window()`: Centra ventanas en la pantalla
- Gestión de tema oscuro forzado
- Inicialización de módulos UI
- Manejo de eventos de navegación

### database.py - Capa de Datos
- `conectar_db()`: Conexión SQLite con ruta portable para USB
- `inicializar_tablas()`: Creación automática de esquema de BD
- `crear_backup()`: Copias de seguridad automáticas
- Funciones CRUD para artículos, préstamos y devoluciones
- Paginación inteligente para grandes volúmenes de datos

### modules/inventario.py - Gestión de Inventario
- Búsqueda en tiempo real con debounce
- Paginación de resultados (50 ítems por página)
- Agregar/editar/eliminar artículos
- Generación de códigos de barras automáticos
- Validación de datos de entrada

### modules/prestamos.py - Sistema de Préstamos
- Carrito de compras para préstamos múltiples
- Validación de stock disponible
- Generación de códigos únicos de préstamo
- Asociación profesor-alumno-equipo

### modules/devoluciones.py - Devoluciones
- Recepción de artículos devueltos
- Validación automática de estado
- Actualización de stock en tiempo real
- Confirmación de recepción

### modules/historial.py - Historial
- Visualización de préstamos activos
- Edición en tiempo real
- Filtros por profesor/alumno/equipo
- Seguimiento de fechas

### utils.py - Utilidades
- `get_resource_path()`: Manejo de rutas para desarrollo/ejecutable
- `get_chile_time()`: Zona horaria UTC-3
- `center_window()`: Posicionamiento de ventanas
- Funciones de mensajes estandarizados

## Configuraciones

### Configuración de Base de Datos (config.py)
```python
DB_PATH = "data/inventario.db"          # Ruta relativa portable
BACKUP_DIR = "backups"                  # Directorio de backups
```

### Configuración de UI
```python
WINDOW_TITLE = "Sistema de Inventario Escolar"
THEME_MODE = "Dark"                     # Tema forzado oscuro
THEME_COLOR = "dark-blue"               # Color de acento
ACCENT_COLOR = "#FFFA03"                # Amarillo personalizado
```

### Configuración Funcional
```python
SINGLE_INSTANCE_PORT = 54321            # Puerto para instancia única
SEARCH_DEBOUNCE_MS = 500                # Retardo búsqueda inteligente
ITEMS_PER_PAGE = 50                     # Paginación
```

### Configuración de Etiquetas PDF
```python
ETIQUETA_WIDTH_MM = 60                  # Ancho de etiqueta
ETIQUETA_HEIGHT_MM = 35                 # Alto de etiqueta
ETIQUETAS_POR_FILA = 3                  # Etiquetas por fila
BARCODE_TYPE = "code128"                # Tipo de código de barras
```

### Categorías de Artículos
```python
CATEGORIAS_PREFIJOS = {
    "Tablet": "TAB",
    "Notebook": "NOTE",
    "PC": "PC",
    "Libro": "LIB",
    "Material Didáctico": "MAT",
    "Impresora": "IMP",
    "Proyector": "PROY"
}
```

## Constantes y Mensajes

### Mensajes de Error (constants.py)
- `ERROR_DB_CONNECTION`: "Error al conectar con la base de datos"
- `ERROR_SINGLE_INSTANCE`: "El sistema ya se encuentra abierto"
- `ERROR_INVALID_DATA`: "Los datos ingresados no son válidos"
- `ERROR_BACKUP_FAILED`: "Error al crear la copia de seguridad"

### Mensajes Informativos
- `INFO_BACKUP_SUCCESS`: "Copia de seguridad creada exitosamente"
- `INFO_ITEM_ADDED`: "Artículo agregado correctamente"
- `INFO_LOAN_SUCCESS`: "Préstamo registrado correctamente"

### Etiquetas de UI
- `LABEL_INVENTORY`: "📋 Inventario"
- `LABEL_NEW_ITEM`: "➕ Nuevo Ingreso"
- `LABEL_LOAN`: "📤 Préstamo"
- `LABEL_RETURN`: "📥 Devolución"
- `LABEL_HISTORY`: "📋 Historial"

## Sistema de Excepciones

### Jerarquía de Excepciones (exceptions.py)
```
InventarioError (base)
├── DatabaseError          # Errores de BD
├── ValidationError        # Validación de datos
├── PermissionError        # Permisos
├── FileOperationError     # Operaciones de archivos
├── PDFGenerationError     # Generación de PDFs
├── BarcodeGenerationError # Códigos de barras
└── LoanError             # Operaciones de préstamo
```

## Sistema de Logging

### Configuración (logger.py)
- **Nivel**: INFO
- **Formato**: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`
- **Handlers**: Archivo diario + consola
- **Ubicación**: `logs/inventario_YYYYMMDD.log`

## Requisitos del Sistema

- **Python**: 3.8 o superior
- **Memoria RAM**: 512MB mínimo, 1GB recomendado
- **Espacio en Disco**: 50MB para instalación, 100MB para datos
- **Sistema Operativo**: Windows 7+, macOS 10.12+, Linux
- **Permisos**: Lectura/escritura en directorio de ejecución

## Instalación

### Desde Código Fuente
1. **Clona el repositorio**:
```bash
git clone <url-del-repositorio>
cd inventario-Koalink
```

2. **Crea entorno virtual**:
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate
```

3. **Instala dependencias**:
```bash
pip install -r requirements.txt
```

4. **Ejecuta la aplicación**:
```bash
python main.py
```

### Dependencias Principales (requirements.txt)
```
customtkinter==5.2.2
pillow==12.1.1
reportlab==4.4.10
python-barcode==0.16.1
darkdetect==0.8.0
```

## Uso

### Funcionalidades Principales
1. **📋 Inventario**: Gestiona artículos con búsqueda y paginación
2. **➕ Nuevo Ingreso**: Agrega equipos con códigos automáticos
3. **📤 Préstamo**: Crea préstamos múltiples con carrito
4. **📥 Devolución**: Procesa devoluciones con validación
5. **📋 Historial**: Visualiza y edita préstamos activos
6. **📄 Generar Etiquetas**: Crea PDFs con códigos de barras

### Atajos de Teclado
- `Ctrl+F`: Enfocar búsqueda
- `Enter`: Confirmar acciones
- `Esc`: Cancelar operaciones

## Ejecutable para USB

### Compilación
```bash
python compilar.py
```

### Distribución
1. Copia la carpeta `dist/` completa a tu USB
2. Ejecuta `main.exe` desde cualquier PC Windows
3. Los datos se guardan en `dist/data/inventario.db`

**Nota**: La carpeta completa es necesaria por recursos empaquetados.

## Desarrollo

### Configuración del Entorno
```bash
# Instalar dependencias de desarrollo
pip install pyinstaller pytest

# Ejecutar tests
pytest test_basic.py

# Compilar ejecutable
python compilar.py
```

### Convenciones de Código
- **PEP 8**: Estilo de código Python
- **Docstrings**: Documentación en funciones
- **Logging**: Uso obligatorio de logger
- **Excepciones**: Usar excepciones personalizadas
- **Configuración**: Centralizar en config.py

### Debugging
- Logs en `logs/inventario_YYYYMMDD.log`
- Modo verbose: `python main.py --debug`
- Base de datos: `data/inventario.db` (SQLite)

### Testing
- Tests básicos en `test_basic.py`
- Cobertura: Funciones críticas de BD y UI
- Ejecución: `pytest test_basic.py`

## API y Extensiones

### Puntos de Extensión
- **Módulos UI**: Agregar nuevos módulos en `modules/`
- **Categorías**: Extender `CATEGORIAS_PREFIJOS` en config.py
- **Reportes**: Agregar funciones en `database.py`
- **Validaciones**: Extender en `utils.py`

### Migración de Datos
- Script `migracion.py` para importar datos antiguos
- Soporte para bases de datos legacy
- Mapeo inteligente de campos

## Soporte y Mantenimiento

### Logs de Error
- Ubicación: `logs/`
- Rotación: Diaria automática
- Contenido: Errores, warnings, operaciones críticas

### Backups
- Automáticos en `backups/`
- Manuales desde la interfaz
- Restauración: Copiar archivo .db a `data/`

### Rendimiento
- Paginación: 50 ítems por página
- Debounce: 500ms en búsquedas
- Optimización: Índices en BD para búsquedas

## Licencia

Este proyecto es software propietario desarrollado para uso educativo interno.

## Versión

**v1.0.0** - Sistema completo funcional con ejecutable portable.

---

*Desarrollado con cariño para la gestión eficiente de inventario escolar*

### Agregar Nuevas Categorías

Edita `CATEGORIAS_PREFIJOS` en `database.py`:

```python
CATEGORIAS_PREFIJOS = {
    "NuevaCategoria": "PREFIJO",
    # ... categorías existentes
}
```

## Contribución

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -am 'Agrega nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

## Licencia

Este proyecto está bajo la Licencia MIT.