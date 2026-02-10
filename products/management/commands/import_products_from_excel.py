from __future__ import annotations

import os
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, Tuple

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.conf import settings

from openpyxl import load_workbook
from django.utils.text import slugify

from products.models import Category, Product, ProductVariant


class Command(BaseCommand):
    help = "Importa categorías y productos desde un archivo Excel (.xlsx)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            dest="file_path",
            default="data.xlsx",
            help="Ruta al archivo .xlsx (por defecto: data.xlsx en la raíz del proyecto)",
        )
        parser.add_argument(
            "--sheet",
            dest="sheet_name",
            default=None,
            help="Nombre de la hoja a importar (por defecto, la activa)",
        )
        parser.add_argument(
            "--update",
            action="store_true",
            dest="do_update",
            help="Si existe un producto con el mismo SKU, actualizar sus datos",
        )

    def handle(self, *args, **options):
        file_path = options["file_path"]
        sheet_name = options["sheet_name"]
        do_update = options["do_update"]

        abs_path = file_path
        if not os.path.isabs(abs_path):
            abs_path = os.path.join(settings.BASE_DIR, file_path)
        if not os.path.exists(abs_path):
            raise CommandError(f"No se encontró el archivo: {abs_path}")

        wb = load_workbook(abs_path, data_only=True)
        ws = wb[sheet_name] if sheet_name else wb.active

        headers = self._read_headers(ws)
        if not headers:
            raise CommandError("La hoja no contiene encabezados válidos en la primera fila.")

        self.stdout.write(self.style.NOTICE(f"Encabezados detectados: {headers}"))
        mapped = self._map_columns(headers)
        self.stdout.write(self.style.NOTICE(f"Mapeo de columnas: {mapped}"))

        created_categories = 0
        created_products = 0
        updated_products = 0

        with transaction.atomic():
            for row_idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
                data = self._row_to_dict(row, headers)
                try:
                    category_name = (data.get(mapped["category"]) or "").strip()
                    if not category_name:
                        self.stdout.write(self.style.WARNING(f"Fila {row_idx}: sin categoría; saltando"))
                        continue
                    category, cat_created = Category.objects.get_or_create(name=category_name)
                    if cat_created:
                        created_categories += 1

                    name = (data.get(mapped["name"]) or "").strip()
                    sku = (data.get(mapped["sku"]) or "").strip()
                    if not sku:
                        self.stdout.write(self.style.WARNING(f"Fila {row_idx}: sin SKU; saltando"))
                        continue
                    if not name:
                        name = sku

                    # Campos opcionales: usar mapeo si existe
                    desc_col = mapped.get("description")
                    description = ((data.get(desc_col) if desc_col else "") or "").strip()

                    price_col = mapped.get("price")
                    price = self._parse_decimal(data.get(price_col)) if price_col else None

                    stock_col = mapped.get("stock")
                    stock = self._parse_int(data.get(stock_col)) if stock_col else None

                    image_col = mapped.get("image_url")
                    image_url = ((data.get(image_col) if image_col else "") or "").strip()

                    product_defaults = {
                        "name": name,
                        "category": category,
                        "description": description,
                        "price": price if price is not None else Decimal("0"),
                        "stock": stock if stock is not None else 0,
                        "is_active": True,
                    }
                    if image_url:
                        product_defaults["image_url"] = image_url

                    # Crear o actualizar por SKU asegurando slug único
                    obj = Product.objects.filter(sku=sku).first()
                    if obj is None:
                        unique_slug = self._make_unique_product_slug(name, sku)
                        payload = {**product_defaults, "sku": sku, "slug": unique_slug}
                        obj = Product(**payload)
                        obj.save()
                        created_products += 1
                    else:
                        if do_update:
                            for field, value in product_defaults.items():
                                setattr(obj, field, value)
                            obj.slug = self._make_unique_product_slug(name, sku, exclude_id=obj.id)
                            obj.save()
                            updated_products += 1

                    # Asegurar al menos una variante vacía
                    ProductVariant.objects.get_or_create(product=obj, name="")
                except Exception as exc:
                    raise CommandError(f"Error en fila {row_idx}: {exc}") from exc

        self.stdout.write(self.style.SUCCESS(
            f"Importación completada. Categorías nuevas: {created_categories}, "
            f"Productos creados: {created_products}, Productos actualizados: {updated_products}"
        ))

    def _read_headers(self, ws) -> Tuple[str, ...]:
        header_row = next(ws.iter_rows(min_row=1, max_row=1, values_only=True))
        headers = tuple((h or "").strip() for h in header_row)
        return headers

    def _row_to_dict(self, row: Tuple[Any, ...], headers: Tuple[str, ...]) -> Dict[str, Any]:
        return {headers[i]: row[i] for i in range(min(len(headers), len(row)))}

    def _map_columns(self, headers: Tuple[str, ...]) -> Dict[str, str]:
        # Sinónimos aceptados por campo
        synonyms = {
            "category": {"categoria", "category", "cat", "familia"},
            "name": {"nombre", "name", "titulo", "título", "producto"},
            "sku": {"sku", "codigo", "código", "codigo_sku", "id", "referencia"},
            "price": {"precio", "price", "valor"},
            "stock": {"stock", "cantidad", "inventario", "existencias"},
            "description": {"descripcion", "descripción", "description", "detalle"},
            "image_url": {"imagen", "imagen_url", "image", "image_url", "foto", "foto_url"},
        }

        lower_headers = {h.lower(): h for h in headers if h}
        mapping: Dict[str, str] = {}
        for field, keys in synonyms.items():
            found = None
            for k in keys:
                if k in lower_headers:
                    found = lower_headers[k]
                    break
            if not found:
                # Campos obligatorios mínimos
                if field in {"category", "sku"}:
                    raise CommandError(f"No se encontró la columna obligatoria para '{field}'. Encabezados: {headers}")
            else:
                mapping[field] = found
        # El nombre puede faltar; usaremos SKU como nombre en ese caso
        if "name" not in mapping:
            mapping["name"] = mapping.get("sku", "sku")
        return mapping

    def _parse_decimal(self, value: Any) -> Decimal | None:
        if value is None or value == "":
            return None
        if isinstance(value, (int, float, Decimal)):
            try:
                return Decimal(str(value))
            except Exception:
                return None
        if isinstance(value, str):
            txt = value.replace("$", "").replace(",", "").strip()
            try:
                return Decimal(txt)
            except InvalidOperation:
                return None
        return None

    def _make_unique_product_slug(self, name: str, sku: str, exclude_id: int | None = None) -> str:
        base = slugify(name) or slugify(sku) or sku.lower()
        candidate = base
        counter = 2
        qs = Product.objects.all()
        if exclude_id:
            qs = qs.exclude(id=exclude_id)
        while qs.filter(slug=candidate).exists():
            candidate = f"{base}-{counter}"
            counter += 1
        return candidate

    def _parse_int(self, value: Any) -> int | None:
        if value is None or value == "":
            return None
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            try:
                return int(value)
            except Exception:
                return None
        if isinstance(value, str):
            txt = value.strip()
            try:
                return int(txt)
            except Exception:
                return None
        return None


