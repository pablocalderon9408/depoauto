from django.contrib import admin
from django.forms import ModelForm, PasswordInput
from django.shortcuts import redirect
from django.urls import reverse
from .models import Category, Product, ProductVariant, VariantImage, RelatedProduct, SiteConfig, HeroSlide


class SiteConfigForm(ModelForm):
    class Meta:
        model = SiteConfig
        fields = "__all__"
        widgets = {
            "email_smtp_password": PasswordInput(attrs={"autocomplete": "new-password", "placeholder": "Dejar vacío para mantener la actual"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["email_smtp_password"].required = False

    def save(self, commit=True):
        obj = super().save(commit=False)
        # No sobrescribir la contraseña si el usuario dejó el campo vacío
        if not self.cleaned_data.get("email_smtp_password") and obj.pk:
            obj.email_smtp_password = SiteConfig.objects.get(pk=obj.pk).email_smtp_password
        if commit:
            obj.save()
        return obj


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
    form = SiteConfigForm
    inlines = []
    fieldsets = (
        ("Carrusel - Slide 1", {"fields": ("hero_title_1", "hero_subtitle_1", "hero_image_1_url", "hero_image_1_file", "hero_cta_1_label", "hero_cta_1_url")}),
        ("Carrusel - Slide 2", {"fields": ("hero_title_2", "hero_subtitle_2", "hero_image_2_url", "hero_image_2_file", "hero_cta_2_label", "hero_cta_2_url")}),
        ("Carrusel - Slide 3", {"fields": ("hero_title_3", "hero_subtitle_3", "hero_image_3_url", "hero_image_3_file", "hero_cta_3_label", "hero_cta_3_url")}),
        ("Sección: Categorías destacadas", {"fields": (
            "show_top_categories", "home_top_categories_title", "home_top_categories_limit",
            "home_top_categories_cta_label", "home_top_categories_cta_url",
        )}),
        ("Sección: Novedades", {"fields": (
            "show_new_arrivals", "home_new_arrivals_title", "home_new_arrivals_limit",
            "home_new_arrivals_cta_label", "home_new_arrivals_cta_url",
        )}),
        ("Contacto / WhatsApp", {"fields": ("contact_phone", "whatsapp_prefill")}),
        ("Email (formulario de contacto)", {"fields": ("contact_email", "email_smtp_user", "email_smtp_password")}),
    )
    def has_add_permission(self, request):
        return not SiteConfig.objects.exists()

    def changelist_view(self, request, extra_context=None):
        # Redirigir directamente a editar la única instancia
        obj = SiteConfig.get_solo()
        url = reverse('admin:products_siteconfig_change', args=[obj.pk])
        return redirect(url)


class HeroSlideInline(admin.TabularInline):
    model = HeroSlide
    extra = 1
    fields = ("title", "subtitle", "image_url", "image_file", "cta_label", "cta_url", "is_active", "sort_order")


SiteConfigAdmin.inlines = [HeroSlideInline]


@admin.register(HeroSlide)
class HeroSlideAdmin(admin.ModelAdmin):
    list_display = ("title", "is_active", "sort_order", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("title", "subtitle")
    ordering = ("sort_order", "id")
    fields = ("title", "subtitle", "image_url", "image_file", "cta_label", "cta_url", "is_active", "sort_order")
