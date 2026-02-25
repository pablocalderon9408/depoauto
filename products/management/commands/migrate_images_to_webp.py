"""
Migra imágenes JPG/PNG existentes en S3 a WebP.

Lista todos los objetos en el bucket configurado, filtra .jpg/.jpeg/.png,
convierte cada uno a WebP, actualiza la base de datos para apuntar al WebP
y elimina los archivos originales.

Uso:
  python manage.py migrate_images_to_webp
  python manage.py migrate_images_to_webp --no-delete   # No eliminar originales

Requerido: USE_S3=true y variables AWS_* configuradas.
"""
import io
import os

from django.conf import settings
from django.core.management.base import BaseCommand
from products.models import Category, HeroSlide, Product, SiteConfig, VariantImage

try:
    from PIL import Image
except ImportError:
    Image = None

IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png')
WEBP_QUALITY = 80
CACHE_CONTROL = 'max-age=604800'

# Modelos y campos ImageField que almacenan rutas de archivos
IMAGE_FIELD_MAPPING = [
    (Category, 'image_file'),
    (Product, 'image_file'),
    (VariantImage, 'image_file'),
    (SiteConfig, 'hero_image_1_file'),
    (SiteConfig, 'hero_image_2_file'),
    (SiteConfig, 'hero_image_3_file'),
    (HeroSlide, 'image_file'),
]


def convert_to_webp(content: bytes) -> bytes | None:
    """Convierte bytes de imagen a WebP. Retorna None si falla."""
    if Image is None:
        return None
    try:
        img = Image.open(io.BytesIO(content)).copy()
    except Exception:
        return None

    if img.mode in ('RGBA', 'LA', 'P'):
        if img.mode == 'P' and 'transparency' in img.info:
            img = img.convert('RGBA')
        elif img.mode in ('LA', 'P'):
            img = img.convert('RGBA')
    elif img.mode not in ('RGB', 'RGBA'):
        img = img.convert('RGB')

    buffer = io.BytesIO()
    save_kwargs = {'format': 'WEBP', 'quality': WEBP_QUALITY}
    if img.mode == 'RGBA':
        save_kwargs['method'] = 6
    img.save(buffer, **save_kwargs)
    return buffer.getvalue()


def update_db_path(old_path: str, new_path: str) -> int:
    """
    Actualiza todos los registros que apuntan a old_path para que apunten a new_path.
    Retorna el número de registros actualizados.
    """
    total = 0
    for model, field_name in IMAGE_FIELD_MAPPING:
        filter_kwargs = {field_name: old_path}
        updated = model.objects.filter(**filter_kwargs).update(**{field_name: new_path})
        total += updated
    return total


class Command(BaseCommand):
    help = "Convierte imágenes JPG/PNG en S3 a WebP, actualiza BD y elimina originales"

    def add_arguments(self, parser):
        parser.add_argument(
            '--no-delete',
            action='store_true',
            help='No eliminar los archivos originales (.jpg/.png) de S3',
        )

    def handle(self, *args, **options):
        if not getattr(settings, 'USE_S3', False):
            self.stderr.write(
                self.style.ERROR("USE_S3 debe estar activo. Configura USE_S3=true y AWS_*.")
            )
            return

        bucket = getattr(settings, 'AWS_STORAGE_BUCKET_NAME', None) or os.environ.get(
            'AWS_STORAGE_BUCKET_NAME'
        )
        if not bucket:
            self.stderr.write(
                self.style.ERROR("AWS_STORAGE_BUCKET_NAME no configurado.")
            )
            return

        if Image is None:
            self.stderr.write(
                self.style.ERROR("Pillow no instalado. Ejecuta: pip install Pillow")
            )
            return

        import boto3
        from botocore.config import Config

        endpoint = getattr(settings, 'AWS_S3_ENDPOINT_URL', None) or os.environ.get(
            'AWS_S3_ENDPOINT_URL'
        )
        region = (
            getattr(settings, 'AWS_S3_REGION_NAME', None)
            or os.environ.get('AWS_S3_REGION_NAME')
            or os.environ.get('AWS_DEFAULT_REGION')
            or 'us-east-1'
        )
        location = getattr(settings, 'AWS_LOCATION', '') or ''

        client = boto3.client(
            's3',
            endpoint_url=endpoint or None,
            region_name=region,
            config=Config(signature_version='s3v4') if endpoint else None,
        )

        prefix = location.rstrip('/') + '/' if location else ''
        delete_originals = not options.get('no_delete', False)
        self.stdout.write(f"Listando objetos en s3://{bucket}/{prefix}...")
        if delete_originals:
            self.stdout.write("Los archivos originales se eliminarán tras la conversión.")
        else:
            self.stdout.write("Modo --no-delete: los originales no se eliminarán.")

        success_count = 0
        error_count = 0
        db_updated_count = 0

        paginator = client.get_paginator('list_objects_v2')
        for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
            for obj in page.get('Contents', []):
                key = obj['Key']
                ext = os.path.splitext(key)[1].lower()
                if ext not in IMAGE_EXTENSIONS:
                    continue

                webp_key = os.path.splitext(key)[0] + '.webp'
                if webp_key == key:
                    continue

                try:
                    resp = client.get_object(Bucket=bucket, Key=key)
                    raw = resp['Body'].read()
                except Exception as e:
                    self.stderr.write(
                        self.style.WARNING(f"  Error descargando {key}: {e}")
                    )
                    error_count += 1
                    continue

                webp_bytes = convert_to_webp(raw)
                if webp_bytes is None:
                    self.stderr.write(
                        self.style.WARNING(f"  No se pudo convertir {key}")
                    )
                    error_count += 1
                    continue

                try:
                    client.put_object(
                        Bucket=bucket,
                        Key=webp_key,
                        Body=webp_bytes,
                        ContentType='image/webp',
                        CacheControl=CACHE_CONTROL,
                    )
                except Exception as e:
                    self.stderr.write(
                        self.style.WARNING(f"  Error subiendo {webp_key}: {e}")
                    )
                    error_count += 1
                    continue

                # Ruta tal como la guarda Django en la BD (sin prefijo de location)
                db_path_old = key[len(prefix) :].lstrip('/') if prefix else key
                db_path_new = os.path.splitext(db_path_old)[0] + '.webp'

                updated = update_db_path(db_path_old, db_path_new)
                db_updated_count += updated
                if updated > 0:
                    self.stdout.write(
                        f"  OK: {key} -> {webp_key} (BD: {updated} registro(s) actualizado(s))"
                    )
                else:
                    self.stdout.write(f"  OK: {key} -> {webp_key} (sin referencias en BD)")
                success_count += 1

                if delete_originals:
                    try:
                        client.delete_object(Bucket=bucket, Key=key)
                        self.stdout.write(f"      Eliminado original: {key}")
                    except Exception as e:
                        self.stderr.write(
                            self.style.WARNING(f"  Error eliminando {key}: {e}")
                        )
                        error_count += 1

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                f"Migración completada: {success_count} convertidos, "
                f"{db_updated_count} referencias en BD actualizadas, "
                f"{error_count} errores."
            )
        )
