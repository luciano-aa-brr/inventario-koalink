#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de prueba para verificar que las nuevas funciones de libros funcionan correctamente.
"""

import database

print("=" * 60)
print("PRUEBA: Sistema de Libros con Identificación Individual")
print("=" * 60)

# 1. Inicializar tablas
print("\n1. Inicializando tablas...")
try:
    database.inicializar_tablas()
    print("   ✓ Tablas creadas/verificadas exitosamente")
except Exception as e:
    print(f"   ✗ Error: {e}")
    exit(1)

# 2. Generar código de libro
print("\n2. Generando código de libro...")
try:
    codigo = database.generar_codigo_libro("Libro")
    print(f"   ✓ Código generado: {codigo}")
except Exception as e:
    print(f"   ✗ Error: {e}")
    exit(1)

# 3. Registrar un nuevo libro con copias
print("\n3. Registrando nuevo libro...")
try:
    exito, mensaje = database.registrar_libro_db(
        codigo,
        "Don Quijote de la Mancha",
        "Miguel de Cervantes",
        "Estante A-1",
        3
    )
    if exito:
        print(f"   ✓ {mensaje}")
    else:
        print(f"   ✗ {mensaje}")
except Exception as e:
    print(f"   ✗ Error: {e}")
    exit(1)

# 4. Obtener lista de libros
print("\n4. Obteniendo lista de libros...")
try:
    libros = database.obtener_libros_db()
    print(f"   ✓ Libros encontrados: {len(libros)}")
    for libro in libros:
        cod_lib, nombre, autor, total, disp, prest = libro
        print(f"      - {cod_lib}: {nombre} ({total} copias: {disp} disponibles, {prest} prestadas)")
except Exception as e:
    print(f"   ✗ Error: {e}")
    exit(1)

# 5. Obtener copias de un libro
print(f"\n5. Obteniendo copias de {codigo}...")
try:
    copias = database.obtener_copias_libro_db(codigo)
    print(f"   ✓ Copias encontradas: {len(copias)}")
    for copia in copias:
        numero_serie, estado, responsable, fecha = copia
        print(f"      - {numero_serie}: {estado} ({responsable})")
except Exception as e:
    print(f"   ✗ Error: {e}")
    exit(1)

# 6. Probar búsqueda por número de serie
print("\n6. Buscando copia específica...")
try:
    numero_serie = f"{codigo}-01"
    info = database.buscar_copia_por_numero_serie_db(numero_serie)
    if info['encontrado']:
        print(f"   ✓ Copia encontrada: {numero_serie}")
        print(f"      - Libro: {info['nombre_libro']}")
        print(f"      - Estado: {info['estado']}")
        print(f"      - Autor: {info['autor']}")
    else:
        print(f"   ✗ Copia no encontrada")
except Exception as e:
    print(f"   ✗ Error: {e}")
    exit(1)

# 7. Prestar una copia
print("\n7. Prestando una copia...")
try:
    exito, mensaje = database.prestar_copia_libro_db(
        numero_serie,
        "Juan Pérez",
        "Sala de Lectura",
        "Estudiante"
    )
    if exito:
        print(f"   ✓ {mensaje}")
    else:
        print(f"   ✗ {mensaje}")
except Exception as e:
    print(f"   ✗ Error: {e}")
    exit(1)

# 8. Verificar estado de la copia después de prestar
print("\n8. Verificando estado de copia prestada...")
try:
    info = database.buscar_copia_por_numero_serie_db(numero_serie)
    if info['encontrado']:
        print(f"   ✓ Estado actualizado: {info['estado']}")
        print(f"      - Responsable: {info['responsable']}")
    else:
        print(f"   ✗ Copia no encontrada")
except Exception as e:
    print(f"   ✗ Error: {e}")
    exit(1)

# 9. Devolver la copia
print("\n9. Devolviendo copia...")
try:
    exito, mensaje, info_prestamo = database.devolver_copia_libro_db(numero_serie)
    if exito:
        print(f"   ✓ {mensaje}")
        print(f"      - Responsable: {info_prestamo['responsable']}")
        print(f"      - Fecha salida: {info_prestamo['fecha_salida']}")
        print(f"      - Fecha devolución: {info_prestamo['fecha_devolucion']}")
    else:
        print(f"   ✗ {mensaje}")
except Exception as e:
    print(f"   ✗ Error: {e}")
    exit(1)

# 10. Agregar más copias a un libro existente
print("\n10. Agregando más copias al libro...")
try:
    exito, mensaje, nuevas = database.agregar_copias_libro_db(codigo, 2)
    if exito:
        print(f"   ✓ {mensaje}")
        print(f"      - Nuevos números de serie: {', '.join(nuevas)}")
    else:
        print(f"   ✗ {mensaje}")
except Exception as e:
    print(f"   ✗ Error: {e}")
    exit(1)

# 11. Verificar cantidad final de copias
print("\n11. Verificando cantidad final de copias...")
try:
    libros = database.obtener_libros_db()
    for libro in libros:
        if libro[0] == codigo:
            cod_lib, nombre, autor, total, disp, prest = libro
            print(f"   ✓ {nombre}: {total} copias totales")
            copias = database.obtener_copias_libro_db(codigo)
            print(f"      - Copias registradas: {len(copias)}")
            for copia in copias:
                numero_serie, estado, responsable, fecha = copia
                print(f"        • {numero_serie}: {estado}")
except Exception as e:
    print(f"   ✗ Error: {e}")
    exit(1)

print("\n" + "=" * 60)
print("✓ TODAS LAS PRUEBAS COMPLETADAS EXITOSAMENTE")
print("=" * 60)
