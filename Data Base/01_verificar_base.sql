-- Ejecutar en el SQL Editor de Supabase o mediante psql.
-- No modifica datos.

-- 1. Conteos principales.
SELECT 'usuarios' AS entidad, count(*) AS filas FROM auth_user
UNION ALL SELECT 'productos', count(*) FROM store_product
UNION ALL SELECT 'variantes', count(*) FROM store_variant
UNION ALL SELECT 'imagenes', count(*) FROM store_productimage
UNION ALL SELECT 'carritos', count(*) FROM store_cart
UNION ALL SELECT 'pedidos', count(*) FROM store_order
UNION ALL SELECT 'pagos', count(*) FROM store_payment
UNION ALL SELECT 'movimientos_inventario', count(*) FROM store_inventoryadjustment
ORDER BY entidad;

-- 2. Productos sin variante activa.
SELECT p.id, p.name, p.slug
FROM store_product p
WHERE NOT EXISTS (
  SELECT 1 FROM store_variant v
  WHERE v.product_id = p.id AND v.active = true
)
ORDER BY p.id;

-- 3. Variantes con datos incoherentes.
SELECT id, sku, stock, price, sale_price
FROM store_variant
WHERE stock < 0
   OR price < 0
   OR (sale_price IS NOT NULL AND sale_price > price)
ORDER BY id;

-- 4. Pedidos cuyo total no coincide con subtotal más envío.
SELECT id, number, subtotal, shipping_amount, total
FROM store_order
WHERE total <> subtotal + shipping_amount
ORDER BY id;

-- 5. Migraciones aplicadas.
SELECT app, name, applied
FROM django_migrations
ORDER BY applied DESC, app, name;

-- 6. Índices y restricciones de las tablas de la tienda.
SELECT
  n.nspname AS esquema,
  c.relname AS tabla,
  i.relname AS indice,
  pg_get_indexdef(ix.indexrelid) AS definicion
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
JOIN pg_index ix ON ix.indrelid = c.oid
JOIN pg_class i ON i.oid = ix.indexrelid
WHERE n.nspname = 'public'
  AND c.relname LIKE 'store_%'
ORDER BY c.relname, i.relname;

