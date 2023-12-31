from django.shortcuts import render, get_object_or_404, redirect
from .models import Product, ReviewRating
from category.models import *
from django.http import HttpResponse
from carts.models import *
from django.db.models import Q
from .forms import ReviewForm
from django.contrib import messages
from carts.views import _cart_id
from orders.models import OrderProduct


from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator

# Create your views here.


def store(request, category_slug=None):
    categories = None
    products = None
    if category_slug:
        categories = get_object_or_404(Category, slug=category_slug)
        products = Product.objects.filter(category=categories, is_available=True)
        paginator = Paginator(products, 6)
        page = request.GET.get('page')
        paged_products = paginator.get_page(page)
        product_count = products.count()
    else:
        products = Product.objects.filter(is_available=True).order_by('id')
        paginator = Paginator(products, 6)
        page = request.GET.get('page')
        paged_products = paginator.get_page(page)
        product_count = products.count()
    
    context ={
        'products': paged_products,
        'product_count': product_count
    }
    
    return render(request, 'store/store.html', context)


def product_detail(request, category_slug, product_slug):
    try:
        single_product = Product.objects.get(category__slug=category_slug, slug=product_slug)
        in_cart = CartItem.objects.filter(cart__cart_id=_cart_id(request), product=single_product).exists()
    except :
        return HttpResponse("No Product Found")

    try:
        order_product = OrderProduct.objects.filter(user = request.user, product= single_product).exists()
    except:
        print("ecpet")
        order_product = None
        
    reviews = ReviewRating.objects.filter(product = single_product)
    
        
    context={
        'single_product': single_product,
        'in_cart': in_cart,
        'order_product': order_product,
        'reviews': reviews
    }
    
    
    return render(request, 'store/product_detail.html', context)
    
    
def search(request):
    if 'keyword' in request.GET:
        keyword = request.GET.get('keyword')
        if keyword:
            products = Product.objects.order_by('-create_date').filter(Q(description__icontains=keyword) | Q(product_name__icontains=keyword))
            product_count = products.count()
    
    context={
        'products': products,
        'product_count': product_count
    }
    
    return render(request, 'store/store.html', context)
        

def submit_review(request, product_id):
    url = request.META.get('HTTP_REFERER')
    if request.method == 'POST':
        try:
            reviews = ReviewRating.objects.get(user__id=request.user.id, product__id=product_id)
            form = ReviewForm(request.POST, instance=reviews)
            form.save()
            messages.success(request,"Thank You! Your review has been updated.")
            return redirect(url)
        except ReviewRating.DoesNotExist:
            form = ReviewForm(request.POST)
            if form.is_valid():
                data = ReviewRating()
                data.subject = form.cleaned_data["subject"]
                data.review = form.cleaned_data["review"]
                data.rating = form.cleaned_data["rating"]
                data.ip = request.META.get('REMOTE_ADDR')
                data.product_id = product_id
                data.user_id = request.user.id
                data.save()
                messages.success(request, "Thank You! Your review has been submitted.")
                return redirect(url)
                
                