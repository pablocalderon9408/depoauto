from django.db import models
from django.utils.text import slugify
from django.core.exceptions import ValidationError


class Category(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    description = models.TextField(blank=True)
    image_url = models.URLField(max_length=500, blank=True)
    image_file = models.ImageField(upload_to='categories/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def image_url_display(self) -> str | None:
        if getattr(self, 'image_file', None) and self.image_file:
            try:
                return self.image_file.url
            except Exception:
                pass
        return self.image_url or None

    def clean(self) -> None:
        # Allow either URL or file or none, but not both simultaneously to avoid ambiguity
        if self.image_url and self.image_file:
            raise ValidationError({
                'image_url': 'Proporcione URL o archivo, no ambos.',
                'image_file': 'Proporcione URL o archivo, no ambos.',
            })


class Product(models.Model):
    name = models.CharField(max_length=160)
    slug = models.SlugField(max_length=180, unique=True, blank=True)
    sku = models.CharField(max_length=64, unique=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    description = models.TextField(blank=True)
    # Deprecated at UI level: mantenido por compatibilidad, preferir imágenes en variantes
    image_url = models.URLField(max_length=500, blank=True)
    image_file = models.ImageField(upload_to='products/', blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    related_products = models.ManyToManyField(
        'self',
        through='RelatedProduct',
        symmetrical=False,
        related_name='related_by',
        through_fields=('from_product', 'to_product'),
        blank=True,
    )

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["sku"]),
            models.Index(fields=["name"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.sku})"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def image_url_display(self) -> str | None:
        # Prefer main image from variants if available; fallback to product-level fields
        # Look for a main image across variants
        try:
            main_image = (
                VariantImage.objects
                .filter(variant__product=self, is_main=True)
                .select_related('variant')
                .order_by('variant__id', 'sort_order', 'id')
                .first()
            )
        except Exception:
            main_image = None
        if main_image:
            return main_image.image_url_display
        # Fallback to first variant image
        try:
            first_image = (
                VariantImage.objects
                .filter(variant__product=self)
                .select_related('variant')
                .order_by('variant__id', 'sort_order', 'id')
                .first()
            )
        except Exception:
            first_image = None
        if first_image:
            return first_image.image_url_display
        # Final fallback to product-level fields
        if getattr(self, 'image_file', None) and self.image_file:
            try:
                return self.image_file.url
            except Exception:
                pass
        return self.image_url or None

    @property
    def gallery_images(self):
        """Return an ordered queryset of VariantImage for this product."""
        return (
            VariantImage.objects
            .filter(variant__product=self)
            .select_related('variant')
            .order_by('-is_main', 'variant__id', 'sort_order', 'id')
        )


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    name = models.CharField(max_length=160, blank=True, default="")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["id"]

    def __str__(self) -> str:
        base = self.product.name
        return f"{base} - {self.name or 'Variant'}"


class VariantImage(models.Model):
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name="images")
    image_url = models.URLField(max_length=500, blank=True, null=True)
    image_file = models.ImageField(upload_to='products/variants/', blank=True, null=True)
    alt_text = models.CharField(max_length=200, blank=True)
    sort_order = models.PositiveSmallIntegerField(default=0)
    is_main = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["sort_order", "id"]
        constraints = [
            models.CheckConstraint(
                check=(models.Q(image_url__isnull=False) | models.Q(image_file__isnull=False)),
                name="ck_variantimage_has_url_or_file",
            ),
            models.UniqueConstraint(
                fields=["variant"], condition=models.Q(is_main=True), name="uq_variantimage_main_per_variant"
            ),
        ]

    def __str__(self) -> str:
        return f"Image for {self.variant}"

    @property
    def image_url_display(self) -> str | None:
        if getattr(self, 'image_file', None) and self.image_file:
            try:
                return self.image_file.url
            except Exception:
                pass
        return self.image_url or None


class SiteConfig(models.Model):
    # Hero slides (up to 3)
    hero_title_1 = models.CharField(max_length=160, blank=True)
    hero_subtitle_1 = models.CharField(max_length=240, blank=True)
    hero_image_1_url = models.URLField(max_length=500, blank=True)
    hero_image_1_file = models.ImageField(upload_to='site/hero/', blank=True, null=True)

    hero_title_2 = models.CharField(max_length=160, blank=True)
    hero_subtitle_2 = models.CharField(max_length=240, blank=True)
    hero_image_2_url = models.URLField(max_length=500, blank=True)
    hero_image_2_file = models.ImageField(upload_to='site/hero/', blank=True, null=True)

    hero_title_3 = models.CharField(max_length=160, blank=True)
    hero_subtitle_3 = models.CharField(max_length=240, blank=True)
    hero_image_3_url = models.URLField(max_length=500, blank=True)
    hero_image_3_file = models.ImageField(upload_to='site/hero/', blank=True, null=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Site configuration"
        verbose_name_plural = "Site configuration"

    def __str__(self) -> str:
        return "Site configuration"

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(id=1)
        return obj

    def _image_url_from_pair(self, url: str, file_field) -> str | None:
        if getattr(file_field, 'url', None):
            try:
                return file_field.url
            except Exception:
                pass
        return url or None

    @property
    def hero_slides(self):
        slides = []
        pairs = [
            (self.hero_title_1, self.hero_subtitle_1, self.hero_image_1_url, self.hero_image_1_file),
            (self.hero_title_2, self.hero_subtitle_2, self.hero_image_2_url, self.hero_image_2_file),
            (self.hero_title_3, self.hero_subtitle_3, self.hero_image_3_url, self.hero_image_3_file),
        ]
        for title, subtitle, url, file_field in pairs:
            effective_url = self._image_url_from_pair(url, file_field)
            if effective_url:
                slides.append({
                    'image_url': effective_url,
                    'title': title,
                    'subtitle': subtitle,
                })
        return slides


class RelatedProduct(models.Model):
    from_product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='related_from')
    to_product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='related_to')
    sort_order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["sort_order", "id"]
        constraints = [
            models.UniqueConstraint(fields=["from_product", "to_product"], name="uq_related_from_to"),
            models.CheckConstraint(check=~models.Q(from_product=models.F('to_product')), name='ck_no_self_related'),
        ]

    def __str__(self) -> str:
        return f"{self.from_product} -> {self.to_product}"
