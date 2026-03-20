import sqlite3
import os
from datetime import datetime
import pandas as pd
# Importaciones de ReportLab para el PDF y Códigos de Barras
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.graphics.barcode import code128
from reportlab.lib.units import mm

def inicializar_base_de_datos():
    conn = sqlite3.connect('inventario.db') # Usa el mismo nombre de conectar_db
    cursor = conn.cursor()
    try:
        # Intentar crear la columna cantidad por si no existe
        cursor.execute("ALTER TABLE articulos ADD COLUMN cantidad INTEGER DEFAULT 1")
        conn.commit()
        print("Base de datos actualizada: Columna 'cantidad' lista.")
    except sqlite3.OperationalError:
        # Si ya existe, no hace nada y el programa sigue
        pass
    conn.close()

# EJECUTAR ESTO SIEMPRE AL CARGAR EL MÓDULO
inicializar_base_de_datos()

def conectar_db():
    # Creamos la carpeta data si no existe para que sea portable
    if not os.path.exists('data'):
        os.makedirs('data')
    
    conexion = sqlite3.connect('data/inventario.db')
    return conexion

def inicializar_tablas():
    conn = conectar_db()
    cursor = conn.cursor()
    
    # 1. Creamos la tabla con la columna cantidad incluida por defecto
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

    # 2. BLOQUE DE EMERGENCIA: Si la tabla ya existía de antes, esto añade la columna
    try:
        cursor.execute("ALTER TABLE articulos ADD COLUMN cantidad INTEGER DEFAULT 1")
        conn.commit()
    except:
        # Si ya existe, no hará nada y no dará error
        pass

    # Tabla de Movimientos
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


def generar_pdf_etiquetas_reales():
    """Genera etiquetas con CÓDIGO DE BARRAS real corregido para evitar error de wrapOn."""
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        cursor.execute("SELECT codigo_barras, nombre FROM articulos WHERE estado != 'Inactivo' ORDER BY categoria, codigo_barras")
        datos = cursor.fetchall()
        conn.close()

        if not datos: return False, "No hay datos."

        nombre_archivo = "Etiquetas_Scanner_Ready.pdf"
        doc = SimpleDocTemplate(nombre_archivo, pagesize=letter, 
                                 rightMargin=10, leftMargin=10, topMargin=20, bottomMargin=20)
        
        estilos = getSampleStyleSheet()
        # Creamos un estilo personalizado para el texto de la etiqueta
        estilo_etiqueta = estilos["Normal"]
        estilo_etiqueta.alignment = 1 # Centrado
        estilo_etiqueta.fontSize = 8

        elementos = []
        tabla_datos = []
        fila_temporal = []

        for d in datos:
            codigo = d[0]
            nombre = d[1][:20] # Limitar nombre

            # 1. Crear el objeto de código de barras
            bc = code128.Code128(codigo, barHeight=12*mm, barWidth=0.3*mm)
            
            # 2. CREAR UN SUB-CONTENIDO PARA LA CELDA
            # Usamos una tabla pequeña dentro de la celda para organizar: Barras, luego Texto
            sub_tabla = Table([
                [bc],
                [Paragraph(f"<b>{codigo}</b>", estilo_etiqueta)],
                [Paragraph(nombre, estilo_etiqueta)]
            ], colWidths=[55*mm])
            
            sub_tabla.setStyle(TableStyle([
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('TOPPADDING', (0,0), (-1,-1), 1),
                ('BOTTOMPADDING', (0,0), (-1,-1), 1),
            ]))

            fila_temporal.append(sub_tabla)
            
            if len(fila_temporal) == 3:
                tabla_datos.append(fila_temporal)
                fila_temporal = []

        if fila_temporal:
            while len(fila_temporal) < 3: fila_temporal.append("")
            tabla_datos.append(fila_temporal)

        # Tabla principal que organiza las etiquetas en la hoja
        tabla_principal = Table(tabla_datos, colWidths=[65*mm, 65*mm, 65*mm], rowHeights=40*mm)
        tabla_principal.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        
        elementos.append(tabla_principal)
        doc.build(elementos)
        os.startfile(nombre_archivo)
        return True, nombre_archivo

    except Exception as e:
        print(f"Error detallado: {e}")
        return False, str(e)
    
def registrar_prestamo_stock(codigo, responsable, destino, cantidad_a_prestar):
    """Registra el movimiento y resta la cantidad del inventario general."""
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        
        # 1. Obtener stock actual
        cursor.execute("SELECT cantidad, nombre FROM articulos WHERE codigo_barras = ?", (codigo,))
        res = cursor.fetchone()
        stock_actual = res[0]
        nombre_item = res[1]

        if stock_actual < cantidad_a_prestar:
            return False, f"Solo quedan {stock_actual} unidades de {nombre_item}."

        # 2. Restar del inventario
        nuevo_stock = stock_actual - cantidad_a_prestar
        cursor.execute("UPDATE articulos SET cantidad = ? WHERE codigo_barras = ?", (nuevo_stock, codigo))
        
        # 3. Registrar el movimiento (usamos la columna 'destino' para guardar la cantidad prestada temporalmente o en una nota)
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M")
        query_mov = "INSERT INTO movimientos (codigo_articulo, responsable, destino, fecha_prestamo) VALUES (?, ?, ?, ?)"
        # Guardamos la cantidad en el campo destino para saber cuántos devolver luego
        destino_con_cant = f"{destino} (Cant: {cantidad_a_prestar})"
        cursor.execute(query_mov, (codigo, responsable, destino_con_cant, fecha))
        
        conn.commit()
        conn.close()
        return True, f"Prestadas {cantidad_a_prestar} unidades de {nombre_item}."
    except Exception as e:
        return False, str(e)
    
def actualizar_estructura_stock():
    conn = conectar_db()
    cursor = conn.cursor()
    try:
        # Añadimos la columna cantidad con valor por defecto 1
        cursor.execute("ALTER TABLE articulos ADD COLUMN cantidad INTEGER DEFAULT 1")
        conn.commit()
    except:
        pass # Si ya existe, no hace nada
    conn.close()

def guardar_item_db(codigo, nombre, categoria, ubicacion, cantidad):
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        # Esta línea debe tener exactamente estos nombres de columna
        query = '''INSERT INTO articulos (codigo_barras, nombre, categoria, estado, ubicacion, cantidad) 
                   VALUES (?, ?, ?, 'Disponible', ?, ?)'''
        
        cursor.execute(query, (codigo, nombre, categoria, ubicacion, cantidad))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error real al guardar: {e}") # Este es el mensaje que ves en la terminal
        return False
    
def generar_pdf_inventario():
    """Genera un archivo PDF con todos los códigos activos del inventario."""
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        # Solo traemos los que no están inactivos
        cursor.execute("SELECT codigo_barras, nombre, categoria FROM articulos WHERE estado != 'Inactivo' ORDER BY categoria, codigo_barras")
        datos = cursor.fetchall()
        conn.close()

        if not datos:
            return False, "No hay datos para exportar."

        nombre_archivo = "Etiquetas_Inventario_KoaLink.pdf"
        doc = SimpleDocTemplate(nombre_archivo, pagesize=letter)
        elementos = []
        estilos = getSampleStyleSheet()

        # Título del documento
        titulo = Paragraph("<b>Listado de Etiquetas - Escuela Araucanía</b>", estilos['Title'])
        elementos.append(titulo)
        elementos.append(Paragraph("<br/><br/>", estilos['Normal']))

        # Preparar la tabla: Encabezados + Datos
        tabla_datos = [["CÓDIGO DE BARRAS", "DESCRIPCIÓN", "CATEGORÍA"]]
        for d in datos:
            tabla_datos.append([d[0], d[1], d[2]])

        # Estilo de la tabla (Bordes y colores para facilitar el recorte)
        tabla = Table(tabla_datos, colWidths=[120, 280, 100])
        estilo_tabla = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black), # Cuadrícula para recorte
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ])
        tabla.setStyle(estilo_tabla)
        elementos.append(tabla)

        # Construir PDF
        doc.build(elementos)
        
        # Abrir el PDF automáticamente (Windows)
        os.startfile(nombre_archivo)
        return True, nombre_archivo

    except Exception as e:
        return False, str(e)


def registrar_item(codigo, nombre, categoria, ubicacion):
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO articulos (codigo_barras, nombre, categoria, ubicacion, estado)
            VALUES (?, ?, ?, ?, 'Disponible')
        ''', (codigo, nombre, categoria, ubicacion))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error al registrar: {e}")
        return False
    
def registrar_prestamo_masivo(codigo, responsable, destino):
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        
        # 1. Verificar si el equipo existe y está disponible
        cursor.execute("SELECT estado FROM articulos WHERE codigo_barras = ?", (codigo,))
        resultado = cursor.fetchone()
        
        if resultado and resultado[0] == 'Disponible':
            # 2. Registrar el préstamo
            cursor.execute('''
                INSERT INTO movimientos (codigo_articulo, responsable, destino)
                VALUES (?, ?, ?)
            ''', (codigo, responsable, destino))
            
            # 3. Actualizar estado del artículo
            cursor.execute('''
                UPDATE articulos SET estado = 'Prestado' WHERE codigo_barras = ?
            ''', (codigo,))
            
            conn.commit()
            conn.close()
            return True, "Registrado"
        elif resultado:
            return False, f"El equipo ya está {resultado[0]}"
        else:
            return False, "Código no encontrado"
            
    except Exception as e:
        return False, str(e)
    
def registrar_devolucion(codigo, nueva_ubicacion):
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        
        # 1. Verificar si está prestado
        cursor.execute("SELECT estado FROM articulos WHERE codigo_barras = ?", (codigo,))
        res = cursor.fetchone()
        
        if res and res[0] == 'Prestado':
            # 2. Actualizar el movimiento (poner fecha de retorno)
            cursor.execute('''
                UPDATE movimientos SET fecha_retorno = CURRENT_TIMESTAMP 
                WHERE codigo_articulo = ? AND fecha_retorno IS NULL
            ''', (codigo,))
            
            # 3. Volver el artículo a Disponible y actualizar su ubicación física
            cursor.execute('''
                UPDATE articulos SET estado = 'Disponible', ubicacion = ? 
                WHERE codigo_barras = ?
            ''', (nueva_ubicacion, codigo))
            
            conn.commit()
            conn.close()
            return True, "Devolución Exitosa"
        else:
            return False, "El equipo no figura como prestado"
    except Exception as e:
        return False, str(e)

def conectar_db():
    return sqlite3.connect('inventario.db')

def obtener_articulos_inventario(categoria="Todos", estado="Activos"):
    """Consulta mejorada que incluye la columna cantidad."""
    conn = conectar_db()
    cursor = conn.cursor()
    query = "SELECT codigo_barras, nombre, categoria, estado, ubicacion, cantidad FROM articulos WHERE 1=1"
    params = []

    if categoria != "Todos":
        query += " AND categoria = ?"
        params.append(categoria)
    
    if estado == "Activos":
        query += " AND estado != 'Inactivo'"
    elif estado == "Inactivos":
        query += " AND estado = 'Inactivo'"

    cursor.execute(query, params)
    datos = cursor.fetchall()
    conn.close()
    return datos

def registrar_movimiento_completo(codigo, responsable, destino, cant_prestar):
    """Registra el préstamo y descuenta el stock en una sola operación."""
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 1. Obtener stock actual
        cursor.execute("SELECT cantidad, nombre FROM articulos WHERE codigo_barras = ?", (codigo,))
        res = cursor.fetchone()
        if not res: return False, "Código no encontrado"
        
        stock_actual, nombre = res
        if stock_actual < cant_prestar:
            return False, f"Stock insuficiente (Disponible: {stock_actual})"

        # 2. Registrar en tabla movimientos (Guardamos la cantidad en el destino para control)
        destino_final = f"{destino} | Cant: {cant_prestar}"
        cursor.execute('''INSERT INTO movimientos (codigo_articulo, responsable, destino, fecha_salida) 
                          VALUES (?, ?, ?, ?)''', (codigo, responsable, destino_final, fecha))

        # 3. Actualizar Stock y Estado
        nuevo_stock = stock_actual - cant_prestar
        # Si el stock llega a 0, marcamos como Prestado, si no, sigue Disponible
        nuevo_estado = "Prestado" if nuevo_stock == 0 else "Disponible"
        
        cursor.execute("UPDATE articulos SET cantidad = ?, estado = ? WHERE codigo_barras = ?", 
                       (nuevo_stock, nuevo_estado, codigo))

        conn.commit()
        conn.close()
        return True, f"Préstamo exitoso de {nombre}"
    except Exception as e:
        return False, str(e)

def obtener_detalle_prestamo(codigo):
    """Busca el ítem para validación rápida en la interfaz de préstamo."""
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("SELECT nombre, categoria, cantidad FROM articulos WHERE codigo_barras = ?", (codigo,))
    res = cursor.fetchone()
    conn.close()
    return res # (nombre, categoria, cantidad)

def obtener_datos_para_reporte():
    conn = conectar_db()
    # Esta consulta busca el artículo y, si está prestado, trae el último responsable registrado
    query = '''
        SELECT 
            a.codigo_barras AS 'Código',
            a.nombre AS 'Artículo',
            a.categoria AS 'Categoría',
            a.estado AS 'Estado Actual',
            a.ubicacion AS 'Ubicación Física',
            (SELECT responsable FROM movimientos WHERE codigo_articulo = a.codigo_barras AND fecha_retorno IS NULL ORDER BY fecha_salida DESC LIMIT 1) AS 'Poseedor Actual'
        FROM articulos a
    '''
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def obtener_info_individual(codigo):
    """Busca un artículo y devuelve su información y quién lo tiene (si aplica)."""
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        
        # Consulta SQL avanzada: busca el ítem y cruza datos con el último préstamo activo
        query = '''
            SELECT 
                a.nombre, a.categoria, a.estado, a.ubicacion,
                m.responsable, m.destino, m.fecha_salida
            FROM articulos a
            LEFT JOIN movimientos m ON a.codigo_barras = m.codigo_articulo 
                 AND m.fecha_retorno IS NULL
            WHERE a.codigo_barras = ?
            ORDER BY m.fecha_salida DESC LIMIT 1
        '''
        cursor.execute(query, (codigo,))
        resultado = cursor.fetchone()
        conn.close()
        
        if resultado:
            # Organizamos los datos en un diccionario para que sea fácil de leer en main.py
            return {
                "encontrado": True,
                "nombre": resultado[0],
                "categoria": resultado[1],
                "estado": resultado[2],
                "ubicacion_base": resultado[3],
                "quien_lo_tiene": resultado[4] if resultado[4] else "Nadie (En bodega)",
                "donde_esta": resultado[5] if resultado[5] else resultado[3],
                "desde_cuando": resultado[6] if resultado[6] else "N/A"
            }
        else:
            return {"encontrado": False}
            
    except Exception as e:
        print(f"Error en búsqueda individual: {e}")
        return {"encontrado": False, "error": str(e)}
    
def dar_de_baja_logica(codigo):
    """Cambia el estado a Inactivo sin borrar el registro."""
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE articulos SET estado = 'Inactivo' WHERE codigo_barras = ?", (codigo,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error en baja lógica: {e}")
        return False

def obtener_inventario_filtrado(categoria="Todos", estado="Activos"):
    conn = conectar_db()
    # Esta consulta trae los datos del item y, si está prestado, trae el responsable y destino
    query = '''
        SELECT 
            a.codigo_barras, 
            a.nombre, 
            a.categoria, 
            a.estado, 
            CASE 
                WHEN a.estado = 'Prestado' THEN (m.responsable || " (" || m.destino || ")")
                ELSE a.ubicacion 
            END as ubicacion_dinamica
        FROM articulos a
        LEFT JOIN movimientos m ON a.codigo_barras = m.codigo_articulo 
             AND m.fecha_retorno IS NULL
        WHERE 1=1
    '''
    params = []

    if categoria != "Todos":
        query += " AND a.categoria = ?"
        params.append(categoria)
    
    if estado == "Activos":
        query += " AND a.estado != 'Inactivo'"
    elif estado == "Inactivos":
        query += " AND a.estado = 'Inactivo'"

    # Agregamos GROUP BY para evitar duplicados si hay errores en movimientos
    query += " GROUP BY a.codigo_barras"

    cursor = conn.cursor()
    cursor.execute(query, params)
    datos = cursor.fetchall()
    conn.close()
    return datos

def actualizar_item_db(codigo_original, nuevo_nombre, nueva_categoria, nueva_ubicacion):
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE articulos 
            SET nombre = ?, categoria = ?, ubicacion = ? 
            WHERE codigo_barras = ?
        ''', (nuevo_nombre, nueva_categoria, nueva_ubicacion, codigo_original))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error al actualizar: {e}")
        return False
    
def reactivar_item_db(codigo, nuevo_nombre, nueva_categoria, nueva_ubicacion):
    """Actualiza los datos y cambia el estado de 'Inactivo' a 'Disponible'."""
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE articulos 
            SET nombre = ?, categoria = ?, ubicacion = ?, estado = 'Disponible'
            WHERE codigo_barras = ?
        ''', (nuevo_nombre, nueva_categoria, nueva_ubicacion, codigo))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error al reactivar: {e}")
        return False
    
def obtener_prestamos_activos():
    """Trae los artículos que tienen estado 'Prestado' y su info de préstamo."""
    conn = conectar_db()
    cursor = conn.cursor()
    query = '''
        SELECT a.codigo_barras, a.nombre, a.categoria, a.estado, a.ubicacion, m.responsable
        FROM articulos a
        JOIN movimientos m ON a.codigo_barras = m.codigo_articulo
        WHERE a.estado = 'Prestado' AND m.fecha_retorno IS NULL
    '''
    cursor.execute(query)
    datos = cursor.fetchall()
    conn.close()
    return datos

def obtener_item_base(codigo):
    """Devuelve los datos originales del ítem (sin info de préstamos)."""
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        query = "SELECT codigo_barras, nombre, categoria, estado, ubicacion FROM articulos WHERE codigo_barras = ?"
        cursor.execute(query, (codigo,))
        resultado = cursor.fetchone()
        conn.close()
        return resultado # Retorna (codigo, nombre, categoria, estado, ubicacion_base)
    except Exception as e:
        print(f"Error al obtener ítem base: {e}")
        return None
    
def generar_siguiente_codigo(categoria):
    """Genera un código automático basado en la categoría."""
    # Mapeo de prefijos
    prefijos = {
        "Tablet": "TAB",
        "Notebook": "NOTE",
        "Libro": "LIB",
        "Impresora": "IMP",
        "Material Didáctico": "MAT"
    }
    prefijo = prefijos.get(categoria, "EQU")
    
    conn = conectar_db()
    cursor = conn.cursor()
    # Buscamos el código más alto que empiece con ese prefijo
    cursor.execute("SELECT codigo_barras FROM articulos WHERE codigo_barras LIKE ? ORDER BY codigo_barras DESC LIMIT 1", (prefijo + '-%',))
    ultimo = cursor.fetchone()
    conn.close()

    if ultimo:
        # Extraemos el número del final (ej: TAB-005 -> 5)
        ultimo_num = int(ultimo[0].split('-')[1])
        nuevo_num = ultimo_num + 1
    else:
        nuevo_num = 1

    # Retornamos con formato de 3 dígitos: PREFIJO-001
    return f"{prefijo}-{nuevo_num:03d}"


if __name__ == "__main__":
    inicializar_tablas()