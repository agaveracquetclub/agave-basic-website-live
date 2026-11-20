# Agave Racquet Club — Basic Website

Versión simplificada y separada del proyecto académico `FINAL`. Está pensada como base real de tienda: catálogo, usuarios, carrito, pedidos, pagos, inventario por variante, recolección, envíos y administración.

## Qué incluye

- Django 5.2 y Python.
- PostgreSQL local o alojado en Supabase.
- Django Auth para registro, inicio de sesión y permisos.
- Productos con una o más variantes.
- Precio normal y precio de oferta.
- Inventario por variante con historial de ajustes.
- Carrito para visitante y usuario autenticado.
- Pedidos con envío a domicilio o recolección.
- Cotización de Envia.com desde el servidor.
- Pago con Mercado Pago Checkout Pro.
- Panel de dueño propio para catálogo, variantes, inventario, pedidos e indicadores.
- Panel Django Admin para configuración avanzada, pagos y ubicaciones.
- Pantalla interna para registrar ventas externas.
- Imágenes en Supabase Storage mediante su interfaz S3 opcional.
- Diseño responsive basado en la identidad visual de Agave.

## Regla de la última unidad

El stock no se comprueba solamente en el navegador. Al crear el pedido, PostgreSQL bloquea las filas de las variantes con `SELECT ... FOR UPDATE`, vuelve a validar las cantidades y descuenta el inventario dentro de la misma transacción.

El bloqueo dura 15 minutos. Si el pedido vence o el pago falla, el inventario se devuelve de forma idempotente. Si Mercado Pago notificara un pago aprobado después de que el stock ya fue liberado, el sistema solicita un reembolso para evitar vender la misma unidad dos veces.

## Tarjetas

Agave no guarda número completo, CVV ni fecha de vencimiento. Mercado Pago procesa y tokeniza la tarjeta. La base conserva únicamente la referencia externa, marca y últimos cuatro dígitos cuando Mercado Pago los proporciona.

## Instalación rápida en Windows

Desde PowerShell:

```powershell
cd "C:\Users\Sergio\Documents\AGAVE RACQUET CLUB\Basic Website"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py migrate
python manage.py seed_catalog
python manage.py createsuperuser
python manage.py runserver
```

Abre `http://127.0.0.1:8000/`, el panel de dueño en `http://127.0.0.1:8000/dueno/` y la administración avanzada en `http://127.0.0.1:8000/admin/`.

Para desarrollo sin PostgreSQL, elimina o comenta `DATABASE_URL` en `.env`; Django usará SQLite. Para producción usa siempre PostgreSQL.

## Opción Docker local

```powershell
docker compose up --build
docker compose exec web python manage.py seed_catalog
docker compose exec web python manage.py createsuperuser
```

El sitio queda en `http://127.0.0.1:8000/`.

## Configurar Supabase PostgreSQL

1. Crea un proyecto en Supabase.
2. Copia la cadena de conexión PostgreSQL del panel.
3. En `.env`, configura:

```text
DATABASE_URL=postgresql://usuario:contraseña@host:5432/postgres
DB_SSL_REQUIRE=True
```

4. Ejecuta:

```powershell
python manage.py migrate
python manage.py seed_catalog
python manage.py createsuperuser
```

## Configurar imágenes con Supabase Storage

La aplicación funciona con archivos locales durante desarrollo. Para producción:

1. En Supabase Storage, crea un bucket público, por ejemplo `agave-products`.
2. Activa S3 y genera una clave de acceso para uso exclusivo del servidor.
3. Completa las variables `SUPABASE_S3_*` de `.env`.
4. Nunca pongas la clave secreta en JavaScript, HTML o Git.

Las imágenes iniciales del catálogo ya están incluidas como recursos estáticos. Las nuevas imágenes subidas desde Admin usarán el almacenamiento configurado.

## Configurar Mercado Pago

Completa en `.env` las credenciales de prueba:

```text
MERCADOPAGO_ACCESS_TOKEN=
MERCADOPAGO_PUBLIC_KEY=
MERCADOPAGO_WEBHOOK_SECRET=
MERCADOPAGO_SUCCESS_URL=https://tu-dominio.com/pago/exito/
MERCADOPAGO_FAILURE_URL=https://tu-dominio.com/pago/error/
MERCADOPAGO_PENDING_URL=https://tu-dominio.com/pago/pendiente/
```

En Mercado Pago registra este webhook:

```text
https://tu-dominio.com/webhooks/mercadopago/
```

Usa credenciales de prueba hasta verificar pagos aprobados, rechazados, pendientes, expirados y reembolsos.

## Configurar Envia.com

Completa:

```text
ENVIA_API_TOKEN=
ENVIA_RATE_URL=https://api-test.envia.com/ship/rate/
```

Cada producto necesita **peso de envío por unidad**, **largo, ancho y alto de la caja** y **unidades máximas por caja**. Estos campos se editan desde el panel de dueño o desde **Admin → Productos**. El origen se elige desde **Admin → Sucursales y puntos de entrega** y necesita código postal y teléfono. Solo puede existir un origen activo marcado como origen de envíos.

El algoritmo agrupa productos con el mismo perfil de empaque antes de solicitar tarifas. El perfil inicial de las raquetas es `65 × 30 × 10 cm`, `0.4 kg` por unidad y hasta `2` unidades por caja. Por ello, dos raquetas compatibles se cotizan como una caja de `0.8 kg`. La interfaz también muestra el peso cobrable estimado con divisor volumétrico `5000`; la paquetería determina el peso y precio definitivos.

Para habilitar cotizaciones reales, genera primero un token sandbox en `https://shipping-test.envia.com/settings/developers`, guárdalo solamente en `.env` como `ENVIA_API_TOKEN` y reinicia Django. Usa el token y la URL de producción solo después de probar direcciones, tarifas y errores en sandbox.

Antes de usar producción confirma la URL de producción y los formatos actuales con la documentación de Envia.com.

## Operación del panel

- **Inicio (`/dueno/`):** indicadores de catálogo, inventario, ventas recientes, pedidos pendientes, bajo stock y actividad reciente.
- **Productos:** crear y editar nombre, descripción, categoría, deportes, especificaciones, imágenes y visibilidad.
- **Variantes:** crear y editar SKU, atributos, precio, oferta, medidas y peso.
- **Archivar:** sustituye a eliminar. Oculta el producto o la variante sin borrar pedidos, historial ni relaciones de la base de datos.
- **Inventario:** recibir, retirar o establecer existencias; exige motivo y registra usuario, referencia, notas y fecha.
- **Pedidos:** consulta operativa con búsqueda y filtros. Los cambios avanzados siguen disponibles en Django Admin.
- **Venta externa:** `/panel/venta-externa/` para efectivo, transferencia o tarjeta cobrada fuera del sistema.
- **Ubicaciones:** origen de envíos y puntos de recolección configurables.

Solo un superusuario puede entrar al panel de dueño. Si aún no existe, créalo con:

```powershell
python manage.py createsuperuser
```

## Catálogo inicial y autenticidad

Las tres raquetas de tenis se cargan con nombres genéricos y sin afirmar tecnologías o marcas originales. Las cuatro palas de pádel se importan ocultas con estado **Sin verificar**. Una restricción de base de datos impide publicar productos sin verificar. Antes de publicarlas, confirma factura, proveedor y autenticidad, y cambia su estado a **Original verificado** o renómbralas como genéricas.

## Datos pendientes antes del lanzamiento

- Colonia, código postal, teléfono y horario del origen temporal en 11 Poniente 2707.
- Código postal, teléfono y horario del punto de recolección en 9 Poniente 2709.
- Teléfono y horario de Orizaba.
- Dirección definitiva desde donde se entregan los paquetes a la paquetería.
- Existencias reales de cada variante.
- Peso y medidas de cada variante empacada.
- Credenciales de prueba y producción de Mercado Pago.
- Token sandbox y producción de Envia.com.
- Dominio, correo transaccional, aviso de privacidad, términos, política de cambios y devoluciones.
- Confirmación de autenticidad de las palas.

## Pruebas y validación

```powershell
python manage.py check
python manage.py test
python manage.py collectstatic --noinput
python manage.py check --deploy
```

Las pruebas incluyen que una última unidad no pueda asignarse a dos pedidos, devolución idempotente de stock y conservación del descuento después de un pago aprobado.

## Despliegue

`render.yaml`, `Procfile` y `Dockerfile` están incluidos. Antes de desplegar:

- establece `DJANGO_DEBUG=False`;
- configura un `DJANGO_SECRET_KEY` aleatorio;
- agrega dominio y origen HTTPS permitidos;
- usa PostgreSQL administrado;
- configura almacenamiento persistente para imágenes;
- ejecuta migraciones y `collectstatic`;
- usa HTTPS y prueba los webhooks reales.

El servidor productivo usa Gunicorn; `runserver` es únicamente para desarrollo.

