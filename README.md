# Sistema de Inventario Escolar

Un sistema completo de gestión de inventario escolar desarrollado con Python y CustomTkinter.

## Características

- 📋 **Gestión de Inventario**: Control completo de artículos escolares
- 📤 **Sistema de Préstamos**: Préstamos múltiples con carrito de compras
- 📥 **Devoluciones**: Recepción y gestión de devoluciones
- 📋 **Historial**: Seguimiento de préstamos activos con edición
- 📄 **Etiquetas PDF**: Generación automática de etiquetas con códigos de barras
- 🔍 **Búsqueda Inteligente**: Búsqueda en tiempo real con debounce
- 🎨 **Interfaz Moderna**: Tema oscuro con CustomTkinter

## Requisitos

- Python 3.8+
- CustomTkinter
- SQLite3
- ReportLab
- Python-Barcode
- Pillow

## Instalación

1. Clona el repositorio:
```bash
git clone <url-del-repositorio>
cd inventario-Koalink
```

2. Crea un entorno virtual:
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

3. Instala las dependencias:
```bash
pip install -r requirements.txt
```

4. Ejecuta la aplicación:
```bash
python main.py
```

## Estructura del Proyecto

```
inventario-Koalink/
├── main.py                 # Aplicación principal
├── database.py             # Conexiones y operaciones de BD
├── modules/                # Módulos de la interfaz
│   ├── __init__.py
│   ├── inventario.py       # Gestión de inventario
│   ├── prestamos.py        # Sistema de préstamos
│   ├── devoluciones.py     # Gestión de devoluciones
│   └── historial.py        # Historial de préstamos
├── assets/                 # Recursos gráficos
├── data/                   # Base de datos SQLite
├── reportes/               # Reportes generados
└── build/                  # Archivos de construcción
```

## Uso

1. **Inventario**: Gestiona artículos, agrega nuevos equipos
2. **Préstamo**: Selecciona artículos y crea préstamos múltiples
3. **Devolución**: Recibe artículos devueltos
4. **Historial**: Visualiza y edita préstamos activos
5. **Etiquetas**: Genera PDF con códigos de barras

## Ejecutable para USB

Si quieres usar la aplicación desde una memoria USB o en otro equipo sin instalar Python directamente, copia la carpeta creada por PyInstaller:

1. Construye la aplicación con:
```bash
python build_app.py
```

2. Copia la carpeta generada `dist/SistemaInventarioEscolar/` completa a tu USB.

3. En el otro equipo, abre la carpeta copiada y ejecuta:
```bash
SistemaInventarioEscolar.exe
```

> Nota: Usa la carpeta completa `SistemaInventarioEscolar`, no solo el `.exe`, porque contiene recursos y la base de datos necesarios.

## Desarrollo

### Arquitectura

El sistema sigue una arquitectura modular:
- **main.py**: Controlador principal y utilidades compartidas
- **modules/**: Componentes especializados de UI
- **database.py**: Capa de datos con SQLite

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