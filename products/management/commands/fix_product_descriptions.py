from __future__ import annotations

import re
from typing import Optional

from django.core.management.base import BaseCommand
from django.db import transaction

from products.models import Product


class Command(BaseCommand):
    help = "Normaliza descripciones: agrega salto de línea antes de cada '✅' y homogeniza saltos."

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            default=False,
            help="Aplica los cambios en la base de datos (por defecto solo muestra un resumen).",
        )
        parser.add_argument(
            "--only-with-check",
            action="store_true",
            default=False,
            help="Procesa solo productos cuya descripción contenga '✅'.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=0,
            help="Limita el número de productos a procesar (0 = sin límite).",
        )

    def handle(self, *args, **options):
        apply_changes: bool = options["apply"]
        only_with_check: bool = options["only_with_check"]
        limit: int = options["limit"] or 0

        qs = Product.objects.all().order_by("id")
        if only_with_check:
            qs = qs.filter(description__icontains="✅")
        if limit > 0:
            qs = qs[:limit]

        total = qs.count()
        changed = 0

        self.stdout.write(self.style.NOTICE(f"Productos a revisar: {total}"))

        ctx = transaction.atomic() if apply_changes else _nullcontext()
        with ctx:
            for p in qs:
                original = p.description or ""
                updated = self._normalize_text(original)
                if updated != original:
                    changed += 1
                    if apply_changes:
                        p.description = updated
                        p.save(update_fields=["description"])
        if apply_changes:
            self.stdout.write(self.style.SUCCESS(f"Productos modificados: {changed}/{total}"))
        else:
            self.stdout.write(self.style.WARNING(f"[DRY-RUN] Se modificarían {changed}/{total} productos"))

    def _normalize_text(self, text: str) -> str:
        if not text:
            return text
        # Normalizar saltos de línea a \n
        t = text.replace("\r\n", "\n").replace("\r", "\n")
        # Insertar \n antes de cada '✅' si no está al inicio de la cadena y no hay ya un \n antes
        # (evita generar dobles saltos al re-ejecutar)
        t = re.sub(r"(?<!\n)(?<!^)✅", r"\n✅", t)
        # Colapsar más de 2 saltos de línea consecutivos en solo 2
        t = re.sub(r"\n{3,}", "\n\n", t)
        return t


class _nullcontext:
    def __enter__(self):
        return None

    def __exit__(self, exc_type, exc, tb):
        return False


