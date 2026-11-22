# Modelo lógico resumido

## Identidad y clientes

- `auth_user`: autenticación de Django.
- `store_customerprofile`: teléfono y perfil comercial ligado uno a uno al usuario.
- `store_address`: direcciones guardadas por usuario; el pedido conserva además una fotografía histórica en JSON.

## Catálogo

- `store_product`: producto visible en catálogo, categoría, deportes y especificaciones variables en JSON.
- `store_productimage`: una o más imágenes por producto.
- `store_variant`: SKU vendible, atributos, precio, oferta, stock y medidas propias opcionales.

Un producto puede tener una o muchas variantes. El stock se controla únicamente en la variante.

## Inventario

- `store_variant.stock`: existencia actual y fuente operativa de disponibilidad.
- `store_inventoryadjustment`: bitácora inmutable de entradas, salidas, correcciones, ventas y devoluciones.

La venta en línea bloquea la fila de la variante con `SELECT ... FOR UPDATE`, vuelve a validar existencias y descuenta dentro de la misma transacción. Esto evita que dos clientes compren simultáneamente la última unidad.

## Compra del cliente

- `store_cart` y `store_cartitem`: carrito activo de usuario o sesión invitada.
- `store_order`: pedido, estado, totales, modalidad y fotografía histórica de la dirección.
- `store_orderitem`: nombre, SKU, atributos y precio históricos de cada línea.
- `store_payment`: estado y referencia del cobro; nunca guarda número completo ni CVV.

## Entrega

- `store_storelocation`: origen de envíos y puntos de recolección.
- Los datos de cotización y rastreo se guardan en el pedido.
- Las dimensiones generales viven en producto; una variante puede sobrescribirlas cuando lo necesite.

## Reglas clave

- Un solo carrito activo por usuario o por sesión.
- Un SKU es único.
- El precio de oferta no puede superar el precio normal.
- Solo puede existir un origen de envíos activo marcado como origen.
- Los productos sin autenticidad verificada no pueden publicarse como originales.
- Las cancelaciones y expiraciones devuelven stock de forma idempotente.

