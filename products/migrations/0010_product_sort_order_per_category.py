from django.db import migrations, models


def normalize_sort_order_per_category(apps, schema_editor):
    Product = apps.get_model('products', 'Product')
    seen_categories = set()
    for product in Product.objects.all().order_by('category_id', 'sort_order', 'name', 'id'):
        seen_categories.add(product.category_id)

    for category_id in sorted(seen_categories):
        rows = list(
            Product.objects.filter(category_id=category_id).order_by('sort_order', 'name', 'id')
        )
        for position, p in enumerate(rows, start=1):
            Product.objects.filter(pk=p.pk).update(sort_order=position * 10)


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0009_product_sort_order'),
    ]

    operations = [
        migrations.RunPython(normalize_sort_order_per_category, noop_reverse),
        migrations.AlterField(
            model_name='product',
            name='sort_order',
            field=models.PositiveIntegerField(
                db_index=True,
                default=0,
                help_text='Orden dentro de la categoría (menor = primero).',
            ),
        ),
        migrations.AlterModelOptions(
            name='product',
            options={'ordering': ['category__name', 'sort_order', 'name']},
        ),
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['category', 'sort_order'], name='product_category_sort_idx'),
        ),
    ]
