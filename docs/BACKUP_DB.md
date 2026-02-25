# Backup automático de la base de datos

## Descripción

El comando `backup_db` crea un dump comprimido de PostgreSQL y lo sube a S3 (o lo guarda localmente si S3 no está configurado). Protege contra pérdida de datos si la EC2 falla.

## Uso manual

```bash
# Con Docker (local)
make backup

# O directamente
docker-compose exec web python manage.py backup_db
```

## Configuración en EC2 (producción)

### 1. Variables de entorno

Añade a tu `.env` o configuración de producción:

```bash
# Bucket S3 para backups (puede ser el mismo que media o uno dedicado)
BACKUP_S3_BUCKET=depoauto-backups

# Prefijo dentro del bucket (opcional, default: db-backups/)
BACKUP_S3_PREFIX=db-backups/

# Retención: eliminar backups más antiguos (días, default: 30)
BACKUP_RETENTION_DAYS=30

# Credenciales AWS (o usa IAM role de la EC2)
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_S3_REGION_NAME=us-east-1
```

### 2. Crear bucket S3 (si no existe)

```bash
aws s3 mb s3://depoauto-backups --region us-east-1
```

### 3. Cron para ejecución periódica

En la EC2, edita el crontab:

```bash
crontab -e
```

Añade una línea para ejecutar el backup diariamente a las 2:00 AM:

```cron
0 2 * * * cd /ruta/a/depoauto && docker-compose exec -T web python manage.py backup_db >> /var/log/depoauto-backup.log 2>&1
```

O si usas `docker-compose -f docker-compose.prod.yml`:

```cron
0 2 * * * cd /ruta/a/depoauto && docker-compose -f docker-compose.prod.yml exec -T web python manage.py backup_db >> /var/log/depoauto-backup.log 2>&1
```

### 4. Restaurar desde un backup

```bash
# Descargar el backup desde S3
aws s3 cp s3://depoauto-backups/db-backups/depoauto-20250224-020000.sql.gz ./

# Descomprimir y restaurar
gunzip -c depoauto-20250224-020000.sql.gz | docker-compose exec -T db psql -U depoauto -d depoauto
```

## Opciones del comando

```bash
# Guardar solo localmente (no subir a S3)
python manage.py backup_db --local-only

# Cambiar retención (ej: 7 días)
python manage.py backup_db --retention-days 7
```

## Notas

- **Solo PostgreSQL**: si usas SQLite, el comando no hace nada (SQLite no requiere backup en producción).
- **pg_dump**: el contenedor web incluye `postgresql-client` para ejecutar `pg_dump`.
- **IAM en EC2**: si la instancia tiene un rol IAM con permisos S3, no necesitas `AWS_ACCESS_KEY_ID` ni `AWS_SECRET_ACCESS_KEY`.
