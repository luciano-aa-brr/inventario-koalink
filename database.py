import sqlite3
import os
import sys

def recurso_ruta(relative_path):
    """ Gestiona rutas para el .exe """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

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
    conn.commit()
    conn.close()

def obtener_articulos_inactivos_reporte():
    """Trae los datos de la tabla 'bajas' sumados por código."""
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        # Sumamos las bajas para mostrar el total acumulado de ese ítem
        query = '''
            SELECT 
                b.codigo_articulo, 
                a.nombre, 
                'Inactivo' as estado, 
                SUM(b.cantidad_baja) as stock_en_baja, 
                'Bodega' as ubicacion
            FROM bajas b
            JOIN articulos a ON b.codigo_articulo = a.codigo_barras
            GROUP BY b.codigo_articulo
            HAVING stock_en_baja > 0
        '''
        cursor.execute(query)
        items = cursor.fetchall()
        conn.close()
        return items
    except Exception as e:
        print(f"Error en consulta de inactivos: {e}")
        return []

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
    """
    Busca el último código en la DB según la categoría y entrega el siguiente.
    Ejemplo: Si el último es TAB-010, entrega TAB-011.
    """
    prefijos = {
        "Tablet": "TAB",
        "Notebook": "NOTE",
        "Libro": "LIB",
        "Material Didáctico": "MAT",
        "Impresora": "IMP"
    }
    prefijo = prefijos.get(categoria, "EQU") # EQU por defecto si no coincide
    
    conn = conectar_db()
    cursor = conn.cursor()
    
    # Buscamos el código más alto que empiece con ese prefijo
    cursor.execute(f"SELECT codigo_barras FROM articulos WHERE codigo_barras LIKE '{prefijo}-%' ORDER BY codigo_barras DESC LIMIT 1")
    ultimo = cursor.fetchone()
    conn.close()

    if ultimo:
        # Extraemos el número después del guion y sumamos 1
        ultimo_num = int(ultimo[0].split("-")[1])
        nuevo_num = ultimo_num + 1
    else:
        # Si es el primero de esa categoría
        nuevo_num = 1
        
    return f"{prefijo}-{nuevo_num:03d}" # Formato: TAB-001

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
        
        # 1. Verificar stock real antes de restar
        cursor.execute("SELECT cantidad, nombre FROM articulos WHERE codigo_barras = ?", (codigo,))
        res = cursor.fetchone()
        if not res or res[0] < cantidad_baja:
            conn.close()
            return False, "Error: No puedes dar de baja más de lo que hay en stock."
        
        nombre_art = res[1]

        # 2. Restar del inventario (Nunca bajará de 0 por la validación anterior)
        cursor.execute("UPDATE articulos SET cantidad = cantidad - ? WHERE codigo_barras = ?", (cantidad_baja, codigo))
        
        # 3. Si el stock llegó a 0, marcar como Inactivo automáticamente
        cursor.execute("UPDATE articulos SET estado = 'Inactivo' WHERE codigo_barras = ? AND cantidad <= 0", (codigo,))

        # 4. REGISTRAR EN TABLA BAJAS (Para que se vea en el apartado Inactivos)
        cursor.execute("INSERT INTO bajas (codigo_articulo, cantidad_baja, motivo) VALUES (?, ?, ?)", 
                       (codigo, cantidad_baja, motivo))
        
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
        
        # 1. ¿Hay suficientes en la tabla de bajas para reactivar?
        cursor.execute("SELECT SUM(cantidad_baja) FROM bajas WHERE codigo_articulo = ?", (codigo,))
        total_en_baja = cursor.fetchone()[0] or 0
        
        if cantidad_a_recuperar > total_en_baja:
            conn.close()
            return False, "No puedes reactivar más de lo que se dio de baja."

        # 2. Devolver al stock principal y poner estado Disponible
        cursor.execute("UPDATE articulos SET cantidad = cantidad + ?, estado = 'Disponible' WHERE codigo_barras = ?", 
                       (cantidad_a_recuperar, codigo))
        
        # 3. Restar de la tabla de bajas (insertando un registro negativo para balancear)
        cursor.execute("INSERT INTO bajas (codigo_articulo, cantidad_baja, motivo) VALUES (?, ?, ?)", 
                       (codigo, -cantidad_a_recuperar, "Reactivación"))
        
        conn.commit()
        conn.close()
        return True, "Equipos reactivados correctamente."
    except Exception as e:
        return False, str(e)
    
def registrar_prestamo_multiple(responsable, destino, tipo_usuario, lista_carrito):
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        
        # 1. VALIDACIÓN PREVIA: Revisar que TODO el carrito tenga stock
        for item in lista_carrito:
            cursor.execute("SELECT cantidad, nombre FROM articulos WHERE codigo_barras = ?", (item["codigo"],))
            resultado = cursor.fetchone()
            
            if not resultado:
                return False, f"El artículo {item['codigo']} no existe."
            
            stock_actual, nombre_art = resultado
            if stock_actual < item["cantidad"]:
                return False, f"¡Error! No hay suficiente stock de '{nombre_art}'.\nDisponible: {stock_actual}"

        # 2. Si llegamos aquí, hay stock de todo. Procedemos a registrar.
        cursor.execute('''INSERT INTO prestamos (responsable, destino, tipo_usuario) 
                          VALUES (?, ?, ?)''', (responsable, destino, tipo_usuario))
        id_prestamo = cursor.lastrowid

        for item in lista_carrito:
            # Descontar stock
            cursor.execute("UPDATE articulos SET cantidad = cantidad - ? WHERE codigo_barras = ?", 
                           (item["cantidad"], item["codigo"]))
            
            # Si el stock llega a 0, marcar como 'Prestado' automáticamente
            cursor.execute("UPDATE articulos SET estado = 'Prestado' WHERE cantidad = 0 AND codigo_barras = ?", 
                           (item["codigo"],))
            
            # Registrar detalle
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
    """Procesa la devolución y maneja si es total o parcial."""
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        
        # 1. Obtener cuánto se prestó originalmente
        cursor.execute("SELECT cantidad_prestada FROM detalle_prestamo WHERE id = ?", (id_detalle,))
        cant_original = cursor.fetchone()[0]

        if cantidad_regresada >= cant_original:
            # DEVOLUCIÓN TOTAL: Cerramos el registro
            cursor.execute('''UPDATE detalle_prestamo 
                              SET fecha_devolucion_item = CURRENT_TIMESTAMP 
                              WHERE id = ?''', (id_detalle,))
        else:
            # DEVOLUCIÓN PARCIAL: Restamos la cantidad del préstamo pero queda abierto
            nueva_cant_pendiente = cant_original - cantidad_regresada
            cursor.execute('''UPDATE detalle_prestamo 
                              SET cantidad_prestada = ? 
                              WHERE id = ?''', (nueva_cant_pendiente, id_detalle))
        
        # 2. Reingresar stock al inventario general
        cursor.execute("UPDATE articulos SET cantidad = cantidad + ? WHERE codigo_barras = ?", 
                       (cantidad_regresada, codigo_art))
        
        # Asegurar estado disponible
        cursor.execute("UPDATE articulos SET estado = 'Disponible' WHERE codigo_barras = ?", (codigo_art,))
        
        conn.commit()
        conn.close()
        return True, "Operación exitosa"
    except Exception as e:
        return False, str(e)
    
def obtener_historial_activos_db():
    """Trae todos los registros de la tabla detalle_prestamo que no han sido devueltos."""
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        
        # Unimos las tablas para tener: Nombre Articulo, Responsable, Destino, Cantidad y Fecha
        query = '''
            SELECT 
                a.nombre, 
                p.responsable, 
                p.destino, 
                p.tipo_usuario,
                dp.cantidad_prestada, 
                p.fecha_salida,
                a.codigo_barras
            FROM detalle_prestamo dp
            JOIN prestamos p ON dp.id_prestamo = p.id
            JOIN articulos a ON dp.codigo_articulo = a.codigo_barras
            WHERE dp.fecha_devolucion_item IS NULL
            ORDER BY p.fecha_salida DESC
        '''
        cursor.execute(query)
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