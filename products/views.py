from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from django.core.paginator import Paginator
from django.core.mail import send_mail, BadHeaderError
from django.contrib import messages
from django.conf import settings
from .models import Category, Product, RelatedProduct, SiteConfig, HeroSlide


def index(request):
    site_config = SiteConfig.get_solo()
    top_limit = site_config.home_top_categories_limit if site_config else 6
    new_limit = site_config.home_new_arrivals_limit if site_config else 8
    top_categories = Category.objects.filter(is_active=True).order_by('name')[: top_limit]
    featured_products = Product.objects.filter(is_active=True).order_by('-created_at')[: new_limit]
    # Slides dinámicos: usa HeroSlide activos si existen; si no, usa SiteConfig.hero_slides
    hero_slides = HeroSlide.objects.filter(is_active=True).order_by('sort_order', 'id')

    show_top_categories = site_config.show_top_categories if site_config else True
    show_new_arrivals = site_config.show_new_arrivals if site_config else True
    
    context = {
        'show_top_categories': show_top_categories,
        'show_new_arrivals': show_new_arrivals,
        'top_categories': top_categories,
        'featured_products': featured_products,
        'site_config': site_config,
        'hero_slides': hero_slides,
    }
    return render(request, 'index.html', context)


def product_list(request, category_slug=None):
    categories = Category.objects.filter(is_active=True).order_by('name')
    products = Product.objects.filter(is_active=True).order_by('name')

    selected_category = None
    if category_slug:
        selected_category = Category.objects.filter(slug=category_slug, is_active=True).first()
        if selected_category:
            products = products.filter(category=selected_category)

    query = request.GET.get('q')
    if query:
        products = products.filter(
            Q(name__icontains=query) | Q(description__icontains=query) | Q(sku__icontains=query)
        )

    # Precio no se usa en este proyecto; se remueven filtros de precio

    products = products.order_by('name')

    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'categories': categories,
        'page_obj': page_obj,
        'selected_category': selected_category,
        'query': query or '',
    }
    return render(request, 'products/product_list.html', context)


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    curated_ids = RelatedProduct.objects.filter(from_product=product).order_by('sort_order').values_list('to_product_id', flat=True)
    curated = Product.objects.filter(id__in=list(curated_ids), is_active=True)
    fallback = Product.objects.filter(is_active=True, category=product.category).exclude(id__in=[product.id, *curated_ids])[: max(0, 8 - curated.count())]
    related_products = list(curated) + list(fallback)
    site_config = SiteConfig.get_solo()
    context = {
        'product': product,
        'related_products': related_products,
        'site_config': site_config,
    }
    return render(request, 'products/product_detail.html', context)


def about(request):
    return render(request, 'pages/about.html')


def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        message = request.POST.get('message', '').strip()
        if not name or not email or not message:
            messages.error(request, 'Please fill in all fields.')
            return redirect('contact')
        subject = f"Contact form - {name}"
        body = f"From: {name} <{email}>\n\n{message}"

        cfg = SiteConfig.get_solo()
        recipient = (cfg.contact_email or '').strip() or settings.CONTACT_EMAIL
        auth_user = (cfg.email_smtp_user or '').strip() or settings.EMAIL_HOST_USER
        auth_password = (cfg.email_smtp_password or '').strip() or settings.EMAIL_HOST_PASSWORD
        from_email = auth_user or settings.DEFAULT_FROM_EMAIL

        try:
            send_mail(
                subject,
                body,
                from_email,
                [recipient],
                auth_user=auth_user or None,
                auth_password=auth_password or None,
            )
            messages.success(request, 'Your message has been sent. We will contact you soon.')
        except BadHeaderError:
            messages.error(request, 'Invalid header found.')
        except Exception:
            messages.error(request, 'There was an error sending your message. Please try again later.')
        return redirect('contact')
    return render(request, 'pages/contact.html')

# Create your views here.
