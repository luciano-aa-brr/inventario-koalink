import PyInstaller.__main__
import os
import sys
from config import Config

def build_executable():
    """Construye el ejecutable usando PyInstaller."""

    # Asegurar que existan los directorios necesarios
    Config.ensure_directories()

    # Parámetros de PyInstaller
    pyinstaller_args = [
        'main.py',  # Script principal
        '--onedir',  # Crear una carpeta con el ejecutable y recursos
        '--windowed',  # No mostrar consola (ventana)
        '--name=SistemaInventarioEscolar',  # Nombre del ejecutable
        '--icon=assets/logo.ico',  # Icono de la aplicación
        '--add-data=data;data',  # Incluir carpeta data
        '--add-data=assets;assets',  # Incluir carpeta assets
        '--add-data=reportes;reportes',  # Incluir carpeta de reportes si existe
        '--hidden-import=customtkinter',  # Import oculto para CustomTkinter
        '--hidden-import=reportlab',  # Import oculto para ReportLab
        '--hidden-import=barcode',  # Import oculto para python-barcode
        '--hidden-import=fpdf',  # Import oculto para FPDF
        '--clean',  # Limpiar archivos temporales
        '--noconfirm',  # No pedir confirmación para sobrescribir
    ]

    # Ejecutar PyInstaller
    try:
        print("🏗️  Construyendo ejecutable...")
        PyInstaller.__main__.run(pyinstaller_args)
        print("✅ Ejecutable construido exitosamente en la carpeta 'dist/'")
        print("📁 Archivo: dist/SistemaInventarioEscolar.exe")

        # Verificar que el ejecutable se creó
        exe_path = os.path.join('dist', 'SistemaInventarioEscolar.exe')
        if os.path.exists(exe_path):
            file_size = os.path.getsize(exe_path) / (1024 * 1024)  # MB
            print(f"Tamaño estimado: {file_size:.2f} MB")
        else:
            print("⚠️  Advertencia: El ejecutable no se encontró en la ubicación esperada")

    except Exception as e:
        print(f"❌ Error durante la construcción: {e}")
        sys.exit(1)

if __name__ == '__main__':
    build_executable()