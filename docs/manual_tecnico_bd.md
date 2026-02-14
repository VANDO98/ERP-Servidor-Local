# Manual Técnico de la Base de Datos

## 1. Conceptos Fundamentales (Claves)

Para que la base de datos "hable" y conecte la información, usamos dos tipos de claves:

*   **🔑 PK (Primary Key / Llave Primaria):**
    *   **¿Qué es?**: Es el DNI de cada registro. Un número único que identifica irrepetiblemente a una fila.
    *   **Ejemplo**: En la tabla `productos`, el `id=5` es ÚNICO para el "Martillo". No puede haber otro producto con `id=5`.

*   **🔗 FK (Foreign Key / Llave Foránea):**
    *   **¿Qué es?**: Es un "puntero" o "ancla" que conecta una tabla con otra. En lugar de escribir toda la información de nuevo, guardamos solo el ID de referencia.
    *   **Ejemplo**: En la factura, no escribimos "Proveedor: Ferretería Central S.A., Dirección: Av. Siempre Viva 123...". Solo guardamos `proveedor_id = 8`. La base de datos busca el ID 8 en la tabla de proveedores y recupera toda la info.

---

## 2. Explicación de las Relaciones

El diagrama muestra cómo fluye la información. Vamos de lo general a lo específico:

### A. Proveedores y Compras (`proveedores` ||--o{ `compras_cabecera`)
*   **Relación**: Uno a Muchos (1:N).
*   **Lectura**: *"Un Proveedor puede tener MUCHAS Facturas de compra, pero una Factura pertenece a UN solo proveedor".*
*   **Conexión**: La tabla `compras_cabecera` tiene la columna `proveedor_id` (FK) apuntando hacia `proveedores`.

### B. Compras y Detalles (`compras_cabecera` ||--|{ `compras_detalle`)
*   **Relación**: Uno a Muchos (1:N).
*   **Lectura**: *"Una Factura (Cabecera) se compone de MUCHAS líneas de detalle (ítems), pero una línea de detalle pertenece a UNA única factura".*
*   **Conexión**: La tabla `compras_detalle` usa `compra_id` (FK) para saber a qué papel pertenece.

### C. Productos y Detalles (`productos` ||--o{ `compras_detalle`)
*   **Relación**: Uno a Muchos (1:N).
*   **Lectura**: *"Un Producto (ej. Cemento) puede aparecer en MUCHAS líneas de detalle de diferentes facturas".*
*   **Conexión**: La tabla `compras_detalle` usa `producto_id` (FK) para saber qué se compró.

---

## 3. Ejemplo Práctico "La Factura Física"

Imagina que tienes una factura de papel en la mano:

1.  **Cabecera (Lo de arriba):**
    *   Dice "Señor: Juan Perez". En la BD, esto es una fila en `compras_cabecera` con `proveedor_id` apuntando a Juan.
    *   Dice "Fecha: 10/02/2026". Se guarda en `fecha_emision`.

2.  **Cuerpo (La grilla de ítems):**
    *   **Renglón 1:** "10 bolsas de Cemento".
        *   Se crea una fila en `compras_detalle`.
        *   `compra_id`: Apunta a la cabecera de arriba.
        *   `producto_id`: Apunta al ítem "Cemento" en la tabla `productos`.
        *   `cantidad`: 10.
    *   **Renglón 2:** "5 Palas".
        *   Se crea OTRA fila en `compras_detalle`.
        *   `compra_id`: El mismo de arriba (es la misma factura).
        *   `producto_id`: Apunta al ítem "Pala".
        *   `cantidad`: 5.

De esta forma, nunca duplicamos nombres y todo está matemáticamente enlazado.
