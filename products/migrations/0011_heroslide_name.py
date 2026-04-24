from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("products", "0010_product_sort_order_per_category"),
    ]

    operations = [
        migrations.AddField(
            model_name="heroslide",
            name="name",
            field=models.CharField(
                blank=True,
                help_text="Identificador corto solo para el listado del admin (ej. Promo verano, Banner principal).",
                max_length=120,
                verbose_name="Nombre en admin",
            ),
        ),
    ]
