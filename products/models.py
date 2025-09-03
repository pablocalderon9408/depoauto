from django.db import models
from django.utils.text import slugify


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


class Product(models.Model):
    name = models.CharField(max_length=160)
    slug = models.SlugField(max_length=180, unique=True, blank=True)
    sku = models.CharField(max_length=64, unique=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    description = models.TextField(blank=True)
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
        if getattr(self, 'image_file', None) and self.image_file:
            try:
                return self.image_file.url
            except Exception:
                pass
        return self.image_url or None


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image_url = models.URLField(max_length=500)
    image_file = models.ImageField(upload_to='products/gallery/', blank=True, null=True)
    alt_text = models.CharField(max_length=200, blank=True)
    sort_order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self) -> str:
        return f"Image for {self.product.name}"

    @property
    def image_url_display(self) -> str | None:
        if getattr(self, 'image_file', None) and self.image_file:
            try:
                return self.image_file.url
            except Exception:
                pass
        return self.image_url or None


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
