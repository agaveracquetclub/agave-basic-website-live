# Agave Website — despliegue

## Enlaces

- Sitio público: https://agave-racquet-club.onrender.com/
- Render: https://dashboard.render.com/web/srv-dc1lbarl550s73er14cg
- Supabase: https://supabase.com/dashboard/project/lhzpojsvadkbvicdwnun
- Tablas de Supabase: https://supabase.com/dashboard/project/lhzpojsvadkbvicdwnun/editor
- Repositorio privado principal: https://github.com/agaveracquetclub/agave-basic-website
- Repositorio público de despliegue: https://github.com/agaveracquetclub/agave-basic-website-live

## Arquitectura

- Django y Gunicorn en Render Free.
- PostgreSQL en Supabase.
- Recursos iniciales del catálogo incluidos como archivos estáticos.
- Mercado Pago y Envia.com quedan desactivados hasta agregar sus credenciales.

## Operación

Render ejecuta durante cada despliegue:

```text
pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate --noinput
gunicorn agave_site.wsgi:application
```

El plan gratuito de Render se suspende después de un periodo sin tráfico; la primera visita puede tardar alrededor de un minuto.

## Seguridad

- Las contraseñas y tokens viven únicamente como variables secretas del servidor.
- `.env`, `db.sqlite3`, `media/`, `.venv/` y respaldos no se publican.
- Nunca pegues `DATABASE_URL`, tokens de Mercado Pago o tokens de Envia.com en GitHub.

## Actualizaciones

El código fuente principal se trabaja en la carpeta local y el repositorio privado. La copia pública se creó como repositorio de despliegue y no contiene credenciales. Antes de publicar cambios se deben ejecutar:

```powershell
python manage.py check
python manage.py test
python manage.py collectstatic --noinput
```

