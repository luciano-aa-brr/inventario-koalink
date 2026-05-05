import sqlite3
import os
import sys
import shutil
from datetime import datetime, timezone, timedelta

# Importar las nuevas utilidades
from config import Config
from utils import get_chile_time, format_chile_time, create_backup as utils_create_backup
from constants import Constants
from exceptions import DatabaseError
from logger import logger

# --- CONFIGURACIÓN MAESTRA DE CATEGORÍAS ---
# Si en el futuro quieres agregar algo nuevo, SOLO lo agregas aquí.
CATEGORIAS_PREFIJOS = Config.CATEGORIAS_PREFIJOS

def obtener_hora_chile():
    """Genera la hora exacta de Chile (UTC-3) para insertarla en la base de datos."""
    return format_chile_time(get_chile_time())

def crear_backup():
    """Crea una copia de seguridad de la base de datos."""
    try:
        success, result = utils_create_backup(Config.DB_PATH, Config.BACKUP_DIR)
        if success:
            logger.info(f"Backup creado exitosamente: {result}")
            return True, Constants.INFO_BACKUP_SUCCESS
        else:
            logger.error(f"Error al crear backup: {result}")
            return False, Constants.ERROR_BACKUP_FAILED
    except Exception as e:
        logger.error(f"Error inesperado al crear backup: {e}")
        return False, f"Error al crear backup: {e}"

from utils import get_resource_path

# Alias para compatibilidad
recurso_ruta = get_resource_path

def conectar_db():
    """Crea la carpeta data fuera del .exe y conecta a la base de datos."""
    
    # 1. Identificar la ruta donde vive el ejecutable (o el script .py)
    if getattr(sys, 'frozen', False):
        # Estamos en el ejecutable (.exe)
        ruta_base = os.path.dirname(sys.executable)
    else:
        # Estamos en modo desarrollo (Python)
        ruta_base = os.path.dirname(os.path.abspath(__file__))

    # 2. Definimos la ruta de la carpeta 'data' de forma externa
    ruta_carpeta_data = os.path.join(ruta_base, 'data')
    
    # 3. Creamos la carpeta si no existe (esto ocurrirá en la carpeta de tu programa)
    if not os.path.exists(ruta_carpeta_data):
        os.makedirs(ruta_carpeta_data)
    
    # 4. Definimos la ruta del archivo .db
    ruta_db = os.path.join(ruta_carpeta_data, 'inventario.db')
    
    # Esto imprimirá la ruta en la consola (útil para debuguear)
    print(f"Conectando a base de datos en: {ruta_db}")
    
    return sqlite3.connect(ruta_db)


# ==========================================
# --- PAGINACIÓN: FUNCIONES DE INVENTARIO ---
# ==========================================

def contar_articulos_con_stock(busqueda="", categoria="Todos"):
    """Cuenta el total de artículos que coinciden con la búsqueda para calcular las páginas."""
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        query = '''
            SELECT COUNT(DISTINCT a.codigo_barras)
            FROM articulos a
            LEFT JOIN detalle_prestamo dp ON a.codigo_barras = dp.codigo_articulo AND dp.fecha_devolucion_item IS NULL
            WHERE a.estado != 'De Baja'
        '''
        params = []
        if busqueda:
            query += " AND (a.nombre LIKE ? OR a.codigo_barras LIKE ?)"
            termino = f"%{busqueda}%"
            params.extend([termino, termino])
        if categoria != "Todos":
            query += " AND a.categoria = ?"
            params.append(categoria)
            
        cursor.execute(query, params)
        total = cursor.fetchone()[0]
        conn.close()
        return total
    except Exception as e:
        return 0

def obtener_articulos_con_stock(busqueda="", categoria="Todos", limite=50, offset=0):
    """Obtiene un fragmento (página) específico del inventario."""
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        query = '''
            SELECT 
                a.codigo_barras, a.nombre, a.ubicacion, a.cantidad AS stock_total,
                COALESCE(SUM(dp.cantidad_prestada), 0) AS en_prestamo,
                a.cantidad - COALESCE(SUM(dp.cantidad_prestada), 0) AS disponibles
            FROM articulos a
            LEFT JOIN detalle_prestamo dp ON a.codigo_barras = dp.codigo_articulo AND dp.fecha_devolucion_item IS NULL
            WHERE a.estado != 'De Baja'
        '''
        params = []
        if busqueda:
            query += " AND (a.nombre LIKE ? OR a.codigo_barras LIKE ?)"
            termino = f"%{busqueda}%"
            params.extend([termino, termino])
        if categoria != "Todos":
            query += " AND a.categoria = ?"
            params.append(categoria)
            
        # MAGIA AQUÍ: Agregamos LIMIT y OFFSET
        query += " GROUP BY a.codigo_barras ORDER BY a.nombre ASC LIMIT ? OFFSET ?"
        params.extend([limite, offset])
        
        cursor.execute(query, params)
        articulos = cursor.fetchall()
        conn.close()
        return articulos
    except Exception as e:
        return []


# ==========================================
# --- PAGINACIÓN: FUNCIONES DE INACTIVOS ---
# ==========================================

def contar_articulos_inactivos():
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        query = '''SELECT COUNT(*) FROM (
                    SELECT b.codigo_articulo FROM bajas b
                    GROUP BY b.codigo_articulo HAVING SUM(b.cantidad_baja) > 0
                   )'''
        cursor.execute(query)
        total = cursor.fetchone()[0]
        conn.close()
        return total
    except Exception:
        return 0

def obtener_articulos_inactivos_reporte(limite=50, offset=0):
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        query = '''
            SELECT 
                b.codigo_articulo, a.nombre, 
                (SELECT motivo FROM bajas WHERE codigo_articulo = b.codigo_articulo AND cantidad_baja > 0 ORDER BY fecha_baja DESC LIMIT 1) AS ultimo_motivo,
                SUM(b.cantidad_baja) AS stock_en_baja, 
                (SELECT fecha_baja FROM bajas WHERE codigo_articulo = b.codigo_articulo AND cantidad_baja > 0 ORDER BY fecha_baja DESC LIMIT 1) AS ultima_fecha
            FROM bajas b
            JOIN articulos a ON b.codigo_articulo = a.codigo_barras
            GROUP BY b.codigo_articulo
            HAVING stock_en_baja > 0
            ORDER BY ultima_fecha DESC
            LIMIT ? OFFSET ?
        '''
        cursor.execute(query, (limite, offset))
        items = cursor.fetchall()
        conn.close()
        return items
    except Exception:
        return []
    
def inicializar_tablas():
    """Crea las tablas desde cero con la estructura de stock."""
    conn = conectar_db()
    cursor = conn.cursor()
    
    # Tabla de Artículos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS articulos (
            codigo_barras TEXT PRIMARY KEY,
            nombre TEXT NOT NULL,
            categoria TEXT,
            estado TEXT DEFAULT 'Disponible',
            ubicacion TEXT,
            cantidad INTEGER DEFAULT 1
        )
    ''')

    # NUEVA TABLA: préstamos (Cabecera del movimiento)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS prestamos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            responsable TEXT NOT NULL,
            destino TEXT,
            tipo_usuario TEXT, -- Estudiante o Funcionario
            fecha_salida DATETIME DEFAULT CURRENT_TIMESTAMP,
            fecha_retorno DATETIME -- Fecha general de devolución (si se devuelve todo junto)
        )
    ''')

    # NUEVA TABLA: detalle_prestamo (Lista de artículos por préstamo)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS detalle_prestamo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_prestamo INTEGER, -- Enlace a la tabla prestamos
            codigo_articulo TEXT,
            cantidad_prestada INTEGER,
            fecha_devolucion_item DATETIME, -- Por si devuelve cosas por separado
            FOREIGN KEY(id_prestamo) REFERENCES prestamos(id),
            FOREIGN KEY(codigo_articulo) REFERENCES articulos(codigo_barras)
        )
    ''')

    # Tabla de Movimientos (Préstamos)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS movimientos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_articulo TEXT,
            responsable TEXT,
            destino TEXT,
            fecha_salida DATETIME DEFAULT CURRENT_TIMESTAMP,
            fecha_retorno DATETIME,
            FOREIGN KEY(codigo_articulo) REFERENCES articulos(codigo_barras)
        )
    ''')

    # ============ NUEVAS TABLAS PARA LIBROS CON IDENTIFICACIÓN INDIVIDUAL ============
    
    # Tabla de Libros (títulos/códigos de libros)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS libros (
            codigo_libro TEXT PRIMARY KEY,
            nombre TEXT NOT NULL,
            autor TEXT,
            categoria TEXT DEFAULT 'Libro',
            ubicacion TEXT,
            fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Tabla de Copias de Libros (cada copia física con número de serie único)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS copias_libro (
            numero_serie TEXT PRIMARY KEY,
            codigo_libro TEXT NOT NULL,
            estado TEXT DEFAULT 'Disponible',
            fecha_adquisicion DATETIME DEFAULT CURRENT_TIMESTAMP,
            observaciones TEXT,
            FOREIGN KEY(codigo_libro) REFERENCES libros(codigo_libro)
        )
    ''')

    # Tabla de Préstamos de Copias Individuales
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS prestamos_libro (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_serie TEXT NOT NULL,
            responsable TEXT NOT NULL,
            destino TEXT,
            tipo_usuario TEXT,
            fecha_salida DATETIME DEFAULT CURRENT_TIMESTAMP,
            fecha_devolucion DATETIME,
            FOREIGN KEY(numero_serie) REFERENCES copias_libro(numero_serie)
        )
    ''')

    conn.commit()
    conn.close()


def obtener_articulo_por_codigo(codigo):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("SELECT nombre, codigo_barras FROM articulos WHERE codigo_barras = ?", (codigo,))
    res = cursor.fetchone()
    conn.close()
    return res

# --- FUNCIONES PARA EL DASHBOARD (DATOS REALES) ---

def contar_items_totales():
    conn = conectar_db()
    res = conn.execute("SELECT SUM(cantidad) FROM articulos").fetchone()[0]
    conn.close()
    return res if res else 0

def contar_items_prestados():
    conn = conectar_db()
    res = conn.execute("SELECT COUNT(*) FROM movimientos WHERE fecha_retorno IS NULL").fetchone()[0]
    conn.close()
    return res if res else 0

def contar_stock_critico():
    conn = conectar_db()
    # Alerta si quedan menos de 3 unidades en Libros o Materiales
    res = conn.execute("SELECT COUNT(*) FROM articulos WHERE cantidad < 3 AND categoria IN ('Libro', 'Material Didáctico')").fetchone()[0]
    conn.close()
    return res if res else 0

def guardar_item_db(codigo, nombre, categoria, ubicacion, cantidad):

    """
    Registra un item. 
    Si el código ya existe (como en libros), suma la cantidad al stock.
    Si es nuevo, lo crea.
    """
    
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        
        # Primero revisamos si el código ya existe
        cursor.execute("SELECT cantidad FROM articulos WHERE codigo_barras = ?", (codigo,))
        resultado = cursor.fetchone()
        
        if resultado:
            # Si existe, sumamos la nueva cantidad al stock actual
            nueva_cantidad = resultado[0] + cantidad
            cursor.execute("UPDATE articulos SET cantidad = ? WHERE codigo_barras = ?", (nueva_cantidad, codigo))
            mensaje = f"Stock actualizado: ahora hay {nueva_cantidad} unidades."
        else:
            # Si no existe, lo creamos desde cero
            query = '''INSERT INTO articulos (codigo_barras, nombre, categoria, estado, ubicacion, cantidad) 
                       VALUES (?, ?, ?, 'Disponible', ?, ?)'''
            cursor.execute(query, (codigo, nombre, categoria, ubicacion, cantidad))
            mensaje = "Nuevo artículo registrado con éxito."
            
        conn.commit()
        conn.close()
        return True, mensaje
    except Exception as e:
        print(f"Error al guardar: {e}")
        return False, str(e)
    
def generar_siguiente_codigo(categoria):
    """Genera el código automáticamente leyendo el diccionario maestro."""
    # Lee el prefijo directamente de la configuración maestra
    prefijo = CATEGORIAS_PREFIJOS.get(categoria, "EQU") # EQU si no existe
    
    conn = conectar_db()
    cursor = conn.cursor()
    
    cursor.execute(f"SELECT codigo_barras FROM articulos WHERE codigo_barras LIKE '{prefijo}-%' ORDER BY codigo_barras DESC LIMIT 1")
    ultimo = cursor.fetchone()
    conn.close()

    if ultimo:
        ultimo_num = int(ultimo[0].split("-")[1])
        nuevo_num = ultimo_num + 1
    else:
        nuevo_num = 1
        
    return f"{prefijo}-{nuevo_num:03d}"

def obtener_articulos_inventario_completo(categoria="Todos", mostrar_inactivos=False):
    conn = conectar_db()
    cursor = conn.cursor()
    
    # Usamos GROUP BY para unificar por código de barras
    # GROUP_CONCAT junta todos los responsables en un solo texto separado por comas
    query = '''
        SELECT 
            a.codigo_barras, 
            a.nombre, 
            a.categoria, 
            a.estado, 
            a.ubicacion, 
            a.cantidad,
            GROUP_CONCAT(p.responsable, ', ') as responsables,
            GROUP_CONCAT(p.destino, ', ') as destinos,
            a.estado -- repetimos para mantener la estructura de la tupla si es necesario
        FROM articulos a
        LEFT JOIN detalle_prestamo dp ON a.codigo_barras = dp.codigo_articulo AND dp.fecha_devolucion_item IS NULL
        LEFT JOIN prestamos p ON dp.id_prestamo = p.id
        WHERE 1=1
    '''
    
    if categoria != "Todos":
        query += " AND a.categoria = ?"
    
    if not mostrar_inactivos:
        query += " AND a.estado != 'Inactivo'"
    else:
        query += " AND a.estado = 'Inactivo'"

    # ESTA ES LA CLAVE: Agrupa todo lo que tenga el mismo código
    query += " GROUP BY a.codigo_barras"

    if categoria != "Todos":
        cursor.execute(query, (categoria,))
    else:
        cursor.execute(query)
        
    items = cursor.fetchall()
    conn.close()
    return items


    
def dar_de_baja_db(codigo, cantidad_baja, motivo="Baja de Inventario"):
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        
        cursor.execute("SELECT cantidad, nombre FROM articulos WHERE codigo_barras = ?", (codigo,))
        res = cursor.fetchone()
        if not res or res[0] < cantidad_baja:
            conn.close()
            return False, "Error: No puedes dar de baja más de lo que hay en stock."
        
        nombre_art = res[1]

        cursor.execute("UPDATE articulos SET cantidad = cantidad - ? WHERE codigo_barras = ?", (cantidad_baja, codigo))
        cursor.execute("UPDATE articulos SET estado = 'Inactivo' WHERE codigo_barras = ? AND cantidad <= 0", (codigo,))

        hora_exacta = obtener_hora_chile()
        
        # Insertar con hora forzada
        cursor.execute("INSERT INTO bajas (codigo_articulo, cantidad_baja, motivo, fecha_baja) VALUES (?, ?, ?, ?)", 
                       (codigo, cantidad_baja, motivo, hora_exacta))
        
        conn.commit()
        conn.close()
        return True, f"Baja exitosa de {cantidad_baja} unidades de {nombre_art}."
    except Exception as e:
        return False, str(e)
    
def actualizar_articulo_db(codigo, nombre, categoria, ubicacion, cantidad):
    """Actualiza la información técnica y de stock de un artículo."""
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        cursor.execute('''UPDATE articulos 
                          SET nombre = ?, categoria = ?, ubicacion = ?, cantidad = ? 
                          WHERE codigo_barras = ?''', 
                       (nombre, categoria, ubicacion, cantidad, codigo))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error al actualizar: {e}")
        return False

def reactivar_item_db(codigo, cantidad_a_recuperar):
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        
        cursor.execute("SELECT SUM(cantidad_baja) FROM bajas WHERE codigo_articulo = ?", (codigo,))
        total_en_baja = cursor.fetchone()[0] or 0
        
        if cantidad_a_recuperar > total_en_baja:
            conn.close()
            return False, "No puedes reactivar más de lo que se dio de baja."

        cursor.execute("UPDATE articulos SET cantidad = cantidad + ?, estado = 'Disponible' WHERE codigo_barras = ?", 
                       (cantidad_a_recuperar, codigo))
        
        hora_exacta = obtener_hora_chile()
        
        cursor.execute("INSERT INTO bajas (codigo_articulo, cantidad_baja, motivo, fecha_baja) VALUES (?, ?, ?, ?)", 
                       (codigo, -cantidad_a_recuperar, "Reactivación", hora_exacta))
        
        conn.commit()
        conn.close()
        return True, "Equipos reactivados correctamente."
    except Exception as e:
        return False, str(e)
    
def registrar_prestamo_multiple(responsable, destino, tipo_usuario, lista_carrito):
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        
        # 1. VALIDACIÓN PREVIA
        for item in lista_carrito:
            cursor.execute("SELECT cantidad, nombre FROM articulos WHERE codigo_barras = ?", (item["codigo"],))
            resultado = cursor.fetchone()
            
            if not resultado:
                return False, f"El artículo {item['codigo']} no existe."
            
            stock_actual, nombre_art = resultado
            if stock_actual < item["cantidad"]:
                return False, f"¡Error! No hay suficiente stock de '{nombre_art}'.\nDisponible: {stock_actual}"

        # 2. Registrar el préstamo con la HORA EXACTA DE CHILE
        hora_exacta = obtener_hora_chile()
        cursor.execute('''INSERT INTO prestamos (responsable, destino, tipo_usuario, fecha_salida) 
                          VALUES (?, ?, ?, ?)''', (responsable, destino, tipo_usuario, hora_exacta))
        id_prestamo = cursor.lastrowid

        for item in lista_carrito:
            cursor.execute("UPDATE articulos SET cantidad = cantidad - ? WHERE codigo_barras = ?", 
                           (item["cantidad"], item["codigo"]))
            cursor.execute("UPDATE articulos SET estado = 'Prestado' WHERE cantidad = 0 AND codigo_barras = ?", 
                           (item["codigo"],))
            cursor.execute('''INSERT INTO detalle_prestamo (id_prestamo, codigo_articulo, cantidad_prestada) 
                              VALUES (?, ?, ?)''', (id_prestamo, item["codigo"], item["cantidad"]))

        conn.commit()
        conn.close()
        return True, "Préstamo registrado correctamente."
    except Exception as e:
        return False, f"Error crítico: {e}"
    
def obtener_info_individual(codigo):
    """Devuelve info básica de un artículo para validación rápida."""
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("SELECT nombre, cantidad, categoria FROM articulos WHERE codigo_barras = ?", (codigo,))
    res = cursor.fetchone()
    conn.close()
    if res:
        return {"encontrado": True, "nombre": res[0], "cantidad": res[1], "categoria": res[2]}
    return {"encontrado": False}

def registrar_devolucion_db(codigo, cantidad_devuelta):
    """Registra el retorno de material, actualiza stock y cierra el movimiento."""
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        
        # 1. Buscar el préstamo más antiguo sin devolver para ese código
        cursor.execute('''SELECT id FROM movimientos 
                          WHERE codigo_articulo = ? AND fecha_retorno IS NULL 
                          ORDER BY fecha_salida ASC LIMIT 1''', (codigo,))
        movimiento = cursor.fetchone()
        
        if not movimiento:
            return False, "Este artículo no figura como prestado."

        # 2. Actualizar la fecha de retorno en el historial
        cursor.execute("UPDATE movimientos SET fecha_retorno = CURRENT_TIMESTAMP WHERE id = ?", (movimiento[0],))

        # 3. Devolver el stock al artículo
        cursor.execute("SELECT cantidad, nombre FROM articulos WHERE codigo_barras = ?", (codigo,))
        art = cursor.fetchone()
        nueva_cantidad = art[0] + cantidad_devuelta
        
        # Siempre vuelve a estar "Disponible" al recibir stock
        cursor.execute("UPDATE articulos SET cantidad = ?, estado = 'Disponible' WHERE codigo_barras = ?", 
                       (nueva_cantidad, codigo))
        
        conn.commit()
        conn.close()
        return True, f"'{art[1]}' devuelto al inventario (Stock: {nueva_cantidad})."
    except Exception as e:
        return False, str(e)
    
def obtener_detalles_prestados(busqueda=""):
    """Trae la lista de artículos individuales que están actualmente en préstamo."""
    conn = conectar_db()
    cursor = conn.cursor()
    
    # Buscamos en detalle_prestamo los que NO tienen fecha de devolución
    query = '''
        SELECT dp.id, a.codigo_barras, a.nombre, p.responsable, p.destino, dp.cantidad_prestada
        FROM detalle_prestamo dp
        JOIN prestamos p ON dp.id_prestamo = p.id
        JOIN articulos a ON dp.codigo_articulo = a.codigo_barras
        WHERE dp.fecha_devolucion_item IS NULL
    '''
    params = []
    if busqueda:
        query += " AND (a.nombre LIKE ? OR p.responsable LIKE ? OR a.codigo_barras LIKE ?)"
        term = f"%{busqueda}%"
        params = [term, term, term]

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return rows

def registrar_devolucion_item_db(id_detalle, codigo_art, cantidad_regresada):
    """Procesa la devolución y maneja si es total o parcial con hora local."""
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        
        cursor.execute("SELECT cantidad_prestada FROM detalle_prestamo WHERE id = ?", (id_detalle,))
        cant_original = cursor.fetchone()[0]

        hora_exacta = obtener_hora_chile() # Hora de recepción

        if cantidad_regresada >= cant_original:
            # DEVOLUCIÓN TOTAL: Cerramos el registro con hora de Chile
            cursor.execute('''UPDATE detalle_prestamo 
                              SET fecha_devolucion_item = ? 
                              WHERE id = ?''', (hora_exacta, id_detalle))
        else:
            # DEVOLUCIÓN PARCIAL
            nueva_cant_pendiente = cant_original - cantidad_regresada
            cursor.execute('''UPDATE detalle_prestamo 
                              SET cantidad_prestada = ? 
                              WHERE id = ?''', (nueva_cant_pendiente, id_detalle))
        
        cursor.execute("UPDATE articulos SET cantidad = cantidad + ? WHERE codigo_barras = ?", 
                       (cantidad_regresada, codigo_art))
        cursor.execute("UPDATE articulos SET estado = 'Disponible' WHERE codigo_barras = ?", (codigo_art,))
        
        conn.commit()
        conn.close()
        return True, "Operación exitosa"
    except Exception as e:
        return False, str(e)
    
def obtener_historial_activos_db(busqueda="", categoria="Todos"):
    """Trae los registros activos incluyendo el ID del préstamo para poder editarlo."""
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        query = '''
            SELECT 
                a.nombre, 
                p.responsable, 
                p.destino, 
                p.tipo_usuario,
                dp.cantidad_prestada, 
                p.fecha_salida,
                a.codigo_barras,
                p.id  -- <--- AGREGAMOS EL ID AL FINAL
            FROM detalle_prestamo dp
            JOIN prestamos p ON dp.id_prestamo = p.id
            JOIN articulos a ON dp.codigo_articulo = a.codigo_barras
            WHERE dp.fecha_devolucion_item IS NULL
        '''
        params = []
        if busqueda:
            query += " AND (a.nombre LIKE ? OR p.responsable LIKE ? OR a.codigo_barras LIKE ?)"
            termino = f"%{busqueda}%"
            params.extend([termino, termino, termino])
        if categoria != "Todos":
            query += " AND a.categoria = ?"
            params.append(categoria)
        query += " ORDER BY p.fecha_salida DESC"
        cursor.execute(query, params)
        datos = cursor.fetchall()
        conn.close()
        return datos
    except Exception as e:
        print(f"Error en historial: {e}")
        return []
    
def crear_tabla_bajas():
    """Crea la tabla para rastrear elementos fuera de inventario."""
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bajas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_articulo TEXT,
            cantidad_baja INTEGER,
            motivo TEXT,
            fecha_baja TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (codigo_articulo) REFERENCES articulos(codigo_barras)
        )
    ''')
    conn.commit()
    conn.close()

def actualizar_info_prestamo_db(id_prestamo, nuevo_resp, nuevo_dest, nuevo_tipo):
    """Actualiza la información de texto de un préstamo activo."""
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        cursor.execute('''UPDATE prestamos 
                          SET responsable = ?, destino = ?, tipo_usuario = ? 
                          WHERE id = ?''', 
                       (nuevo_resp, nuevo_dest, nuevo_tipo, id_prestamo))
        conn.commit()
        conn.close()
        return True, "Información del préstamo actualizada."
    except Exception as e:
        return False, str(e)


# ========== FUNCIONES PARA LIBROS CON IDENTIFICACIÓN INDIVIDUAL ==========

def generar_codigo_libro(categoria="Libro"):
    """Genera un código único para un nuevo libro (título)."""
    prefijo = CATEGORIAS_PREFIJOS.get(categoria, "LIB")
    conn = conectar_db()
    cursor = conn.cursor()
    
    cursor.execute(f"SELECT codigo_libro FROM libros WHERE codigo_libro LIKE '{prefijo}-%' ORDER BY codigo_libro DESC LIMIT 1")
    ultimo = cursor.fetchone()
    conn.close()
    
    if ultimo:
        ultimo_num = int(ultimo[0].split("-")[1])
        nuevo_num = ultimo_num + 1
    else:
        nuevo_num = 1
    
    return f"{prefijo}-{nuevo_num:03d}"


def registrar_libro_db(codigo_libro, nombre, autor, ubicacion, cantidad_copias):
    """
    Registra un nuevo libro (título) y crea automáticamente sus copias con números de serie.
    
    Args:
        codigo_libro: Código del libro (ej: LIB-001)
        nombre: Nombre/título del libro
        autor: Autor del libro
        ubicacion: Ubicación física
        cantidad_copias: Cantidad de copias a registrar
    
    Returns:
        (success: bool, message: str)
    """
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        
        # 1. Verificar si el libro ya existe
        cursor.execute("SELECT codigo_libro FROM libros WHERE codigo_libro = ?", (codigo_libro,))
        if cursor.fetchone():
            conn.close()
            return False, f"El código {codigo_libro} ya está registrado."
        
        # 2. Registrar el libro (título)
        hora_exacta = obtener_hora_chile()
        cursor.execute('''INSERT INTO libros (codigo_libro, nombre, autor, ubicacion, fecha_registro) 
                          VALUES (?, ?, ?, ?, ?)''', 
                       (codigo_libro, nombre, autor, ubicacion, hora_exacta))
        
        # 3. Crear las copias individuales con números de serie
        copias_creadas = []
        for i in range(1, cantidad_copias + 1):
            numero_serie = f"{codigo_libro}-{i:02d}"
            cursor.execute('''INSERT INTO copias_libro (numero_serie, codigo_libro, fecha_adquisicion) 
                              VALUES (?, ?, ?)''', 
                           (numero_serie, codigo_libro, hora_exacta))
            copias_creadas.append(numero_serie)
        
        conn.commit()
        conn.close()
        
        return True, f"Libro '{nombre}' registrado con {cantidad_copias} copias.\nNúmeros de serie: {', '.join(copias_creadas)}"
    except Exception as e:
        return False, f"Error al registrar libro: {e}"


def agregar_copias_libro_db(codigo_libro, cantidad_nuevas):
    """
    Agrega más copias a un libro existente.
    
    Args:
        codigo_libro: Código del libro
        cantidad_nuevas: Cantidad de copias a agregar
    
    Returns:
        (success: bool, message: str, copias_nuevas: list)
    """
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        
        # 1. Verificar que el libro existe
        cursor.execute("SELECT nombre FROM libros WHERE codigo_libro = ?", (codigo_libro,))
        resultado = cursor.fetchone()
        if not resultado:
            conn.close()
            return False, f"El libro con código {codigo_libro} no existe.", []
        
        nombre_libro = resultado[0]
        
        # 2. Obtener el siguiente número de serie
        cursor.execute("SELECT numero_serie FROM copias_libro WHERE codigo_libro = ? ORDER BY numero_serie DESC LIMIT 1", 
                       (codigo_libro,))
        ultima_copia = cursor.fetchone()
        
        if ultima_copia:
            ultimo_num = int(ultima_copia[0].split("-")[-1])
            siguiente_num = ultimo_num + 1
        else:
            siguiente_num = 1
        
        # 3. Crear las nuevas copias
        hora_exacta = obtener_hora_chile()
        copias_nuevas = []
        
        for i in range(siguiente_num, siguiente_num + cantidad_nuevas):
            numero_serie = f"{codigo_libro}-{i:02d}"
            cursor.execute('''INSERT INTO copias_libro (numero_serie, codigo_libro, fecha_adquisicion) 
                              VALUES (?, ?, ?)''', 
                           (numero_serie, codigo_libro, hora_exacta))
            copias_nuevas.append(numero_serie)
        
        conn.commit()
        conn.close()
        
        return True, f"Se agregaron {cantidad_nuevas} copias a '{nombre_libro}'.", copias_nuevas
    except Exception as e:
        return False, f"Error al agregar copias: {e}", []


def obtener_copias_libro_db(codigo_libro):
    """
    Obtiene todas las copias de un libro con su estado.
    
    Returns:
        list: [(numero_serie, estado, responsable_actual, fecha_prestamo), ...]
    """
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        
        query = '''
            SELECT 
                cl.numero_serie,
                cl.estado,
                COALESCE(pl.responsable, 'Sin préstamo') as responsable,
                COALESCE(pl.fecha_salida, 'N/A') as fecha_prestamo
            FROM copias_libro cl
            LEFT JOIN prestamos_libro pl ON cl.numero_serie = pl.numero_serie AND pl.fecha_devolucion IS NULL
            WHERE cl.codigo_libro = ?
            ORDER BY cl.numero_serie
        '''
        
        cursor.execute(query, (codigo_libro,))
        copias = cursor.fetchall()
        conn.close()
        
        return copias
    except Exception as e:
        logger.error(f"Error obteniendo copias: {e}")
        return []


def obtener_libros_db(busqueda=""):
    """
    Obtiene todos los libros con resumen de copias.
    
    Returns:
        list: [(codigo_libro, nombre, autor, total_copias, disponibles, prestadas), ...]
    """
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        
        query = '''
            SELECT 
                l.codigo_libro,
                l.nombre,
                l.autor,
                COUNT(cl.numero_serie) as total_copias,
                SUM(CASE WHEN cl.estado = 'Disponible' THEN 1 ELSE 0 END) as disponibles,
                SUM(CASE WHEN cl.estado = 'Prestado' THEN 1 ELSE 0 END) as prestadas
            FROM libros l
            LEFT JOIN copias_libro cl ON l.codigo_libro = cl.codigo_libro
        '''
        
        params = []
        if busqueda:
            query += " WHERE l.nombre LIKE ? OR l.codigo_libro LIKE ? OR l.autor LIKE ?"
            termino = f"%{busqueda}%"
            params = [termino, termino, termino]
        
        query += " GROUP BY l.codigo_libro ORDER BY l.nombre"
        
        cursor.execute(query, params)
        libros = cursor.fetchall()
        conn.close()
        
        return libros
    except Exception as e:
        logger.error(f"Error obteniendo libros: {e}")
        return []


def prestar_copia_libro_db(numero_serie, responsable, destino, tipo_usuario):
    """
    Registra el préstamo de una copia específica de un libro.
    
    Args:
        numero_serie: Número de serie de la copia (ej: LIB-001-01)
        responsable: Nombre de quien recibe el libro
        destino: Lugar de destino
        tipo_usuario: 'Estudiante' o 'Funcionario'
    
    Returns:
        (success: bool, message: str)
    """
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        
        # 1. Verificar que la copia existe y está disponible
        cursor.execute("SELECT estado, codigo_libro FROM copias_libro WHERE numero_serie = ?", (numero_serie,))
        resultado = cursor.fetchone()
        
        if not resultado:
            conn.close()
            return False, f"La copia {numero_serie} no existe."
        
        estado, codigo_libro = resultado
        if estado != 'Disponible':
            conn.close()
            return False, f"La copia {numero_serie} no está disponible (estado: {estado})."
        
        # 2. Registrar el préstamo
        hora_exacta = obtener_hora_chile()
        cursor.execute('''INSERT INTO prestamos_libro (numero_serie, responsable, destino, tipo_usuario, fecha_salida)
                          VALUES (?, ?, ?, ?, ?)''',
                       (numero_serie, responsable, destino, tipo_usuario, hora_exacta))
        
        # 3. Actualizar estado de la copia
        cursor.execute("UPDATE copias_libro SET estado = 'Prestado' WHERE numero_serie = ?", (numero_serie,))
        
        conn.commit()
        conn.close()
        
        return True, f"Copia {numero_serie} prestada a {responsable}."
    except Exception as e:
        return False, f"Error al prestar copia: {e}"


def devolver_copia_libro_db(numero_serie):
    """
    Registra la devolución de una copia de un libro.
    
    Args:
        numero_serie: Número de serie de la copia a devolver
    
    Returns:
        (success: bool, message: str, info_prestamo: dict)
    """
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        
        # 1. Buscar el préstamo activo
        cursor.execute('''SELECT id, responsable, fecha_salida FROM prestamos_libro 
                          WHERE numero_serie = ? AND fecha_devolucion IS NULL''',
                       (numero_serie,))
        prestamo = cursor.fetchone()
        
        if not prestamo:
            conn.close()
            return False, f"La copia {numero_serie} no tiene préstamos activos.", {}
        
        id_prestamo, responsable, fecha_salida = prestamo
        
        # 2. Registrar la devolución
        hora_exacta = obtener_hora_chile()
        cursor.execute("UPDATE prestamos_libro SET fecha_devolucion = ? WHERE id = ?",
                       (hora_exacta, id_prestamo))
        
        # 3. Actualizar estado de la copia
        cursor.execute("UPDATE copias_libro SET estado = 'Disponible' WHERE numero_serie = ?", 
                       (numero_serie,))
        
        conn.commit()
        conn.close()
        
        info_prestamo = {
            'numero_serie': numero_serie,
            'responsable': responsable,
            'fecha_salida': fecha_salida,
            'fecha_devolucion': hora_exacta
        }
        
        return True, f"Copia {numero_serie} devuelta por {responsable}.", info_prestamo
    except Exception as e:
        return False, f"Error al devolver copia: {e}", {}


def obtener_historial_copia_libro_db(numero_serie):
    """
    Obtiene el historial completo de préstamos de una copia.
    
    Args:
        numero_serie: Número de serie de la copia
    
    Returns:
        list: [(id, responsable, destino, tipo_usuario, fecha_salida, fecha_devolucion), ...]
    """
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        
        cursor.execute('''SELECT id, responsable, destino, tipo_usuario, fecha_salida, fecha_devolucion
                          FROM prestamos_libro
                          WHERE numero_serie = ?
                          ORDER BY fecha_salida DESC''',
                       (numero_serie,))
        historial = cursor.fetchall()
        conn.close()
        
        return historial
    except Exception as e:
        logger.error(f"Error obteniendo historial: {e}")
        return []


def buscar_copia_por_numero_serie_db(numero_serie):
    """
    Busca una copia específica y retorna toda su información.
    
    Returns:
        dict: {'encontrado': bool, 'numero_serie': str, 'codigo_libro': str, 
               'nombre_libro': str, 'estado': str, 'responsable': str, ...}
    """
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        
        query = '''
            SELECT 
                cl.numero_serie,
                cl.codigo_libro,
                l.nombre,
                l.autor,
                cl.estado,
                COALESCE(pl.responsable, 'Sin préstamo') as responsable,
                COALESCE(pl.destino, 'N/A') as destino,
                COALESCE(pl.fecha_salida, 'N/A') as fecha_salida
            FROM copias_libro cl
            JOIN libros l ON cl.codigo_libro = l.codigo_libro
            LEFT JOIN prestamos_libro pl ON cl.numero_serie = pl.numero_serie AND pl.fecha_devolucion IS NULL
            WHERE cl.numero_serie = ?
        '''
        
        cursor.execute(query, (numero_serie,))
        resultado = cursor.fetchone()
        conn.close()
        
        if resultado:
            return {
                'encontrado': True,
                'numero_serie': resultado[0],
                'codigo_libro': resultado[1],
                'nombre_libro': resultado[2],
                'autor': resultado[3],
                'estado': resultado[4],
                'responsable': resultado[5],
                'destino': resultado[6],
                'fecha_salida': resultado[7]
            }
        else:
            return {'encontrado': False}
    except Exception as e:
        logger.error(f"Error buscando copia: {e}")
        return {'encontrado': False}