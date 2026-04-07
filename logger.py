import logging
import os
from datetime import datetime

def setup_logging():
    """Configura el sistema de logging para la aplicación."""

    # Crear directorio de logs si no existe
    if not os.path.exists('logs'):
        os.makedirs('logs')

    # Nombre del archivo de log con fecha
    log_filename = f"logs/inventario_{datetime.now().strftime('%Y%m%d')}.log"

    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename, encoding='utf-8'),
            logging.StreamHandler()  # También mostrar en consola
        ]
    )

    # Crear logger específico de la aplicación
    logger = logging.getLogger('inventario_app')
    logger.info("Sistema de logging inicializado")

    return logger

# Logger global
logger = setup_logging()