from .models import SiteConfig


def site_config(request):
    """Inyecta site_config en todas las plantillas."""
    return {'site_config': SiteConfig.get_solo()}
