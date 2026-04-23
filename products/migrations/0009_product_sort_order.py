from django.db import migrations, models


def initialize_sort_order(apps, schema_editor):
    Product = apps.get_model('products', 'Product')
    for index, product in enumerate(Product.objects.all().order_by('name', 'id'), start=1):
        product.sort_order = index * 10
        product.save(update_fields=['sort_order'])


def reverse_sort_order(apps, schema_editor):
    Product = apps.get_model('products', 'Product')
    Product.objects.all().update(sort_order=0)


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0008_increase_imagefile_max_length'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='sort_order',
            field=models.PositiveIntegerField(db_index=True, default=0),
        ),
        migrations.AlterModelOptions(
            name='product',
            options={'ordering': ['sort_order', 'name']},
        ),
        migrations.RunPython(initialize_sort_order, reverse_sort_order),
    ]
