from django.contrib import admin
from .models import Category, Product, ProductVariant, VariantImage, RelatedProduct, SiteConfig


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


class VariantImageInline(admin.TabularInline):
    model = VariantImage
    extra = 1
    fields = ("image_url", "image_file", "alt_text", "sort_order", "is_main")


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    fields = ("name", "is_active")


ProductAdmin.inlines = [ProductVariantInline]


class RelatedProductInline(admin.TabularInline):
    model = RelatedProduct
    fk_name = 'from_product'
    extra = 1
    fields = ("to_product", "sort_order")


ProductAdmin.inlines.append(RelatedProductInline)


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ("product", "name", "is_active")
    list_filter = ("is_active", "product")
    search_fields = ("name", "product__name", "product__sku")
    inlines = [VariantImageInline]


@admin.register(SiteConfig)
class SiteConfigAdmin(admin.ModelAdmin):
    fieldsets = (
        ("Hero 1", {"fields": ("hero_title_1", "hero_subtitle_1", "hero_image_1_url", "hero_image_1_file")}),
        ("Hero 2", {"fields": ("hero_title_2", "hero_subtitle_2", "hero_image_2_url", "hero_image_2_file")}),
        ("Hero 3", {"fields": ("hero_title_3", "hero_subtitle_3", "hero_image_3_url", "hero_image_3_file")}),
    )
    def has_add_permission(self, request):
        # Single instance
        return not SiteConfig.objects.exists()
