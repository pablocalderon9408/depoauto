from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from django.core.paginator import Paginator
from django.core.mail import send_mail, BadHeaderError
from django.contrib import messages
from django.conf import settings
from .models import Category, Product, RelatedProduct


def index(request):
    top_categories = Category.objects.filter(is_active=True).order_by('name')[:6]
    featured_products = Product.objects.filter(is_active=True).order_by('-created_at')[:8]
    context = {
        'top_categories': top_categories,
        'featured_products': featured_products,
    }
    return render(request, 'index.html', context)


def product_list(request, category_slug=None):
    categories = Category.objects.filter(is_active=True).order_by('name')
    products = Product.objects.filter(is_active=True)

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

    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)

    products = products.order_by('name')

    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'categories': categories,
        'page_obj': page_obj,
        'selected_category': selected_category,
        'query': query or '',
        'min_price': min_price or '',
        'max_price': max_price or '',
    }
    return render(request, 'products/product_list.html', context)


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    curated_ids = RelatedProduct.objects.filter(from_product=product).order_by('sort_order').values_list('to_product_id', flat=True)
    curated = Product.objects.filter(id__in=list(curated_ids), is_active=True)
    fallback = Product.objects.filter(is_active=True, category=product.category).exclude(id__in=[product.id, *curated_ids])[: max(0, 8 - curated.count())]
    related_products = list(curated) + list(fallback)
    context = {
        'product': product,
        'related_products': related_products,
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
        try:
            send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [settings.CONTACT_EMAIL])
            messages.success(request, 'Your message has been sent. We will contact you soon.')
        except BadHeaderError:
            messages.error(request, 'Invalid header found.')
        except Exception:
            messages.error(request, 'There was an error sending your message. Please try again later.')
        return redirect('contact')
    return render(request, 'pages/contact.html')

# Create your views here.
