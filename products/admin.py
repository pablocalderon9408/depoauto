from django.contrib import admin
from .models import Category, Product, ProductImage, RelatedProduct


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("name",)
    fields = ("name", "slug", "description", "image_url", "image_file", "is_active")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "sku", "category", "price", "stock", "is_active")
    list_filter = ("category", "is_active")
    search_fields = ("name", "sku", "slug", "description")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("name",)
    fields = ("name", "slug", "sku", "category", "description", "image_url", "image_file", "price", "stock", "is_active")


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ("image_url", "image_file", "alt_text", "sort_order")


ProductAdmin.inlines = [ProductImageInline]


class RelatedProductInline(admin.TabularInline):
    model = RelatedProduct
    fk_name = 'from_product'
    extra = 1
    fields = ("to_product", "sort_order")


ProductAdmin.inlines.append(RelatedProductInline)
