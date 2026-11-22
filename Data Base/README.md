# Base de datos de Agave Website

Esta carpeta reúne la documentación, consultas de validación y herramientas de respaldo de la base de datos del sitio.

## Base de producción

- Motor: PostgreSQL administrado por Supabase.
- Proyecto: `agave-basic-website`.
- Panel: https://supabase.com/dashboard/project/lhzpojsvadkbvicdwnun
- Editor de tablas: https://supabase.com/dashboard/project/lhzpojsvadkbvicdwnun/editor
- Las credenciales no se guardan en Git ni dentro de esta carpeta.
- Render recibe `DATABASE_URL` como variable secreta.

## Base local

Cuando `DATABASE_URL` no está definida, Django usa `db.sqlite3` para desarrollo. Ese archivo puede contener usuarios, contraseñas cifradas y datos de prueba, por lo que permanece fuera de Git y no debe compartirse.

## Dónde está el esquema operativo

Django necesita conservar el esquema ejecutable en estas ubicaciones:

- `store/models.py`: definición actual de entidades, relaciones y restricciones.
- `store/migrations/`: historial que crea y actualiza las tablas.
- `store/management/commands/seed_catalog.py`: carga inicial del catálogo.

La subcarpeta `django_snapshot` contiene una copia de referencia. No debe editarse como fuente principal: cualquier cambio real debe hacerse en `store/models.py` y convertirse en una nueva migración.

## Flujo correcto para cambios

```powershell
python manage.py makemigrations
python manage.py migrate
python manage.py check
python manage.py test
```

Después de validar, se suben los cambios al repositorio de despliegue y Render ejecuta las migraciones durante la compilación.

## Respaldos

Los scripts de esta carpeta leen la conexión desde la variable de entorno `DATABASE_URL`; nunca incluyen contraseñas.

```powershell
$env:DATABASE_URL = "postgresql://..."
.\02_respaldo_esquema.ps1
.\03_respaldo_completo.ps1
```

Los archivos generados se guardan en `backups/`. No deben subirse a Git ni enviarse por correo o mensajería sin revisar su contenido.

## Archivos

- `01_verificar_base.sql`: conteos y revisión de restricciones, índices y migraciones.
- `02_respaldo_esquema.ps1`: exporta solamente la estructura PostgreSQL.
- `03_respaldo_completo.ps1`: crea un respaldo completo en formato de `pg_dump`.
- `MODELO_LOGICO.md`: inventario legible de entidades y decisiones importantes.
- `django_snapshot/`: copia documental del modelo y las migraciones vigentes.

