import sqlite3
import os

def iniciar_migracion():
    print("Iniciando Asistente de Migración KoaLink (Solo Artículos)...")
    
    # 1. Rutas de las bases de datos
    ruta_vieja = "inventario_viejo.db"
    ruta_nueva = "data/inventario.db" # Tu nueva base de datos

    if not os.path.exists(ruta_vieja):
        print(f"❌ Error: No se encontró la base de datos antigua '{ruta_vieja}'")
        return
    if not os.path.exists(ruta_nueva):
        print(f"❌ Error: No se encontró la base de datos nueva '{ruta_nueva}'. ¡Abre tu programa una vez para que se cree vacía!")
        return

    # 2. Conectar a ambas bases de datos
    conn_vieja = sqlite3.connect(ruta_vieja)
    conn_vieja.row_factory = sqlite3.Row 
    cursor_viejo = conn_vieja.cursor()

    conn_nueva = sqlite3.connect(ruta_nueva)
    cursor_nuevo = conn_nueva.cursor()

    try:
        # ==========================================
        # MIGRACIÓN DE ARTÍCULOS
        # ==========================================
        print("\n⏳ Leyendo inventario antiguo...")
        
        # Lee la tabla vieja (asegúrate de que en la antigua se llame 'articulos' o cambia el nombre aquí)
        cursor_viejo.execute("SELECT * FROM articulos")
        articulos_viejos = cursor_viejo.fetchall()

        migrados_exito = 0
        
        for art in articulos_viejos:
            columnas = art.keys()
            
            # --- MAPEO INTELIGENTE ---
            # Rescata el código (si en la base vieja se llamaba 'codigo', lo toma. Si se llamaba 'codigo_barras', también)
            codigo = art['codigo_barras'] if 'codigo_barras' in columnas else art['codigo'] if 'codigo' in columnas else str(art['id'])
            nombre = art['nombre'] if 'nombre' in columnas else "Sin Nombre"
            
            # Rellena los campos nuevos de la V2 que antes no existían
            categoria = art['categoria'] if 'categoria' in columnas else "Otros"
            ubicacion = art['ubicacion'] if 'ubicacion' in columnas else "Bodega Central"
            cantidad = art['cantidad'] if 'cantidad' in columnas else 0
            
            # Forzamos el estado a 'Activo' para empezar limpios
            estado = "Activo"

            try:
                # Inserta en la nueva base de datos
                cursor_nuevo.execute('''
                    INSERT OR IGNORE INTO articulos (codigo_barras, nombre, categoria, ubicacion, cantidad, estado)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (codigo, nombre, categoria, ubicacion, cantidad, estado))
                
                # Solo sumamos éxito si realmente se insertó un registro nuevo
                if cursor_nuevo.rowcount > 0:
                    migrados_exito += 1
            except Exception as e:
                print(f"⚠️ Error al migrar artículo {nombre}: {e}")

        conn_nueva.commit()
        print(f"✅ ¡Éxito! Se migraron {migrados_exito} artículos al nuevo sistema KoaLink.")

    except Exception as e:
        print(f"\n❌ Ocurrió un error: {e}")
    finally:
        # 3. Cerrar conexiones
        conn_vieja.close()
        conn_nueva.close()
        print("\nProceso finalizado. Cierra esta ventana y abre tu programa (main.py).")

if __name__ == "__main__":
    iniciar_migracion()