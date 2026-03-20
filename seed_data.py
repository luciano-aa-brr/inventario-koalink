import database

def cargar_datos_prueba():
    # Aseguramos que las tablas existan
    database.inicializar_tablas()
    
    datos = [
        # --- SALA DE INFORMÁTICA ---
        ("TAB-001", "Samsung Galaxy Tab A8", "Tablet", "Sala de Informática"),
        ("TAB-002", "Samsung Galaxy Tab A8", "Tablet", "Sala de Informática"),
        ("TAB-003", "iPad Air 5", "Tablet", "Sala de Informática"),
        ("NOTE-010", "Lenovo ThinkPad L14", "Notebook", "Sala de Informática"),
        ("NOTE-011", "HP ProBook 440", "Notebook", "Sala de Informática"),
        
        # --- BIBLIOTECA ---
        ("LIB-990", "Cien Años de Soledad - G. Márquez", "Libro", "Biblioteca"),
        ("LIB-991", "Código Civil Chile", "Libro", "Biblioteca"),
        ("IMP-550", "Epson EcoTank L3250", "Impresora", "Biblioteca"),
        ("PROY-01", "Proyector Epson PowerLite", "Material Didáctico", "Biblioteca"),
        ("MAP-05", "Mapa Físico de América del Sur", "Material Didáctico", "Biblioteca")
    ]

    for d in datos:
        exito = database.registrar_item(d[0], d[1], d[2], d[3])
        if exito:
            print(f"Insertado: {d[1]}")
        else:
            print(f"Saltado (ya existe): {d[0]}")

    print("\n--- Carga de prueba finalizada ---")

if __name__ == "__main__":
    cargar_datos_prueba()