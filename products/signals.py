from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import RelatedProduct


@receiver(post_save, sender=RelatedProduct)
def ensure_bidirectional_related(sender, instance: RelatedProduct, created: bool, **kwargs):
    if not created:
        return
    # Create the reverse relation if it doesn't exist
    reverse, created_rev = RelatedProduct.objects.get_or_create(
        from_product=instance.to_product,
        to_product=instance.from_product,
        defaults={"sort_order": instance.sort_order},
    )
    if not created_rev:
        # Optionally sync sort order
        if reverse.sort_order != instance.sort_order:
            reverse.sort_order = instance.sort_order
            reverse.save(update_fields=["sort_order"])


@receiver(post_delete, sender=RelatedProduct)
def delete_reverse_related(sender, instance: RelatedProduct, **kwargs):
    RelatedProduct.objects.filter(
        from_product=instance.to_product,
        to_product=instance.from_product,
    ).delete()

