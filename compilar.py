import PyInstaller.__main__
import os
import sys

def compilar_ejecutable():
    """
    Compila el proyecto en un ejecutable .exe portable para USB.
    """
    # Ruta del script principal
    script_principal = "main.py"
    
    # Opciones de PyInstaller
    opciones = [
        "--noconfirm",           # No pedir confirmación para sobrescribir
        "--onefile",             # Un solo archivo .exe
        "--windowed",            # Sin consola negra (--noconsole es equivalente)
        "--icon=assets/logo.ico",  # Ícono del ejecutable
        "--add-data=assets;assets",  # Empaquetar carpeta assets
        "--collect-all", "customtkinter",  # Incluir explícitamente customtkinter
        script_principal
    ]
    
    # Ejecutar PyInstaller
    print("Iniciando compilación con PyInstaller...")
    PyInstaller.__main__.run(opciones)
    
    print("Compilación completada. El ejecutable se encuentra en la carpeta 'dist/'.")

if __name__ == "__main__":
    compilar_ejecutable()