from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("products", "0011_heroslide_name"),
    ]

    operations = [
        migrations.AlterField(
            model_name="product",
            name="sort_order",
            field=models.PositiveIntegerField(
                db_index=True,
                default=0,
                help_text="Dentro de la misma categoría: número más bajo = aparece primero en el catálogo. Conviene usar 10, 20, 30… para poder insertar productos entre otros sin reordenar todo.",
                verbose_name="Orden",
            ),
        ),
    ]
