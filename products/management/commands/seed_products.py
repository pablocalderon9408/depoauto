import random
from decimal import Decimal
from django.core.management.base import BaseCommand
from faker import Faker
from products.models import Category, Product, ProductVariant, VariantImage, RelatedProduct, SiteConfig


class Command(BaseCommand):
    help = "Seed categories and products with dummy data"

    def add_arguments(self, parser):
        parser.add_argument('--categories', type=int, default=5)
        parser.add_argument('--products-per-category', type=int, default=20)

    def handle(self, *args, **options):
        fake = Faker()

        num_categories = options['categories']
        num_products_per_category = options['products_per_category']

        self.stdout.write(self.style.NOTICE(f"Creating {num_categories} categories..."))
        categories = []
        for i in range(num_categories):
            name = f"{fake.word().capitalize()} Parts"
            category, _ = Category.objects.get_or_create(name=name)
            category.is_active = True
            category.image_url = f"https://picsum.photos/seed/cat{i}/600/400"
            category.save()
            categories.append(category)

        self.stdout.write(self.style.NOTICE(f"Creating {num_products_per_category} products per category..."))
        created = 0
        for category in categories:
            for _ in range(num_products_per_category):
                name = f"{fake.color_name().capitalize()} {fake.word().capitalize()} {fake.random_number(digits=3)}"
                sku = fake.unique.bothify(text='SKU-####-???').upper()
                price = Decimal(random.randint(5, 500)) + Decimal(random.randint(0, 99)) / Decimal(100)
                description = fake.paragraph(nb_sentences=3)

                product = Product.objects.create(
                    name=name,
                    sku=sku,
                    category=category,
                    image_url=f"https://picsum.photos/seed/{sku}/600/400",
                    price=price,
                    stock=random.randint(0, 200),
                    description=description,
                    is_active=True,
                )
                created += 1
                # create a default variant per product
                variant = ProductVariant.objects.create(product=product, name="", is_active=True)
                # add images to the variant
                num_images = random.randint(1, 3)
                for j in range(num_images):
                    VariantImage.objects.create(
                        variant=variant,
                        image_url=f"https://picsum.photos/seed/{sku}-{j}/800/600",
                        alt_text=f"{product.name} image {j+1}",
                        sort_order=j,
                        is_main=(j == 0),
                    )

        # create curated related products for a subset
        self.stdout.write(self.style.NOTICE("Creating curated related products..."))
        all_products = list(Product.objects.filter(is_active=True))
        for p in all_products[: min(20, len(all_products))]:
            candidates = [c for c in all_products if c.category_id == p.category_id and c.id != p.id]
            random.shuffle(candidates)
            for order, rp in enumerate(candidates[:4]):
                RelatedProduct.objects.get_or_create(from_product=p, to_product=rp, defaults={"sort_order": order})

        # ensure a SiteConfig exists with one hero slide
        cfg = SiteConfig.get_solo()
        cfg.hero_title_1 = "Bienvenido a DepoAuto"
        cfg.hero_subtitle_1 = "Repuestos y accesorios de calidad"
        cfg.hero_image_1_url = "https://picsum.photos/seed/hero-seed/1600/600"
        cfg.save()

        self.stdout.write(self.style.SUCCESS(f"Seeding completed. Categories: {len(categories)}, Products: {created}"))

