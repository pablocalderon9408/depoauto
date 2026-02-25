"""
Storage backend que convierte automáticamente imágenes JPG/PNG a WebP al subir a S3.

Solo aplica cuando USE_S3=true. Convierte JPG, JPEG y PNG a WebP con quality=80,
manejando correctamente transparencia (RGBA) y otros modos de imagen.
"""
import io
import os

from django.core.files.base import ContentFile
from storages.backends.s3boto3 import S3Boto3Storage

try:
    from PIL import Image
except ImportError:
    Image = None

# Extensiones que se convierten a WebP
IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png')
WEBP_QUALITY = 80


def _convert_to_webp(content) -> bytes | None:
    """
    Convierte bytes de imagen (JPG/PNG) a WebP.
    Retorna None si no es una imagen convertible.
    """
    if Image is None:
        return None
    try:
        img = Image.open(io.BytesIO(content)).copy()
    except Exception:
        return None

    # Convertir modos no soportados por WebP
    if img.mode in ('RGBA', 'LA', 'P'):
        # Mantener transparencia
        if img.mode == 'P' and 'transparency' in img.info:
            img = img.convert('RGBA')
        elif img.mode in ('LA', 'P'):
            img = img.convert('RGBA')
    elif img.mode not in ('RGB', 'RGBA'):
        img = img.convert('RGB')

    buffer = io.BytesIO()
    save_kwargs = {'format': 'WEBP', 'quality': WEBP_QUALITY}
    if img.mode == 'RGBA':
        save_kwargs['method'] = 6  # Mejor compresión para transparencia
    img.save(buffer, **save_kwargs)
    return buffer.getvalue()


class WebPS3Storage(S3Boto3Storage):
    """
    Storage S3 que convierte JPG/JPEG/PNG a WebP automáticamente al subir.
    No modifica archivos que no sean imágenes.
    """

    def _save(self, name, content):
        ext = os.path.splitext(name)[1].lower()
        if ext in IMAGE_EXTENSIONS:
            content.seek(0)
            raw = content.read()
            webp_bytes = _convert_to_webp(raw)
            if webp_bytes is not None:
                base, _ = os.path.splitext(name)
                name = base + '.webp'
                content = ContentFile(webp_bytes, name=name)
        return super()._save(name, content)
