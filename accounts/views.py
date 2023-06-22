from django.shortcuts import render, redirect
from .forms import *
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

#Verification Email
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage
# Create your views here.


def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            phone_number = form.cleaned_data['phone']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            username = email.split('@')[0]
            
            user = Account.objects.create_user(username=username, email=email, password=password, first_name=first_name, last_name=last_name)
            user.phone = phone_number
            user.save()
            
            #User Activation
            
            current_site = get_current_site(request)
            mail_subject = "Please activate your account"
            data ={'user': user, 
                   'domain': current_site,
                   'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                   'token': default_token_generator.make_token(user)
                }
            message = render_to_string('accounts/account_verification_email.html', data)
            to_email = email
            send_mail = EmailMessage(mail_subject, message, to=[to_email])
            send_mail.send()
            
            
            
            # messages.success(request,"Registration Successful")
            return redirect('/accounts/login/?command=verification&email=' + email)
    
    else:
        form = RegistrationForm()
    context ={
        'form': form
    }
    return render(request, 'accounts/register.html', context)

def loginUser(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        user = authenticate(email=email, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, "You are now logged in.")
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid login credentials")
            return redirect('login')
        
    return render(request, 'accounts/login.html')



@login_required(login_url="login")
def logoutUser(request):
    logout(request)
    messages.success(request, "You are logged out.")
    return redirect('login')



def activate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user=None
    
    if user is not None and default_token_generator.check_token(user, token):
        user.is_active=True
        user.save()
        messages.success(request, "Congratulations, Your account is activated!!")
        return redirect('login')
    else:
        messages.error(request, "Invlaid activation link")
        return redirect('register')
        
    
    return HttpResponse("Ok")



@login_required(login_url="login")
def dashboard(request):
    return render(request, 'accounts/dashboard.html')



def forgotPassword(request):
    
    if request.method == 'POST':
        email = request.POST.get('email')
        if Account.objects.filter(email=email).exists():
            user = Account.objects.get(email__iexact=email)
            
            #Password Reset email
            
            current_site = get_current_site(request)
            mail_subject = "Please activate your account"
            data ={'user': user, 
                   'domain': current_site,
                   'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                   'token': default_token_generator.make_token(user)
                }
            message = render_to_string('accounts/reset_password_email.html', data)
            to_email = email
            send_mail = EmailMessage(mail_subject, message, to=[to_email])
            send_mail.send()
            
            messages.success(request, "Password rest email has been sent to your email address")
            return redirect('login')
        
        else:
            messages.error(request, 'Account does not exist')
            return redirect('forgotPassword')
        
    return render(request, 'accounts/forgotPassword.html', )
            
            
            
            
            
            
        
    return render(request, 'accounts/forgotPassword.html')
    
    
    
def resetpassword_validate(request, uidb64, token):
    
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user=None
    
    if user is not None and default_token_generator.check_token(user, token):
        request.session['uid'] = uid
        messages.success(request, "Please reset your password")
        return redirect('resetPassword')
    else:
        messages.error(request, "The link has been expired")
        return redirect('login')
        
        
    
    return HttpResponse("Hello")


def resetPassword(request):
    if request.method == 'POST':
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        if password == confirm_password:
            uid = request.session.get('uid')
            user = Account.objects.get(pk=uid)
            user.set_password(password)
            user.save()
            messages.success(request, "Password reset successfully")
            return redirect('login')
        else:
            messages.error(request, "Password does not match")
            return redirect('resetPassword')
            
    
    return render(request, 'accounts/resetPassword.html')