from django.shortcuts import render,redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as log , logout as authlogout
from django.contrib import messages
from Sko_Adminside.forms import AddressForm
from django.core.exceptions import ValidationError
from .utils import generate_otp,send_otp,clean_email,clean_password ,validate_image , validate_data, validate_phone
from datetime import datetime, timedelta
from Sko_Adminside.models import Product , Variants, VarientImage,userprofile,Address,Cart,CartItem,PaymentMethod,Order,OrderItem,Wishlist,Wallet,Transaction
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404
import re
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.contrib.auth import update_session_auth_hash
import json     
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
# from .utils import refund_to_wallet
from Sko_Adminside.models import Coupon
from django.db.models import F
from django.core.serializers import serialize  
import razorpay
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt  
from io import BytesIO
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
  






def  user_sign(request):
    if request.user.is_authenticated:  
        return redirect('home')
    if request.POST:
        username=request.POST['username']
        sign_password=request.POST['password1']
        sign_confirm_password=request.POST['password2']
        email=request.POST['email']
        
        allowed_username_regex = r'^[A-Za-z][A-Za-z]{3,}$'  
        if not re.match(allowed_username_regex, username):
            messages.error(request, "Username must start with a letter and must be at least 4 letters long (letters only).")
            return render(request, 'sigin.html', {'username': username, 'email': email})

        
        elif User.objects.filter(username=username).exists():
            messages.error(request, f"User name '{username}' is already taken")
            return render(request, 'sigin.html', {'username': username, 'email': email})
        elif User.objects.filter(email=email).exists():
            messages.error(request, f"Mail Id '{email}' already has an account")
            return render(request, 'sigin.html', {'username': username, 'email': email})
        elif sign_password!=sign_confirm_password:
            messages.error(request,'password do not match ')
            return render(request, 'sigin.html', {'username': username, 'email': email})
            
        else:
            if not username:
                messages.error(request, "Enter the username")
                return render(request, 'sigin.html', {'username': username, 'email': email})
                   
            elif not email:
                messages.error(request, "Enter the email")
                return render(request, 'sigin.html', {'username': username, 'email': email})
                
            elif not sign_password:
                messages.error(request, "Enter the password")
                return render(request, 'sigin.html', {'username': username, 'email': email})
                
            elif not sign_confirm_password:
                messages.error(request, "Enter the confromation Password")
                return render(request, 'sigin.html', {'username': username, 'email': email})
            else:
                try:
                    clean_email(email)
                    clean_password(sign_password)
                except ValidationError as e:
                   return render(request, 'sigin.html', {'username': username, 'email': email})
                else:
                    request.session['username']=username
                    request.session['email']=email
                    request.session['password']=sign_password
                    
                    otp=generate_otp()
                    send_otp(email,otp)
                    request.session['otp']=otp
                    request.session['otp_creation_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    return redirect('otp')
    
    
    return render(request , 'sigin.html')
                    
              
        
        
    
def otp(request):
    username = request.session.get('username')
    print(username)
    email = request.session.get('email')
    password = request.session.get('password')
    otp_creation_time_str = request.session.get('otp_creation_time')
    session_otp = request.session.get('otp')
    print('session',session_otp)
     
    

    if not all([username, email, password, otp_creation_time_str, session_otp]):

         messages.error(request, "Session expired or missing information. Please sign up again.")
         return redirect('user_sign')
     
    otp_creation_time=datetime.strptime(otp_creation_time_str,'%Y-%m-%d %H:%M:%S')
    expiry_time=otp_creation_time+timedelta(minutes=1)
    
    
    if datetime.now() > expiry_time:
        messages.error(request, "OTP has expired. Please request a new one.")
        return render(request, 'otp.html', {'expiry_time': expiry_time.strftime('%Y-%m-%d %H:%M:%S')})
    
    
 
    if request.POST:
        otp_digits=[request.POST['otp1'],
                    request.POST['otp2'],
                    request.POST['otp3'],
                    request.POST['otp4'],
                    request.POST['otp5']]
        
        otp=''.join(otp_digits)
        print('otp',otp)
       
        
        if otp==session_otp:
            user=User.objects.create_user(username=username,password=password,email=email)
            user.save()
            return redirect('user_login')
        else:
            messages.error(request,'invalid otp')
            return redirect('otp')
            
        
    return render(request,'otp.html',{'expiry_time': expiry_time.strftime('%Y-%m-%d %H:%M:%S')})

def resend_otp(request):
    if request.method == 'POST':
        email = request.session.get('email')

        new_otp = generate_otp()  # Generate new OTP
        request.session['otp'] = new_otp
        otp_creation_time = datetime.now()
        request.session['otp_creation_time'] = otp_creation_time.strftime('%Y-%m-%d %H:%M:%S')

        send_otp(email, new_otp)  # Send the new OTP

        # Calculate new expiry time (1 minute from now)
        expiry_time = otp_creation_time + timedelta(minutes=1)
        request.session['otp_expiry_time'] = expiry_time.strftime('%Y-%m-%d %H:%M:%S')  # Store in session

        messages.success(request, "A new OTP has been sent to your email.")  # Optional: success message

        return redirect('otp')  # Redirect back to the OTP page

    messages.error(request, 'Invalid request')  # Optional: error message
    return redirect('otp')  # Redirect back to the OTP page




def user_login(request):
    if request.user.is_authenticated:  
        return redirect('home')
    
    if request.method == 'POST':
        log_email_or_username = request.POST.get('email')
        log_password = request.POST.get('password')

        print(f"Request Method: {request.method}")
        print(f"Email/Username: {log_email_or_username}")
        print(f"Password: {log_password}")

        try:
            print("Checking email or username...")
            try:
                user = User.objects.get(email=log_email_or_username)
                print("User found by email.")
            except User.DoesNotExist:
                user = User.objects.get(username=log_email_or_username)
                print("User found by username.")

            # Check if the user is active before authenticating
            if not user.is_active:
                messages.error(request, "Your account has been blocked. Please contact support for assistance.")
                return render(request, 'login.html',  {'login_input': log_email_or_username})
            # Authenticate the user only if active
            authenticated_user = authenticate(request, username=user.username, password=log_password)

            if authenticated_user is not None:
                log(request, authenticated_user)
                messages.success(request, "You have successfully logged in!")
                return redirect('home')
            else:
                messages.error(request, "Incorrect password. Please try again.")
                return render(request, 'login.html',  {'login_input': log_email_or_username})

        except User.DoesNotExist:
            messages.error(request, "User not found.")
            return render(request, 'login.html',  {'login_input': log_email_or_username})
        except Exception as e:
            messages.error(request, str(e))
            return render(request, 'login.html',  {'login_input': log_email_or_username})

    return render(request, 'login.html')



def forget_pass_send_otp(request):
    if request.method == 'POST':
        print("Request POST data:", request.POST)
        email = request.POST.get('email')
        
        print(f"Captured email: {email}")  # Debugging line
        if not email:
            messages.error(request, "Email is required.")
            return render(request, 'forget_pass.html')

        pass_otp = generate_otp() 
        request.session['otp'] = pass_otp
        otp_creation_time = datetime.now()
        request.session['email'] = email
        request.session['otp_creation_time'] = otp_creation_time.strftime('%Y-%m-%d %H:%M:%S')
        
        try:
            clean_email(email)
            send_otp(email, pass_otp)  # Handle exceptions inside send_otp if necessary
            print('passotp:', pass_otp)
            messages.success(request, 'OTP sent to your email.')
        except Exception as e:
            messages.error(request, f'Failed to send OTP: {str(e)}')
        
        return redirect('otp_pass_validation')  # Redirect to OTP verification page
    
    return render(request, 'forget_pass.html')

           
    
    
  

def otp_pass_validation(request):
   
    email = request.session.get('email')
    password = request.session.get('password')
    otp_creation_time_str = request.session.get('otp_creation_time')
    session_otp = request.session.get('otp')
    print('session',session_otp)
     
    
    print('Session Variables:')
    print('Email:', email)
    print('Password:', password)
    print('OTP Creation Time:', otp_creation_time_str)
    print('Session OTP:', session_otp)
    

    if not all([ email,  otp_creation_time_str, session_otp]):

         messages.error(request, "Session expired or missing information. Please sign up again.")
         return redirect('user_sign')
     
    otp_creation_time=datetime.strptime(otp_creation_time_str,'%Y-%m-%d %H:%M:%S')
    expiry_time=otp_creation_time+timedelta(minutes=1)
    
    if datetime.now() > expiry_time:
        messages.error(request, "OTP has expired. Please request a new one.")
        return redirect('forget_pass_send_otp')
    
 
    if request.POST:
        otp_digits=[request.POST['otp1'],
                    request.POST['otp2'],
                    request.POST['otp3'],
                    request.POST['otp4'],
                    request.POST['otp5']]
        
        otp=''.join(otp_digits)
        print('otp',otp)
       
        
        if otp==session_otp:
          
            return redirect('reset_password')
        else:
            messages.error(request,'invalid otp')
            return redirect('forget_pass_otp.html')
            
        
    
    return render(request,'forget_pass_otp.html',{'expiry_time': expiry_time.strftime('%Y-%m-%d %H:%M:%S')})


def reset_password(request):
    if request.POST:
        email= request.session.get('email')
        new_password=request.POST.get('password1')
        print(new_password)
        confirm_password=request.POST.get('password2')
        print(confirm_password)
        if not email:
            messages.error(request, "Session expired or email not found. Please try again.")
            return redirect('forget_pass_send_otp') 
        
        # Check if passwords are provided and match
        if not new_password or not confirm_password:
            messages.warning(request, 'Password fields cannot be empty.')
            return redirect('reset_password')
        
        if new_password != confirm_password:
            messages.warning(request, 'Passwords do not match.')
            return redirect('reset_password')
        
        try:
            clean_password(new_password)
            if new_password and confirm_password and new_password == confirm_password:
                user=User.objects.get(email=email)
                user.set_password(new_password)
                user.save()
                messages.success(request, 'password successfully changed.')
                return redirect(user_login)
                
            else:
                messages.warning(request, 'Passwords do not match or are empty.')
        
        except ValidationError as e:
            messages.error(request, e.messages)  
                
    return render(request,'reset_password.html')
    

@never_cache
@login_required(login_url='user_login')
def home(request):
    if request.user.is_authenticated:
        print(f"Authenticated user: {request.user}")
    else:
        print("User is not authenticated")
        return redirect('user_login')
 
    return render(request,'home.html')
 


    

 
def user_logout(request):
     if request.user.is_authenticated:
        print("User is authenticated.")
        authlogout(request)  # Log out the user
        messages.success(request, "You have been logged out successfully.")
        return redirect('user_login')
     else:
        print("User is  not authenticated.")
        messages.warning(request, "You were not logged in.")
        
        
     return redirect('user_login')  # Redirect to the login page


from django.db.models import Q, Count ,Min, Max



@login_required(login_url='user_login')
def productlist(request):
    if request.user.is_authenticated:
      
        sort_option = request.GET.get('sort', 'min_price')
        


        product_list = Product.objects.filter(
            is_active=True,
            is_delete=False,
            category__is_delete=False,
            variants__is_delete=False
        ).prefetch_related('variants').annotate(
            active_variants_count=Count('variants', filter=Q(variants__is_delete=False)),
            min_price=Min('variants__price'),
            max_price=Max('variants__price')
        ).filter(active_variants_count__gt=0)

        if sort_option == 'min_price':
            product_list = product_list.order_by('min_price')
        elif sort_option == 'max_price':
            product_list = product_list.order_by('-max_price')
        elif sort_option == 'featured':
            product_list = product_list.order_by('-active_variants_count') 
        elif sort_option == 'new-arrivals':
            product_list = product_list.order_by('-id')  
        elif sort_option == 'a-to-z':
            product_list = product_list.order_by('name')  
        elif sort_option == 'z-to-a':
            product_list = product_list.order_by('-name') 

        # Paginate the sorted product list
        paginator = Paginator(product_list, 8)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        for product in page_obj:
            product.product_in_wishlist = Wishlist.objects.filter(user=request.user, varients__product=product).exists()


        return render(request, 'product_list.html', {'page_obj': page_obj, 'sort_option': sort_option,})
    else:
        messages.warning(request, "You were not logged in.")
        return redirect('user_login')
    
    


    


@login_required(login_url='user_login')
def product_search(request):
    if request.user.is_authenticated:
        search_query = request.GET.get('q', '')  
        
        product_list = Product.objects.filter(
            Q(name__icontains=search_query),  
            is_active=True,  
            is_delete=False,  
            category__is_delete=False,  
            variants__is_delete=False  
        ).prefetch_related('variants').annotate(
            active_variants_count=Count('variants', filter=Q(variants__is_delete=False))
        ).filter(active_variants_count__gt=0)

        # Return the search results to the template without pagination
        return render(request, 'product_search.html', {'product_list': product_list, 'search_query': search_query}) 
    else:
        messages.warning(request, "You were not logged in.")
        return redirect('user_login')
  
    
    
@login_required(login_url='user_login')
def product_view(request, pk):
    if request.user.is_authenticated:  
   
        try:
            product = Product.objects.get(id=pk, is_delete=False)
        except Product.DoesNotExist:
            messages.error(request, "This product is no longer available.")
            return redirect('home')
            print("Product: ", product.pk)

    
        variants = product.variants.filter(is_delete=False).prefetch_related('images')
        default_variant = variants.first() if variants.exists() else None
        
        
        related_products = Product.objects.filter(
            category=product.category, 
            is_delete=False,
            category__is_delete=False,
            variants__is_delete=False
        ).distinct().exclude(id=product.id)[:4]
        
        product_in_wishlist = Wishlist.objects.filter(user=request.user, varients__product=product).exists()

        
        context = {
            'product': product, 
            'variants': variants,
            'related_product':related_products,
            'default_variant': default_variant,
            'product_in_wishlist': product_in_wishlist,
           
            
        }

        return render(request, 'product_view.html', context)
    
    else:
        print("User is authenticated3.")
        messages.warning(request, "You were not logged in.")
    return redirect('user_login')

@login_required(login_url='user_login')
def get_variant_details(request, variant_id):
   
    variant = get_object_or_404(Variants, id=variant_id, is_delete=False)
    
   
    original_price = variant.price
    discounted_price = variant.get_discounted_price() if hasattr(variant, 'get_discounted_price') else original_price

   
    data = {
        'original_price': str(original_price),
        'discounted_price': str(discounted_price),
        'stock': variant.stock,
    }
    
    
    return JsonResponse(data)



def category_view(request, category_name):
    
    if request.user.is_authenticated:
        if not request.user.is_active:
            messages.error(request, "Your account is inactive. Please contact support.")
            return redirect('user_login')  
    else:
        return redirect('user_login')
    
    
    sort_option = request.GET.get('sort', 'price-low-to-high')  # Default sort option

    # Filtering products
    product_list = Product.objects.filter(
        category__name=category_name,
        is_active=True,
        is_delete=False,
        category__is_delete=False,
        variants__is_delete=False
    ).distinct().prefetch_related('variants').annotate(
        active_variants_count=Count('variants', filter=Q(variants__is_delete=False)),
        min_price=Min('variants__price'),
        max_price=Max('variants__price')
    ).filter(active_variants_count__gt=0)

    # Sorting logic
    if sort_option == 'price-low-to-high':
        product_list = product_list.order_by('min_price')
    elif sort_option == 'price-high-to-low':
        product_list = product_list.order_by('-max_price')
    elif sort_option == 'featured':
        product_list = product_list.order_by('-active_variants_count')
    elif sort_option == 'new-arrivals':
        product_list = product_list.order_by('-id')
    elif sort_option == 'a-to-z':
        product_list = product_list.order_by('name')
    elif sort_option == 'z-to-a':
        product_list = product_list.order_by('-name')

    paginator = Paginator(product_list, 8)  # 8 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Context for the template
    context = {
        'page_obj': page_obj,
        'sort_option': sort_option,
        'category_name': category_name,
    }

    return render(request, 'categoryview.html', context)

    
    

def Userprofile(request):
    
    if request.user.is_authenticated:
        if not request.user.is_active:
            messages.error(request, "Your account is inactive. Please contact support.")
            return redirect('user_login')  
    else:
        return redirect('user_login')
    
    user=request.user
    user_profile, created = userprofile.objects.get_or_create(user=user)
    
    return render(request, 'userprofile.html', {'user': user, 'profile': user_profile})


def editprofile(request):
    if request.user.is_authenticated:
        if not request.user.is_active:
            messages.error(request, "Your account is inactive. Please contact support.")
            return redirect('user_login')  
    else:
        return redirect('user_login')
    
    user = request.user
    user_data = User.objects.get(id=user.id)
    user_profile, created = userprofile.objects.get_or_create(user=user)  # Ensure user profile exists

    if request.method == 'POST':
        current_email = user_data.email
        submitted_email = request.POST.get('email')
        
    
        if submitted_email != current_email:
            messages.error(request, "You cannot change your email address.")
            return redirect('Userprofile')
        
        
        try:
            user_data.first_name = validate_data(request.POST.get('firstname'))
            user_data.last_name = validate_data(request.POST.get('lastname'))
            user_profile.mobile = validate_phone(request.POST.get('phone'))
            user_profile.bio = validate_data(request.POST.get('bio'))

            
            if 'profile_picture' in request.FILES:
                uploaded_file = request.FILES['profile_picture']
                validate_image(uploaded_file)  # Validate the image file
                user_profile.profile_picture = uploaded_file  # Save the uploaded file
            
            
            user_data.save()
            user_profile.save()
            
           
            messages.success(request, "Profile updated successfully.")
            return redirect('Userprofile')
        
        except ValidationError as e:
            
            messages.error(request, e.message)
            return redirect('Userprofile')

    return render(request, 'userprofile.html', {'user': user_data, 'profile': user_profile , 
        'entered_first_name': request.POST.get('firstname', user_data.first_name),
        'entered_last_name': request.POST.get('lastname', user_data.last_name),
        'entered_phone': request.POST.get('phone', user_profile.mobile),
        'entered_bio': request.POST.get('bio', user_profile.bio)})


def address(request):
    if request.user.is_authenticated:
        if not request.user.is_active:
            messages.error(request, "Your account is inactive. Please contact support.")
            return redirect('user_login')  
    else:
        return redirect('user_login')
    
    print('ho')
    address = Address.objects.filter(is_delete=False,user=request.user)
    user_profile = get_object_or_404(userprofile, user=request.user)  
    print('hi')
    
    return render(request, 'addaddress.html', {'data': address, 'profile': user_profile})

def add_address(request):
    
    if request.user.is_authenticated:
        if not request.user.is_active:
            messages.error(request, "Your account is inactive. Please contact support.")
            return redirect('user_login')  
    else:
        return redirect('user_login')
    
    if request.method == "POST":
        
        address_form=AddressForm(request.POST)
        
        
        
        
        if address_form.is_valid():
            address = address_form.save(commit=False)  # Create the instance without saving
            address.user = request.user  # Set the user field
            address.save()  
            
            next_page = request.POST.get('next')
            if next_page == 'checkout':
                return redirect('checkout')  # Replace with your actual checkout URL name
            else:
                return redirect('address') 
        
    else:
            address_form=AddressForm()
            print(address_form.errors)
            
    return render (request,"add.html",{'form': address_form})

def edit_address(request,pk):
    
    if request.user.is_authenticated:
        if not request.user.is_active:
            messages.error(request, "Your account is inactive. Please contact support.")
            return redirect('user_login')  
    else:
        return redirect('user_login')
    
    address_id=get_object_or_404(Address,pk=pk)
    
    if request.method == "POST":
        form = AddressForm(request.POST, instance=address_id)
        if form.is_valid():
            form.save()
            return redirect('address') 
    else:   
        form = AddressForm(instance=address_id)
    return render (request,'edit_address.html',{'form':form})


def delete_address(request, pk):
    
    if request.user.is_authenticated:
        if not request.user.is_active:
            messages.error(request, "Your account is inactive. Please contact support.")
            return redirect('user_login')  
    else:
        return redirect('user_login')
    
    address = get_object_or_404(Address, pk=pk)
    
    
    address.is_delete = True
    address.save()
    
   
    return redirect('address') 


def change_password(request):
    
    if request.user.is_authenticated:
        if not request.user.is_active:
            messages.error(request, "Your account is inactive. Please contact support.")
            return redirect('user_login')  
    else:
        return redirect('user_login')
    
    if request.POST:
        old_password=request.POST.get('oldpass')  
        new_password=request.POST.get('new_password')
        confirm_password=request.POST.get('confirm_password') 
        
        if new_password!=confirm_password:
            messages.error(request, "New password and confirm password do not match.")
            return redirect('Userprofile') 
        
        user = request.user
        if not user.check_password(old_password):
            messages.error(request, "The old password is incorrect.")
            return redirect('Userprofile')
        
         
        if old_password == new_password:
            messages.error(request, "New password cannot be the same as the old password.")
            return redirect('Userprofile')
        
        try:
            clean_password(new_password)
        except ValidationError as e:
            messages.error(request, e.message)  
            return redirect('Userprofile')

        user.set_password(new_password)
        user.save()

        
        update_session_auth_hash(request, user)

        messages.success(request, "Password changed successfully.")
        return redirect('Userprofile')  

    return render(request, 'userprofile.html')


def add_to_cart(request):
    
    if request.user.is_authenticated:
        if not request.user.is_active:
            messages.error(request, "Your account is inactive. Please contact support.")
            return redirect('user_login')  
    else:
        return redirect('user_login')
    
    if request.method == 'POST':
        variant_id = request.POST.get('variant_id')
        print(variant_id)
        variant = get_object_or_404(Variants, id=variant_id, is_delete=False)
        quantity = int(request.POST.get('quantity', 1))
        print(quantity)
        product_id = variant.product.id
        
        
        if quantity < 1:
            messages.error(request, "Quantity must be at least 1.")
            return redirect('product_view', pk=product_id)
        
        if quantity > 4:
            messages.error(request, "Cannot purchase more than 4 items at a time.")
            return redirect('product_view', pk=product_id)

        if quantity > variant.stock:
            messages.error(request, "Not enough stock available.")
            return redirect('product_view', pk=product_id)

        cart, created = Cart.objects.get_or_create(user=request.user, is_active=True)
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            variant=variant,
            defaults={'quantity': quantity}
        )

        if not created:
            new_quantity = cart_item.quantity + quantity
            if new_quantity > variant.stock:
                messages.error(request, "Not enough stock available for the requested quantity.")
                return redirect('product_view', pk=product_id)
            
            elif new_quantity > 4:
                messages.error(request, "Cannot purchase more than 4 items at a time.")
                return redirect('product_view', pk=product_id)
            
            cart_item.quantity = new_quantity
            cart_item.save()

        messages.success(request, "Item added to cart.")
        return redirect('cart_view')
    
    return redirect('product_list')


def delete_cart(request, pk):
    
    if request.user.is_authenticated:
        if not request.user.is_active:
            messages.error(request, "Your account is inactive. Please contact support.")
            return redirect('user_login')  
    else:
        return redirect('user_login')
    
    try:
        item = CartItem.objects.get(pk=pk, cart__user=request.user, cart__is_active=True)
        
    except CartItem.DoesNotExist:
       
        messages.error(request, "Item not found or you don't have permission to delete it.")
        return redirect('cart_view')
    
    item.delete()
    messages.success(request, "Item removed from cart.")
    return redirect('cart_view')


  

def cart_view(request):
    
    if request.user.is_authenticated:
        if not request.user.is_active:
            messages.error(request, "Your account is inactive. Please contact support.")
            return redirect('user_login')  
    else:
        return redirect('user_login')
    
    cart = Cart.objects.filter(user=request.user, is_active=True).first()
    cart_items = cart.cart_items.all() if cart else [] 
    total_price = cart.total_price if cart else 0
    
    is_empty = len(cart_items) == 0


    return render(request, 'add_to_cart.html', {
        'cart_items': cart_items,
        'total_price': total_price,
        'is_empty': is_empty,
        
    })



@require_http_methods(["POST"])
def update_cart_item(request):
    
    
    if request.user.is_authenticated:
        if not request.user.is_active:
            messages.error(request, "Your account is inactive. Please contact support.")
            return redirect('user_login')  
    else:
        return redirect('user_login')
    
    try:
        data = json.loads(request.body)
        item_id = data.get('item_id')
        quantity = data.get('quantity')
        print(quantity)
        
        
        if quantity < 1:
            return JsonResponse({
                'success': False,
                'error': 'Quantity cannot be less than 1'
            })
        
        
       
        cart_item = CartItem.objects.select_related('variant', 'cart').get(
            id=item_id,
            cart__user=request.user,
            cart__is_active=True
        )
        print(item_id)
        
        
        if quantity > cart_item.variant.stock:
            return JsonResponse({
                'success': False,
                'error': f'Only {cart_item.variant.stock} units available'
            })
        
        
        cart_item.quantity = min(quantity, 4)  # Ensure max 4 items
        cart_item.save()
        
        
        cart = cart_item.cart
        total_amount = sum(item.total_price for item in cart.cart_items.all())
        
        return JsonResponse({
            'success': True,
            'new_quantity': cart_item.quantity,
            'item_total_price': int(cart_item.total_price),  # Ensure it's a number
            'total_amount': int(total_amount)
        })
        
    except CartItem.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Cart item not found'
        })
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })
 
from django.views.decorators.csrf import csrf_protect


@csrf_protect  # This ensures CSRF protection
def set_primary_address(request):
    
    if request.user.is_authenticated:
        if not request.user.is_active:
            messages.error(request, "Your account is inactive. Please contact support.")
            return redirect('user_login')  
    else:
        return redirect('user_login')
    
    if request.user.is_authenticated:
        try:
            data = json.loads(request.body)
            address_id = data.get('address_id')

            
            address = Address.objects.filter(id=address_id, user=request.user).first()
            if address:
                
                Address.objects.filter(user=request.user).update(is_primary=False)
                
                
                address.is_primary = True
                address.save()
                
                return JsonResponse({'success': True})
            else:
                return JsonResponse({'success': False, 'error': 'Address not found or unauthorized'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    
    return JsonResponse({'success': False, 'error': 'User not authenticated'}, status=403) 




def checkout(request):
    if request.user.is_authenticated:
        if not request.user.is_active:
            messages.error(request, "Your account is inactive. Please contact support.")
            return redirect('user_login')  
    else:
        return redirect('user_login')
    
    profile, created = userprofile.objects.get_or_create(user=request.user)
    user_address = Address.objects.filter(user=request.user, is_delete=False)
    paymentmethod = PaymentMethod.objects.all()
    
    print(profile.mobile)
    
    try:
        cart = Cart.objects.get(user=request.user)
        cartitem = CartItem.objects.filter(cart=cart)
        total_price = cart.total_price if cart else 0
        
    except Cart.DoesNotExist:
        cart = None
        cartitem = []
    
    
        
    total_price = sum(item.total_price for item in cartitem)
    official = sum(item.total_official for item in cartitem)
    final_official = official
    final_total_price = total_price 
    
    
    discounted_total = total_price
    request.session['final_official'] = float(final_official)  
    
    available_coupons = Coupon.objects.filter(
        is_active=True,
        end_date__gte=timezone.now(),
        minimum_purchase_amount__lte=total_price  # Only coupons that meet the cart's total
    )
    
    available_coupons = Coupon.objects.filter(is_active=True, end_date__gte=timezone.now())

    # Check if a coupon code is in the session
    selected_coupon_code = request.session.get('selected_coupon_code')
    coupon_discount = 0.0

    if selected_coupon_code:
        coupon = Coupon.objects.filter(code=selected_coupon_code, is_active=True).first()
        if coupon:
            coupon_discount = Decimal(coupon.calculate_discount(total_price))
            discounted_total = max(total_price - coupon_discount, 0)
    
    user_address_json = serialize('json', user_address, fields=('address_line_1', 'address_line_2', 'city', 'state', 'postal_code', 'is_primary'))   
    
    context = {
        "profile": profile,
        "user_address": user_address,
        "paymentmethod": paymentmethod,
        "cart": cart,
        "total_price": total_price,
        'official': official,
        "cartitem": cartitem,
        "final_total_price": final_total_price,
        'final_official': final_official,
        "available_coupons": available_coupons,  
        "user_address_json": user_address_json,
        "discounted_total": discounted_total,
        "selected_coupon_code": selected_coupon_code,
        'coupon_discount':coupon_discount
        
    }

    return render(request, 'checkout.html', context)


from django.http import JsonResponse
from django.views.decorators.http import require_POST

from django.core.exceptions import ObjectDoesNotExist


@require_POST
def apply_coupon_checkout(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Authentication required."}, status=403)

    data = json.loads(request.body)
    coupon_code = data.get('coupon_code')
    
    
    try:
        cart = Cart.objects.get(user=request.user, is_active=True)
        cart_items = CartItem.objects.filter(cart=cart)
    except Cart.DoesNotExist:
        return JsonResponse({"error": "Cart not found."}, status=404)

    
    coupon = Coupon.objects.filter(code=coupon_code, is_active=True).first()
    if not coupon:
        return JsonResponse({"error": "Invalid coupon code."}, status=400)

    
    valid, message = coupon.is_valid(cart.total_price)
    if not valid:
        return JsonResponse({"error": message}, status=400)

    final_official = sum(item.total_official for item in cart_items)
    discount = coupon.calculate_discount(cart.total_price)
    discounted_total = max(cart.total_price - discount, 0)

   
    request.session['selected_coupon_code'] = coupon_code
    request.session['coupon_discount'] = float(discount)
    request.session['discounted_total'] = float(discounted_total)
    request.session['final_official'] = float(final_official)  

    return JsonResponse({
    "success": True,
    "total_price": cart.total_price,
    "coupon_discount": float(discount),  
    "discounted_total": float(discounted_total), 
    "final_official": float(final_official)
     
})

from django.http import JsonResponse

def remove_coupon_from_checkout(request):
    if request.user.is_authenticated:
        if not request.user.is_active:
            messages.error(request, "Your account is inactive. Please contact support.")
            return redirect('user_login')  
    else:
        return redirect('user_login')
    
    try:
        
        if 'selected_coupon_code' in request.session:
            del request.session['selected_coupon_code']
        if 'coupon_discount' in request.session:
            del request.session['coupon_discount']
        if 'discounted_total' in request.session:
            del request.session['discounted_total']

        
        cart = Cart.objects.filter(user=request.user, is_active=True).first()
        if not cart:
            return JsonResponse({"error": "Cart not found."}, status=404)

        
        total_price = cart.total_price

        return JsonResponse({
            "total_price": total_price,      
            "coupon_discount": 0,            
            "discounted_total": total_price, 
            "grand_total": total_price       
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)





def placeorder(request):
   
    if not request.user.is_authenticated:
        return redirect('user_login')

 
    if not request.user.is_active:
        messages.error(request, "Your account is inactive. Please contact support.")
        return redirect('user_login')

    try:
       
        cart = Cart.objects.get(user=request.user)
        cart_items = CartItem.objects.filter(cart=cart)
    except Cart.DoesNotExist:
        messages.error(request, "Cart not found.")
        return redirect("cart_view")

    
    if not cart_items:
        messages.error(request, "Your cart is empty.")
        return redirect("cart_view")

    
    payment_method_name = request.POST.get("payment_method")
    try:
        payment_method_instance = PaymentMethod.objects.get(name=payment_method_name)
    except PaymentMethod.DoesNotExist:
        messages.error(request, "Invalid payment method.")
        return redirect("cart_view")

  
    address_id = request.POST.get("address")
    if not address_id:
        messages.error(request, "Please select a valid address.")
        return redirect("cart_view")

    try:
        selected_address = Address.objects.get(id=address_id, user=request.user)
    except Address.DoesNotExist:
        messages.error(request, "Invalid address selected.")
        return redirect("cart_view")
    
    request.session['address'] = {
        'addressline1': selected_address.address_line_1,
        'addressline2': selected_address.address_line_2,
        'city': selected_address.city,
        'state': selected_address.state,
        'zip_code': selected_address.postal_code,
        'country': selected_address.country,
    }

    # Handle coupon and discount logic
    selected_coupon_code = request.session.get('selected_coupon_code')
    coupon_discount = Decimal(request.session.get('coupon_discount', 0.0))
    discounted_total = Decimal(request.session.get('discounted_total', cart.total_price))
    
    final_official = Decimal(request.session.get('final_official', 0.0))
    print(f"Official Price: {final_official}")

    
    coupon_discount = Decimal(request.session.get('coupon_discount', 0.0))

    # Calculate the price difference (original price - discounted price)
    original_price = Decimal(cart.total_price)
    discounted_total = Decimal(request.session.get('discounted_total', original_price))
    price_difference = final_official - discounted_total

    # Sum of coupon discount and price difference
    total_discount =  price_difference
    request.session['total_discount'] = str(total_discount)
    print(f"Order Discount Applied: {total_discount}")

    coupon = Coupon.objects.filter(code=selected_coupon_code, is_active=True).first() if selected_coupon_code else None 
    if coupon:
    
        print(coupon.used_count)
    else:
    
        print('Coupon not found')

    try:
        if payment_method_name == "Razopay":
            print("Initializing Razorpay client...")
            client = razorpay.Client(auth=(settings.RAZOR_API_KEY, settings.RAZOR_SECRET_ID))
            amount = int(discounted_total * 100)  # Convert to paise for Razorpay

            print(f"Creating Razorpay order for amount: {amount}")
            razorpay_order = client.order.create({
                "amount": amount,
                "currency": "INR",
                "payment_capture": "1"  
            })
            print(f"Razorpay order created successfully: {razorpay_order}")

            # Save Razorpay order ID and summary to session
            request.session['razorpay_order_id'] = razorpay_order['id']
            request.session['order_summary'] = {
                'original_price': float(cart.total_price),
                'offer_price': float(discounted_total),
                'coupon_discount': float(coupon_discount),
                'grand_total_in_paise': float(discounted_total) * 100
            }
            print("Saved Razorpay order details in session.")
            print(f"Original Price: {cart.total_price}")
            print(f"Offer Price (Discounted Total): {discounted_total}")
            

            # Create the order in your system
            print("Creating order in the system...")
            order = Order.objects.create(
                user=request.user,
                added_date=timezone.now(),
                paymentmethod=payment_method_instance,
                total_amount=discounted_total,
                shipping_address=selected_address,
                coupon=coupon if selected_coupon_code else None,
                is_paid=False  # Will be updated after payment verification
            )
            print(f"Order created: {order.id}")

           
            total_amount = Decimal(0)
            order_items = []  # Store the order items in a list first
            for item in cart_items:
                order_item = OrderItem(
                    order=order,
                    variant=item.variant,
                    quantity=item.quantity,
                    price=item.variant.price,
                    status="Processing",  # Initially, the status is "Pending"
                    product_name=item.variant.product.name,
                    
                )
                order_items.append(order_item)  # Append to the list, not saving yet

            # Now, save all order items after the loop
            for order_item in order_items:
                order_item.save(update_stock=False) 
                print(f"Updated stock for variant: {order_item.variant.id} - {order_item.variant.stock} remaining")
                    
                total_amount += order_item.get_total_price()
                print(f"Added item to order: {order_item}")
                
                request.session['order_id'] = order.id  
                print(f"Saved order ID {order.id} to session.")

            
            final_total = total_amount - coupon_discount
            order.total_amount = final_total
            # order.discount_applied = total_discount 
            order.save()
            print(f"Final order amount after discount: {final_total}")
            

            
            order.razorpay_order_id = razorpay_order['id']
            order.save()
            print("Razorpay order ID saved in the order.")

            # messages.success(request, "Order created successfully. Please proceed to payment.")
            return redirect('payment_confirmation')

        elif payment_method_name == 'Wallet':
            
            wallet = Wallet.objects.get(user=request.user)

            if wallet.balance < discounted_total:
                return JsonResponse({"error": "Insufficient Wallet Balance"}, status=400)

            wallet.debit(discounted_total)

            
            order = Order.objects.create(
                user=request.user,
                added_date=timezone.now(),
                paymentmethod=payment_method_instance,
                total_amount=discounted_total,
                shipping_address=selected_address,
                coupon=coupon if selected_coupon_code else None,
                is_paid=True  
            )

            
            total_amount = Decimal(0)
            for item in cart_items:
                order_item = OrderItem.objects.create(
                    order=order,
                    variant=item.variant,
                    quantity=item.quantity,
                    price=item.variant.price,
                    status="Pending",  
                    product_name=item.variant.product.name
                )
                total_amount += order_item.get_total_price()

            
            final_total = total_amount - coupon_discount
            order.total_amount = final_total
            order.discount_applied = total_discount 
            order.save()
            print(f"Final order amount after discount: {final_total}")
            print(f"Order Discount Applied: {order.discount_applied}")

            
            Transaction.objects.create(
                wallet=wallet,
                user=request.user,
                amount=discounted_total,
                transaction_type='debit',
                description=f"Payment for order {order.id}"
            )

  
            cart_items.delete()

            request.session.pop('selected_coupon_code', None)
            request.session.pop('coupon_discount', None)
            request.session.pop('discounted_total', None)

            messages.success(request, "Order placed successfully using Wallet!")
            return redirect('userorders')

        elif payment_method_name == "Cash On Delivery":
           
            order = Order.objects.create(
                user=request.user,
                added_date=timezone.now(),
                paymentmethod=payment_method_instance,
                total_amount=discounted_total,
                shipping_address=selected_address,
                coupon=coupon if selected_coupon_code else None,
                is_paid=False  # Mark as unpaid (Pending payment)
            )

            # Add items to the order
            total_amount = Decimal(0)
            for item in cart_items:
                order_item = OrderItem.objects.create(
                    order=order,
                    variant=item.variant,
                    quantity=item.quantity,
                    price=item.variant.price,
                    status="Pending",  
                    product_name=item.variant.product.name
                )
                total_amount += order_item.get_total_price()

            
            final_total = total_amount - coupon_discount
            if final_total > 1000:
                messages.error(request, "Cash On Delivery is only available for orders of ₹1000 or less.")
                order.delete()  
                return redirect(reverse('checkout'))
                    
            
            order.total_amount = final_total
            order.discount_applied = total_discount 
            order.save()
            
            if coupon:
    
                print(coupon.used_count)
            else:
            
                print('Coupon not found')

            
            cart_items.delete()

            
            request.session.pop('selected_coupon_code', None)
            request.session.pop('coupon_discount', None)
            request.session.pop('discounted_total', None)

            messages.success(request, "Order placed successfully! Please pay during delivery.")
            return redirect('userorders')  

    except Exception as e:
        messages.error(request, f"Error placing order: {str(e)}")
        return redirect("cart_view")
    

def payment_confirmation_view(request):
    if request.user.is_authenticated:
        if not request.user.is_active:
            messages.error(request, "Your account is inactive. Please contact support.")
            return redirect('user_login')  
    else:
        return redirect('user_login')
    
    razorpay_order_id = request.session.get('razorpay_order_id')
    order_summary = request.session.get('order_summary', {})
    selected_address = request.session.get('address')
    selected_coupon_code = request.session.get('coupon')
    order_id = request.session.get('order_id') 
    selected_address = request.session.get('address')
    
    
    
    if not order_id:
        print("Error: Order ID is not in the session.")

    return render(request, 'payment_confirmation.html', {
        'razorpay_order_id': razorpay_order_id,
        'razorpay_key': settings.RAZOR_API_KEY,
        'order_summary': order_summary,
        'selected_address': selected_address,
        'selected_coupon_code': selected_coupon_code,
        'order_id': order_id, 
    })
  
    

@csrf_exempt
def verify_payment(request):
    if request.user.is_authenticated:
        if not request.user.is_active:
            messages.error(request, "Your account is inactive. Please contact support.")
            return redirect('user_login')  
    else:
        return redirect('user_login')
    print("Starting payment verification...")

    razorpay_payment_id = request.POST.get('razorpay_payment_id')
    razorpay_order_id = request.POST.get('razorpay_order_id')
    razorpay_signature = request.POST.get('razorpay_signature')

    print(f"POST data received: Payment ID={razorpay_payment_id}, Order ID={razorpay_order_id}, Signature={razorpay_signature}")

    if not (razorpay_payment_id and razorpay_order_id and razorpay_signature):
        return JsonResponse({'status': 'failed', 'message': 'Incomplete payment details received'})

    
    razorpay_order_id_from_session = request.session.get('razorpay_order_id')
    print(f"Session Razorpay Order ID: {razorpay_order_id_from_session}")

    if razorpay_order_id_from_session != razorpay_order_id:
        return JsonResponse({'status': 'failed', 'message': 'Order ID mismatch between session and payment data'})

    
    client = razorpay.Client(auth=(settings.RAZOR_API_KEY, settings.RAZOR_SECRET_ID))
    order_id = request.session.get('order_id')
    params_dict = {
        'razorpay_order_id': razorpay_order_id,
        'razorpay_payment_id': razorpay_payment_id,
        'razorpay_signature': razorpay_signature,
    }

    try:
        print("Verifying payment signature...")
        client.utility.verify_payment_signature(params_dict)
        print("Payment signature verified successfully.")

        
        order_id = request.session.get('order_id')
        if not order_id:
            return JsonResponse({'status': 'failed', 'message': 'Order ID not found in session'})

        print(f"Fetching order with ID: {order_id}")
        order = Order.objects.get(id=order_id)
        order.is_paid = True
        order.save()
        print(f"Order marked as paid: {order.id}")
        
        total_discount = Decimal(request.session.get('total_discount', 0.0)) # Calculate the discount based on session data
        order.discount_applied = total_discount
        order.save()
        print(f"Order Discount Applied: {order.discount_applied}")
        
        
        for order_item in order.order_items.all():
            order_item.status = "Pending"  # Change status to 'Pending' when payment is successful
            order_item.save()

       
        for order_item in order.order_items.all():
            variant = order_item.variant
            variant.stock -= order_item.quantity
            variant.save()
            print(f"Reduced stock for variant: {variant.id}")
            print(f"Updated stock for variant: {order_item.variant.id} - {order_item.variant.stock} remaining")

        
        cart = Cart.objects.get(user=request.user)
        cart.cart_items.all().delete()
        print("Cleared cart items.")

        
        for key in ['razorpay_order_id', 'order_id', 'selected_coupon_code', 'coupon_discount', 'discounted_total']:
            request.session.pop(key, None)
            print(f"Cleared session key: {key}")

        messages.success(request, "Payment verified and order placed successfully!")

        
        return redirect('userorders')

    except razorpay.errors.SignatureVerificationError as e:
        print(f"Payment signature verification failed: {e}")
        
        messages.error(request, "Payment signature verification failed. Please try again.")
        return redirect('cart_view')  

    except Exception as e:
        print(f"Unexpected error during payment verification: {e}")
       
        messages.error(request, f"Error: {str(e)}. Please try again.")
        return redirect('cart_view')
    
def userorders(request):
    
    if request.user.is_authenticated:
        if not request.user.is_active:
            messages.error(request, "Your account is inactive. Please contact support.")
            return redirect('user_login')  
    else:
        return redirect('user_login')
    
    user=request.user
    status_filter=request.GET.get('status','all')
    
    if status_filter == 'all':
        orders=OrderItem.objects.filter(order__user=user).order_by('-last_updated')
    else:
        orders=OrderItem.objects.filter(order__user=user ,status=status_filter.capitalize()).order_by('-last_updated')
        
    return render(request, 'user_your_order.html', {
        'orders': orders,
        'status_filter': status_filter
    })
    
    


def cancelorder(request, id):
    if not request.user.is_authenticated:
        return redirect('user_login')
    
    if not request.user.is_active:
        messages.error(request, "Your account is inactive. Please contact support.")
        return redirect('user_login')
    
    order_item = get_object_or_404(OrderItem, id=id, order__user=request.user)
    
    user = order_item.order.user
    wallet, created = Wallet.objects.get_or_create(user=user)
    
    
    if order_item.status != "Pending":
        messages.error(request, "Order cannot be canceled as it is already processed or delivered.")
        return redirect("userorders")
    
    try:
        cancel_reason = request.POST.get("cancel_reason", "").strip()

        if not cancel_reason:
            messages.error(request, "Cancel reason cannot be empty.")
            return redirect("userorders")
        
        pattern = r"^[a-zA-Z].*[a-zA-Z].*[a-zA-Z].*[a-zA-Z].*$"
        if not re.match(pattern, cancel_reason):
            messages.error(request, "Cancel reason must start with an alphabet and contain at least 4 alphabetic characters.")
            return redirect("userorders")
        
        discounted_price = Decimal( order_item.variant.get_discounted_price())
        refund_amount = discounted_price *  Decimal(order_item.quantity)
        
        with transaction.atomic():
            order_item.status = "Cancelled"
            order_item.cancellation_reason = cancel_reason
            order_item.save(update_stock=False)
            
            wallet, _ = Wallet.objects.get_or_create(user=request.user)
            
            
            if order_item.order.is_paid  and order_item.order.paymentmethod != "Cash On Delivery":    
                wallet.credit(refund_amount)
                Transaction.objects.create(
                    wallet=wallet,
                    user=request.user,
                    amount=refund_amount,
                    transaction_type='credit',
                    description="Order cancellation via Razorpay"
                )
                messages.success(request, f"Amount has been successfully refunded and added to your wallet.")
            
            if order_item.order.coupon and order_item.order.paymentmethod != "Cash On Delivery":
                coupon = order_item.order.coupon
                coupon_type = coupon.discount_type
                coupon_value = coupon.value
                adjusted_refund_amount = refund_amount

                
                total_order_items = order_item.order.order_items.count()
                print(f"Total items in the order: {total_order_items}")
                print(f"Initial refund amount for item: ₹{refund_amount}")

                
                if coupon_type == "PERCENTAGE":
                    
                    total_order_value = sum(item.get_total_price() for item in order_item.order.order_items.all())
                    print(f"Total order value: ₹{total_order_value}")
                    total_coupon_discount = (total_order_value * coupon_value) / 100
                    print(f"Total coupon discount at {coupon_value}%: ₹{total_coupon_discount}")
                 
                    if coupon.maximum_discount:
                        total_coupon_discount = min(total_coupon_discount, coupon.maximum_discount)
                        print(f"Total coupon discount after applying maximum limit of ₹{coupon.maximum_discount}: ₹{total_coupon_discount}")

                
                    if total_order_items > 0:
                        prorated_coupon_discount = total_coupon_discount / total_order_items
                    else:
                        prorated_coupon_discount = 0  
                        print(f"Prorated percentage coupon discount per item: ₹{prorated_coupon_discount}")

                    
                    adjusted_refund_amount -= prorated_coupon_discount
                    adjusted_refund_amount = max(adjusted_refund_amount, 0)
                    print(f"Adjusted refund amount after applying percentage coupon discount: ₹{adjusted_refund_amount}")

                elif coupon_type == "FIXED":
                    
                    if total_order_items > 0:
                        prorated_coupon_discount = coupon_value / total_order_items
                    else:
                        prorated_coupon_discount = 0  # Prevent division by zero

                    
                    adjusted_refund_amount -= prorated_coupon_discount
                    adjusted_refund_amount = max(adjusted_refund_amount, 0)

                
                    adjusted_refund_amount = max(adjusted_refund_amount, 0)
                    print(f"Final adjusted refund amount: ₹{adjusted_refund_amount}")

                    
                wallet.credit(adjusted_refund_amount)
                Transaction.objects.create(
                    wallet=wallet,
                    user=request.user,
                    amount=adjusted_refund_amount,
                    transaction_type='credit',
                    description=f"Refund for canceled item with coupon '{coupon.code}'"
                )

           
            order_item.variant.stock += order_item.quantity
            order_item.variant.save()

            messages.success(request, "Order item has been successfully canceled.")

    except Exception as e:
        messages.error(request, "An error occurred while canceling the order.")
        print(e)

    return redirect("userorders")

from django.db import transaction

def returnorder(request, id):
    if not request.user.is_authenticated:
        return redirect('user_login')
    
    if not request.user.is_active:
        messages.error(request, "Your account is inactive. Please contact support.")
        return redirect('user_login')
    
    order_item = get_object_or_404(OrderItem, id=id, order__user=request.user)
    
    if order_item.status != "Delivered":
        messages.error(request, "Order cannot be returned unless it is delivered.")
        return redirect("userorders")
    
    try:
        return_reason = request.POST.get("return_reason", "").strip()
        
        if not return_reason:
            messages.error(request, "Return reason cannot be empty.")
            return redirect("userorders")
        
        
        pattern = r"^[a-zA-Z].*[a-zA-Z].*[a-zA-Z].*[a-zA-Z].*$"  
        if not re.match(pattern, return_reason):
            messages.error(request, "Return reason must start with an alphabet and contain at least 4 alphabetic characters.")
            return redirect("userorders")

       
        with transaction.atomic():
            order_item.status = "Return Requested"
            order_item.return_reason = return_reason
            order_item.save()

        messages.success(request, "Your return request has been submitted. Admin approval is pending.")
    except Exception as e:
        messages.error(request, "An error occurred while submitting the return request.")
        print(e)

    return redirect("userorders")




def wishlist(request):
    if request.user.is_authenticated:
        if not request.user.is_active:
            messages.error(request, "Your account is inactive. Please contact support.")
            return redirect('user_login')  
    else:
        return redirect('user_login')
    items = Wishlist.objects.filter(
        user=request.user, 
        varients__is_delete=False,  # Ensure variants are not deleted
        varients__product__is_delete=False  # Ensure the product's category is not deleted
    ).distinct()
    return render(request , 'wishlist.html',{'items':items})


from django.urls import reverse

def add_to_wishlist(request):
    if not request.user.is_authenticated:
        return redirect('user_login')

    if not request.user.is_active:
        messages.error(request, "Your account is inactive. Please contact support.")
        return redirect('user_login')

    if request.method == 'POST':
        variant_id = request.POST.get('variant_id')
        if not variant_id:
            messages.error(request, "Variant ID is required.")
            return redirect('product_list')  # Redirect to product list or any appropriate page

        variant = get_object_or_404(Variants, id=variant_id, is_delete=False)
        product = variant.product  
        

       
        if Wishlist.objects.filter(user=request.user, varients=variant).exists():
            messages.error(request, "This product is already in your wishlist.")
            return redirect(reverse('product_view', kwargs={'pk': product.pk}))

        
        Wishlist.objects.create(user=request.user, varients=variant)
        messages.success(request, "Product added to your wishlist.")
        return redirect(reverse('product_view', kwargs={'pk': product.pk}))

    messages.error(request, "Invalid request method.")
    return redirect('product_list')


def delete_wishlist(request, id):
    if not request.user.is_authenticated:
        return redirect('user_login')
    
    if not request.user.is_active:
        messages.error(request, "Your account is inactive. Please contact support.")
        return redirect('user_login')
    
   
    variant = get_object_or_404(Variants, id=id)
    
    
    wishlist_item = Wishlist.objects.filter(user=request.user, varients=variant).first()
    
    if wishlist_item:
        wishlist_item.delete()
        messages.success(request, "Item successfully removed from the wishlist.")
    else:
        messages.error(request, "The item could not be found in your wishlist.")
    
    
    return redirect('wishlist') 

def wallet(request):
    
    if request.user.is_authenticated:
        if not request.user.is_active:
            messages.error(request, "Your account is inactive. Please contact support.")
            return redirect('user_login')  
    else:
        return redirect('user_login')
    try :
        wallet=Wallet.objects.get(user=request.user)
    except Wallet.DoesNotExist:
        wallet=Wallet.objects.create(user=request.user)
        
    transactions = Transaction.objects.filter(user=request.user).order_by('-timestamp')
    
    return render(request, 'wallet.html', {
        'wallet': wallet,
        'transactions': transactions
    })
    
    
@login_required(login_url='userlogin')
def wallet_recharge(request):
    if request.user.is_authenticated:
        if not request.user.is_active:
            messages.error(request, "Your account is inactive. Please contact support.")
            return redirect('user_login')  
    else:
        return redirect('user_login')
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            recharge_amount = data.get('amount')

            if not recharge_amount or float(recharge_amount) <= 0:
                return JsonResponse({"error": "Invalid amount"}, status=400)

            client = razorpay.Client(auth=(settings.RAZOR_API_KEY , settings.RAZOR_SECRET_ID))

            amount_in_paise = int(float(recharge_amount) * 100)

            razorpay_order = client.order.create({
                "amount": amount_in_paise,
                "currency": "INR",
                "payment_capture": "1"
            })

            request.session['wallet_recharge_order'] = {
                "amount": recharge_amount,
                "razorpay_order_id": razorpay_order['id']
            }

            return JsonResponse({
                "razorpay_order_id": razorpay_order['id'],
                "razorpay_key_id": settings.RAZOR_API_KEY,
                "amount": recharge_amount
            }, status=200)
        except Exception as e:
            return JsonResponse({"error": f"Failed to initiate recharge: {str(e)}"}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=405)


@csrf_exempt
def wallet_recharge_success(request):
    if request.user.is_authenticated:
        if not request.user.is_active:
            messages.error(request, "Your account is inactive. Please contact support.")
            return redirect('user_login')  
    else:
        return redirect('user_login')
    if request.method == "POST":
        try:
            
            data = json.loads(request.body)
            razorpay_payment_id = data.get('razorpay_payment_id')
            razorpay_order_id = data.get('razorpay_order_id')

            
            session_order = request.session.get('wallet_recharge_order')
            print("Session Order:", session_order)
            print("Session razorpay_order_id:", session_order.get('razorpay_order_id') if session_order else None)
            print("Received razorpay_order_id:", razorpay_order_id)

            
            if not session_order or session_order.get('razorpay_order_id') != razorpay_order_id:
                print("Order ID mismatch or order not found in session")
                return JsonResponse({"status": "error", "message": "Order not found or mismatched"}, status=404)

           
            user = request.user
            amount = Decimal(session_order['amount'])  # Retrieve the correct amount from session

            
            wallet = Wallet.objects.get(user=user)
            wallet.credit(amount)

           
            Transaction.objects.create(
                wallet=wallet,
                user=user, 
                amount=amount,
                transaction_type='credit',
                description='Wallet recharge via Razorpay'
            )

           
            del request.session['wallet_recharge_order']

            return JsonResponse({"status": "success", "message": "Wallet recharge successful"}, status=200)

        except Wallet.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Wallet not found"}, status=404)
        except Exception as e:
            print("Error during wallet recharge:", str(e))
            return JsonResponse({"status": "error", "message": f"Recharge failed: {str(e)}"}, status=500)

    return JsonResponse({"status": "error", "message": "Invalid request"}, status=400)




@login_required(login_url='userlogin')
def download_invoice(request, order_id):
    from decimal import Decimal  
    from Sko_Adminside.models import Order
      
    if not request.user.is_authenticated:
        return redirect('user_login')
    
    if not request.user.is_active:
        messages.error(request, "Your account is inactive. Please contact support.")
        return redirect('user_login')

    # Fetch order for the logged-in user
    order = Order.objects.filter(id=order_id, user=request.user).first()
    if not order:
        return HttpResponse("Unauthorized or order not found", status=401)

    # Create a buffer for PDF generation
    buffer = BytesIO()
    pdf = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []  # Collects elements to add to the PDF
    styles = getSampleStyleSheet()

    # Add title to PDF
    elements.append(Paragraph(f"<b>Invoice for Order ID: {order.id}</b>", styles["Title"]))

    # Add Order Details Table
    order_details = [
        ["Order Date", order.added_date.strftime("%d/%m/%Y")],
        ["Customer Name", order.user.username],
        ["Payment Method", order.paymentmethod.name],
        ["Payment Status", "Paid" if order.is_paid else "Not Paid"] ,
        ["Coupon Used", order.coupon.code if order.coupon else "N/A"]
    ]
    details_table = Table(order_details, colWidths=[150, 350])
    details_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ])
    )
    elements.append(details_table)
    elements.append(Paragraph("<br/>", styles["Normal"]))

    # Add Order Items Table
    items_data = [["Item Name", "Quantity", "Unit Price (₹)", "Total (₹)"]]  # Table Header
    for item in order.order_items.all():
        items_data.append([
            item.product_name,
            item.quantity,
            f"{item.price:.2f}",
            f"{Decimal(item.quantity) * Decimal(item.price):.2f}"
        ])

    items_table = Table(items_data, colWidths=[200, 100, 100, 100])
    items_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 10),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 1), (-1, -1), 10),
            ("ALIGN", (0, 1), (-1, -1), "LEFT"),
        ])
    )
    elements.append(items_table)
    elements.append(Paragraph("<br/>", styles["Normal"]))

    # Add Total Amount Table
    total_table = Table(
        [["Total Amount", f"₹{order.total_amount:.2f}"]],
        colWidths=[450, 100]
    )
    total_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
            ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 12),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
        ])
    )
    elements.append(total_table)

    # Generate PDF and return it as response
    pdf.build(elements)
    buffer.seek(0)
    return HttpResponse(buffer, content_type="application/pdf", headers={
        'Content-Disposition': f'attachment; filename=invoice_{order.id}.pdf',
    })
