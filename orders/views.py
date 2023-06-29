from django.shortcuts import render, redirect
from carts.models import CartItem
from .models import Order, Payment, OrderProduct
from .forms import OrderForm
import datetime
import json
from store.models import Product
from django.template.loader import render_to_string 
from django.core.mail import EmailMessage
from django.http import JsonResponse

# Create your views here.


def place_order(request, total=0, quantity=0):
    current_user = request.user
    
    #if the cart is less than or equal to 0 then redirect back to shop
    cart_items = CartItem.objects.filter(user=current_user)
    cart_count = cart_items.count()
    if cart_count<=0:
        return redirect('store')
    
    grand_total =0
    tax=0
    for cart_item in cart_items:
        quantity+=cart_item.quantity
        total+= cart_item.product.price*cart_item.quantity
    
    tax = total*0.02
    grand_total = total+tax
    
    
    
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            
            # Store all the billing information to the Order's table
            data =Order()
            data.user=request.user
            data.first_name = form.cleaned_data['first_name']
            data.last_name = form.cleaned_data['last_name']
            data.phone = form.cleaned_data['phone']
            data.email = form.cleaned_data['email']
            data.address_line_1 = form.cleaned_data['address_line_1']
            data.address_line_2 = form.cleaned_data['address_line_2']
            data.country = form.cleaned_data['country']
            data.state = form.cleaned_data['state']
            data.city = form.cleaned_data['city']
            data.order_note = form.cleaned_data['order_note']
            data.order_total = grand_total
            data.tax = tax
            data.ip = request.META.get('REMOTE_ADDR')
            data.save()
            
            print(f"*************{data}")
            # Generate Order No.
            
            yr = int(datetime.date.today().strftime('%Y'))
            dt = int(datetime.date.today().strftime('%d'))
            mt = int(datetime.date.today().strftime('%m'))
            
            d = datetime.date(yr, mt,dt)
            current_date = d.strftime('%Y%m%d')
            
            order_number = current_date + str(data.id)
            
            data.order_number = order_number
            data.save()
            
            order = Order.objects.get(user=current_user, is_ordered=False, order_number=order_number)
            context ={
                'order': order,
                'cart_items': cart_items,
                'total': total,
                'tax': tax,
                'grand_total': grand_total
            }
            
            return render(request, 'order/payments.html', context)
    
    return redirect('checkout')
            
            
def payments(request):
    
    body = json.loads(request.body)
    print(body)
    
    order = Order.objects.get(user=request.user, is_ordered=False, order_number = body['orderID'])
    print(f"order_False*****{order}")
    
    # Store transaction details inside Payment model
    payment = Payment(
        user = request.user,
        payment_id = body['transID'],
        payment_method = body['payment_method'],
        amount_paid = order.order_total,
        status=body['status'],
    )
    payment.save()
    order.payment = payment
    order.is_ordered= True
    order.save()
    print(f"payment*****{payment}")
    print(f"order_True*****{order}")
    # Move the cart items to Order Product Table
    
    cart_items = CartItem.objects.filter(user=request.user)
    
    print(f"cart_Items*******{cart_items}")
        
    for item in cart_items:
        order_product = OrderProduct()
        order_product.order_id = order.id
        order_product.payment = payment
        order_product.user_id = request.user.id
        order_product.product_id = item.product_id
        order_product.quantity = item.quantity
        order_product.product_price = item.product.price
        order_product.ordered = True
        order_product.save()
        print(f"order_Product*******{order_product}")
        
        cart_item = CartItem.objects.get(id = item.id)
        product_variation = cart_item.variations.all()
        order_product = OrderProduct.objects.get(id = order_product.id)
        order_product.variations.set(product_variation)
        order_product.save()
    
    # Reduce the quqntity of the sold products
    
        product = Product.objects.get(id = item.product_id)
        product.stock -= item.quantity
        product.save()
        
    # Clear cart
    
    CartItem.objects.filter(user= request.user).delete()
        
        

    #Send order received email to customer
    
    mail_subject = "Thank you for your order"
    data = {'user': request.user, 
            'order': order
        }
    message = render_to_string('order/order_received_email.html', data)
    to_email = request.user.email
    send_mail = EmailMessage(mail_subject, message, to=[to_email])
    send_mail.send()


    # Send order number and transaction id back to sendData method via JsonResponse
    
    data ={
        'order_number': order.order_number,
        'payment_id': payment.payment_id,
    }
    
    
    return JsonResponse(data)
    
    
        
        
    

            

            
            
            
            
def order_complete(request):
    
    order_number = request.GET.get('order_number')
    payment_id = request.GET.get("payment_id")
    
    try:
        order = Order.objects.get(order_number=order_number,is_ordered=True)
        ordered_products = OrderProduct.objects.filter(order_id=order.id)
        payment = Payment.objects.get(payment_id=payment_id)
        
        subtotal =0
        for i in ordered_products:
            subtotal += i.product_price*i.quantity
        
        context ={
            'order': order,
            'ordered_products': ordered_products,
            'payment': payment,
            'subtotal': subtotal
        }
        
        return render(request, 'order/order_complete.html', context)
        
    except (Order.DoesNotExist, Payment.DoesNotExist):
        return redirect('home')
    
    return render(request, 'order/order_complete.html')
    