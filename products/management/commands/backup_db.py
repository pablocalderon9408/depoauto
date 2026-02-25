"""
Backup de la base de datos PostgreSQL a S3 (o local si S3 no está configurado).

Uso:
  python manage.py backup_db

Variables de entorno:
  DATABASE_URL          - Conexión a PostgreSQL (requerido para backup)
  BACKUP_S3_BUCKET      - Bucket S3 donde guardar (opcional)
  BACKUP_S3_PREFIX      - Prefijo en el bucket, ej: db-backups/ (default)
  BACKUP_RETENTION_DAYS - Días de retención, eliminar backups más antiguos (default: 30)
  AWS_*                 - Credenciales S3 (o IAM role en EC2)

Si BACKUP_S3_BUCKET no está definido, se usa AWS_STORAGE_BUCKET_NAME con prefijo db-backups/
Si no hay S3 configurado, se guarda en ./backups/ (crear el directorio si no existe)
"""
import gzip
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand


def get_db_config():
    """Extrae host, port, user, password, dbname de DATABASE_URL."""
    db = settings.DATABASES.get("default", {})
    engine = db.get("ENGINE", "")
    if "postgresql" not in engine:
        return None
    return {
        "host": db.get("HOST") or "localhost",
        "port": db.get("PORT") or "5432",
        "user": db.get("USER") or "",
        "password": db.get("PASSWORD") or "",
        "dbname": db.get("NAME") or "",
    }


def run_pg_dump(config) -> bytes:
    """Ejecuta pg_dump y devuelve el dump como bytes."""
    env = os.environ.copy()
    if config["password"]:
        env["PGPASSWORD"] = config["password"]

    cmd = [
        "pg_dump",
        "-h", config["host"],
        "-p", str(config["port"]),
        "-U", config["user"],
        "-d", config["dbname"],
        "--no-owner",
        "--no-acl",
    ]

    result = subprocess.run(cmd, capture_output=True, env=env, timeout=3600)
    if result.returncode != 0:
        raise RuntimeError(f"pg_dump falló: {result.stderr.decode()}")
    return result.stdout


def upload_to_s3(data: bytes, key: str) -> None:
    """Sube bytes a S3."""
    import boto3
    from botocore.config import Config

    bucket = os.environ.get("BACKUP_S3_BUCKET") or os.environ.get("AWS_STORAGE_BUCKET_NAME")
    if not bucket:
        raise ValueError("BACKUP_S3_BUCKET o AWS_STORAGE_BUCKET_NAME requerido para subir a S3")

    prefix = os.environ.get("BACKUP_S3_PREFIX", "db-backups/").rstrip("/") + "/"
    full_key = f"{prefix}{key}"

    endpoint = os.environ.get("AWS_S3_ENDPOINT_URL") or None
    region = os.environ.get("AWS_S3_REGION_NAME") or os.environ.get("AWS_DEFAULT_REGION") or "us-east-1"

    client = boto3.client(
        "s3",
        endpoint_url=endpoint,
        region_name=region,
        config=Config(signature_version="s3v4") if endpoint else None,
    )

    client.put_object(
        Bucket=bucket,
        Key=full_key,
        Body=data,
        ContentType="application/gzip",
    )


def list_and_prune_s3(retention_days: int) -> None:
    """Lista backups en S3 y elimina los más antiguos que retention_days."""
    import boto3

    bucket = os.environ.get("BACKUP_S3_BUCKET") or os.environ.get("AWS_STORAGE_BUCKET_NAME")
    if not bucket:
        return

    prefix = os.environ.get("BACKUP_S3_PREFIX", "db-backups/").rstrip("/") + "/"
    endpoint = os.environ.get("AWS_S3_ENDPOINT_URL") or None
    region = os.environ.get("AWS_S3_REGION_NAME") or os.environ.get("AWS_DEFAULT_REGION") or "us-east-1"

    client = boto3.client(
        "s3",
        endpoint_url=endpoint,
        region_name=region,
    )

    paginator = client.get_paginator("list_objects_v2")
    cutoff = datetime.utcnow().replace(tzinfo=None).timestamp() - (retention_days * 86400)

    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            if obj["LastModified"].timestamp() < cutoff:
                client.delete_object(Bucket=bucket, Key=obj["Key"])
                print(f"  Eliminado backup antiguo: {obj['Key']}")


class Command(BaseCommand):
    help = "Backup de PostgreSQL a S3 (o local)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--local-only",
            action="store_true",
            help="Guardar solo en disco local, no subir a S3",
        )
        parser.add_argument(
            "--retention-days",
            type=int,
            default=int(os.environ.get("BACKUP_RETENTION_DAYS", "30")),
            help="Días de retención para eliminar backups antiguos en S3",
        )

    def handle(self, *args, **options):
        config = get_db_config()
        if not config:
            self.stdout.write(self.style.WARNING("Solo se soporta backup de PostgreSQL. SQLite no requiere backup."))
            return

        timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        filename = f"depoauto-{timestamp}.sql.gz"

        self.stdout.write("Ejecutando pg_dump...")
        try:
            raw = run_pg_dump(config)
        except FileNotFoundError:
            self.stderr.write(
                self.style.ERROR(
                    "pg_dump no encontrado. Instala postgresql-client en el contenedor/imagen."
                )
            )
            sys.exit(1)
        except Exception as e:
            self.stderr.write(self.style.ERROR(str(e)))
            sys.exit(1)

        compressed = gzip.compress(raw)
        self.stdout.write(f"  Dump comprimido: {len(compressed) / 1024:.1f} KB")

        if options["local_only"]:
            out_dir = Path("backups")
            out_dir.mkdir(exist_ok=True)
            out_path = out_dir / filename
            out_path.write_bytes(compressed)
            self.stdout.write(self.style.SUCCESS(f"Backup guardado en {out_path}"))
            return

        bucket = os.environ.get("BACKUP_S3_BUCKET") or os.environ.get("AWS_STORAGE_BUCKET_NAME")
        if bucket:
            self.stdout.write(self.style.SUCCESS(f"Subiendo a S3: {bucket}/{filename}"))
            try:
                upload_to_s3(compressed, filename)
                self.stdout.write(self.style.SUCCESS("Backup subido correctamente."))
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Error subiendo a S3: {e}"))
                sys.exit(1)

            if options["retention_days"] > 0:
                self.stdout.write(f"Eliminando backups más antiguos de {options['retention_days']} días...")
                try:
                    list_and_prune_s3(options["retention_days"])
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"Advertencia al limpiar backups: {e}"))
        else:
            out_dir = Path("backups")
            out_dir.mkdir(exist_ok=True)
            out_path = out_dir / filename
            out_path.write_bytes(compressed)
            self.stdout.write(
                self.style.WARNING(
                    "BACKUP_S3_BUCKET no configurado. Backup guardado localmente en "
                    f"{out_path}. Configura S3 para subir automáticamente."
                )
            )
