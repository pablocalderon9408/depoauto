"""
URL configuration for depoauto project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from products import views as product_views

urlpatterns = [
    # Rutas admin custom deben ir ANTES de admin.site.urls para evitar
    # que el catch_all_view de Django admin las intercepte.
    path('admin/products/reorder/', product_views.product_reorder, name='product_reorder'),
    path('admin/products/reorder/save/', product_views.product_reorder_save, name='product_reorder_save'),
    path('admin/', admin.site.urls),
    path('', include('products.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
