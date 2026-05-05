# 📚 Guía de Uso: Sistema de Libros con Identificación Individual

## Descripción General
Tu sistema de inventario ahora tiene un módulo especializado para gestionar libros con identificación individual de cada copia. Esto permite:

✅ Tener **código del libro** (para identificar el título)  
✅ Identificar **cada copia de forma única** (número de serie)  
✅ **Rastrear quién tiene** cada copia mediante el número de serie

---

## 1️⃣ Registrar un Nuevo Libro

### Pasos:
1. Abre la aplicación y ve al módulo de **Inventario**
2. Busca la opción **"📚 Gestión de Libros"** (nueva opción)
3. Haz clic en **"➕ Agregar Nuevo Libro"**
4. Completa el formulario:
   - **Código del Libro**: Se genera automáticamente (ej: `LIB-001`)
   - **Título del Libro**: Nombre del libro (ej: "Don Quijote")
   - **Autor**: Autor del libro (ej: "Miguel de Cervantes")
   - **Estante/Ubicación**: Dónde guardar (ej: "Estante A-1")
   - **Cantidad de Copias**: Cuántas copias tienes del libro (ej: `3`)

### Resultado:
El sistema **automáticamente genera números de serie** para cada copia:
- `LIB-001-01` (primera copia)
- `LIB-001-02` (segunda copia)
- `LIB-001-03` (tercera copia)

---

## 2️⃣ Ver Todas las Copias de un Libro

### Pasos:
1. Ve a **Inventario > Libros**
2. Verás una tabla con todos los libros registrados
3. Haz clic en el botón **"📖"** (al lado del libro que quieres ver)

### Información que Verás:
| Campo | Significado |
|-------|-------------|
| Número de Serie | Identificador único (ej: LIB-001-01) |
| Estado | Disponible o Prestado |
| Responsable | Quién tiene la copia actualmente |
| Fecha Préstamo | Cuándo se prestó |

---

## 3️⃣ Prestar una Copia Individual

### Opción A: Buscar por Número de Serie (Recomendado)

1. Ve a **Préstamos > Prestar Copia de Libro** (nueva opción)
2. En el campo "Número de Serie", escribe el código (ej: `LIB-001-01`)
3. Presiona **Enter** para buscar
4. El sistema mostrará:
   - ✅ Detalles del libro
   - ✅ Si está disponible
5. Completa los datos del responsable:
   - Tipo: Estudiante o Funcionario
   - Nombre Completo
   - Sala/Oficina de Destino
6. Haz clic en **"📤 PRESTAR COPIA"**

### Opción B: Desde la Lista de Copias
1. Ve a **Inventario > Libros > Ver Copias (📖)**
2. Identifica la copia que quieres prestar
3. Anota el número de serie (ej: `LIB-001-02`)
4. Sigue los pasos de la **Opción A**

---

## 4️⃣ Devolver una Copia Individual

### Pasos:
1. Ve a **Devoluciones** (módulo existente)
2. Escribe el **número de serie** de la copia (ej: `LIB-001-01`)
3. Especifica la cantidad (siempre será 1 para copias de libro)
4. Confirma la devolución

---

## 5️⃣ Agregar Más Copias a un Libro Existente

### Pasos:
1. Ve a **Inventario > Libros**
2. Encuentra el libro en la tabla
3. Haz clic en el botón **"➕"** (agregar copias)
4. Un diálogo pedirá: ¿Cuántas copias adicionales?
5. Escribe el número (ej: `2`)
6. El sistema generará nuevos números de serie automáticamente:
   - `LIB-001-04` (si ya había 3 copias)
   - `LIB-001-05`

---

## 6️⃣ Buscar una Copia por Número de Serie

### Para Saber Quién Tiene un Libro:

**Ejemplo**: Alguien encontró un libro y quiere saber a quién se le prestó.

1. Lee el **número de serie** del libro (ej: `LIB-001-03`)
2. Ve a **Préstamos > Prestar Copia de Libro**
3. Ingresa el número de serie
4. Presiona **Enter**
5. El sistema te dirá:
   - 📖 Qué libro es
   - 👤 Quién lo tiene actualmente
   - 📍 Dónde está
   - 📅 Desde cuándo lo tiene

---

## 📊 Vista General de Libros

En **Inventario > Libros** puedes ver:

| Columna | Información |
|---------|------------|
| CÓDIGO | Código del libro (ej: LIB-001) |
| TÍTULO | Nombre del libro |
| AUTOR | Autor |
| TOTAL | Cantidad total de copias |
| DISPONIBLES | Copias sin prestar 🟢 |
| PRESTADAS | Copias actualmente prestadas 🟠 |

---

## 🔑 Números de Serie: Ejemplos

### Formato
```
{CODIGO-PREFIJO}{NUMERO}-{COPIA}
LIB-001-01
└─┬─┘  └─┬─┘ └─┬─┘
  │     │    └─ Número de copia
  │     └───── Código auto-generado
  └────────── Prefijo de categoría (LIB = Libro)
```

### Ejemplos Reales
- `LIB-001-01`: Primera copia del Don Quijote
- `LIB-002-05`: Quinta copia del segundo libro registrado
- `LIB-015-03`: Tercera copia del decimoquinto libro registrado

---

## 💡 Casos de Uso

### Caso 1: Estudiante pierde un libro
1. Encontraste un número de serie: `LIB-003-02`
2. Búscalo en "Prestar Copia > Buscar"
3. Sabrás exactamente a qué estudiante se lo prestaste
4. Podrás contactarlo

### Caso 2: Tienes 10 copias de un libro
1. Registra: "1 libro" con "10 copias"
2. Sistema crea automáticamente: `LIB-001-01` a `LIB-001-10`
3. Cada vez que uno se presta, sabes exactamente cuál y a quién

### Caso 3: Auditoría de biblioteca
1. Ve a "Inventario > Libros"
2. Visualiza: Total de copias vs Disponibles vs Prestadas
3. Identifica qué copias están fuera desde hace mucho tiempo
4. Contacta a los responsables

---

## ⚠️ Notas Importantes

- **Número de serie**: Es único e irrepetible en todo el sistema
- **Cada copia**: Tiene su propio historial de préstamos
- **Compatibilidad**: El sistema de artículos generales sigue igual (Tablets, Notebooks, etc.)
- **Búsqueda rápida**: Por número de serie es la forma más eficiente

---

## 🚀 Próximas Mejoras Sugeridas

- [ ] Código de barras para número de serie
- [ ] Reporte de copias por estado (extraviadas, dañadas)
- [ ] Notificaciones automáticas para devoluciones atrasadas
- [ ] Historial gráfico de uso de cada copia

---

## ❓ Preguntas Frecuentes

**P: ¿Se pueden cambiar los números de serie?**  
R: No, son automáticos y únicos. Pero sí puedes agregar más copias.

**P: ¿Qué pasa si pierdo un libro?**  
R: Busca el número de serie en "Devoluciones" > Marcar como "Extraviado/Dañado"

**P: ¿Cómo sé cuántas copias de un libro hay disponibles?**  
R: En la tabla de "Inventario > Libros" verás: DISPONIBLES vs TOTAL

**P: ¿Puedo prestar múltiples copias de un libro a la vez?**  
R: Sí, pero debes hacerlo una por una, ingresando cada número de serie.

---

**¡Sistema listo para usar! 🎉**
