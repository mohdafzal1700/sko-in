from django.shortcuts import render,redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as log , logout as authlogout
from django.contrib import messages
from Sko_Adminside.forms import AddressForm
from django.core.exceptions import ValidationError
from .utils import generate_otp,send_otp,clean_email,clean_password ,validate_image , validate_data, validate_phone
from datetime import datetime, timedelta
from Sko_Adminside.models import Product , Variants, VarientImage,userprofile,Address,Cart,CartItem,PaymentMethod,Order,OrderItem,Wishlist
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







def  user_sign(request):
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
def product_view(request, pk):
    if request.user.is_authenticated:  
   
        product = get_object_or_404(Product, id=pk, is_delete=False)
        print("Product: ", product.pk)

    
        variants = product.variants.filter(is_delete=False).prefetch_related('images')
        default_variant = variants.first() if variants.exists() else None
        product_image_url = request.build_absolute_uri(product.image.url)
        
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
 
 
 
       
from django.core.serializers import serialize       

def checkout(request):
    
    if request.user.is_authenticated:
        if not request.user.is_active:
            messages.error(request, "Your account is inactive. Please contact support.")
            return redirect('user_login')  
    else:
        return redirect('user_login')
    
    user_address = Address.objects.filter(user=request.user, is_delete=False)

    paymentmethod=PaymentMethod.objects.all()
    profile = get_object_or_404(userprofile, user=request.user)
    print(profile.mobile)
    
    try:
        cart=Cart.objects.get(user=request.user)
        cartitem=CartItem.objects.filter(cart=cart)
        
    except Cart.DoesNotExist:
        cart=None
        cartitem=[]
        
    total_price=sum(item.total_price for item in cartitem) 
    final_total_price=total_price     
    user_address_json = serialize('json', user_address , fields=('address_line_1', 'address_line_2', 'city', 'state', 'postal_code', 'is_primary'))   
    
    
    context={
        "profile": profile,
        "user_address":user_address,
        "paymentmethod":paymentmethod,
        "cart":cart,
        "total_price":total_price,
        "cartitem":cartitem,
        "paymentmethod":paymentmethod,
        "final_total_price":final_total_price,
        "user_address_json": user_address_json
        
        }
    return render(request,'checkout.html',context)



def placeorder(request):
    
    if request.user.is_authenticated:
        if not request.user.is_active:
            messages.error(request, "Your account is inactive. Please contact support.")
            return redirect('user_login')  
    else:
        return redirect('user_login')
    
    cart = Cart.objects.get(user=request.user)
    cart_items = CartItem.objects.filter(cart=cart)

    
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

    try:
        
        with transaction.atomic():

            
            order = Order.objects.create(
                user=request.user,
                added_date=timezone.now(),
                paymentmethod=payment_method_instance,
                total_amount=Decimal('0.00'),
                shipping_address=selected_address
            )

            total_amount = Decimal('0.00')

            
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

            
            order.total_amount = total_amount
            order.save()

            
            cart_items.delete()

        
        messages.success(request, "Order placed successfully!")
        return redirect('cart_view')

    except ValidationError as e:
        
        messages.error(request, str(e))
        return redirect("cart_view")

    except Exception as e:
       
        messages.error(request, "An error occurred while placing your order.")
        print(e)
        return redirect("cart_view")
    
        
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
 
  
def cancelorder(request,id):
    
    if request.user.is_authenticated:
        if not request.user.is_active:
            messages.error(request, "Your account is inactive. Please contact support.")
            return redirect('user_login')  
    else:
        return redirect('user_login')
    
    order_item=get_object_or_404(OrderItem,id=id,order__user=request.user)
    
    if order_item.status !="Pending":
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


        with transaction.atomic():
            order_item.status = "Canceled"
            
            print(cancel_reason)
            order_item.cancellation_reason= cancel_reason
            order_item.save(update_stock=False)  
            
            order_item.variant.stock += order_item.quantity  
            order_item.variant.save()

            messages.success(request, "Order item has been successfully canceled.")
    except Exception as e:
        messages.error(request, "An error occurred while canceling the order.")
        print(e)

    return redirect("userorders")


def returnorder(request,id):
    
    if request.user.is_authenticated:
        if not request.user.is_active:
            messages.error(request, "Your account is inactive. Please contact support.")
            return redirect('user_login')  
    else:
        return redirect('user_login')
    
    order_item=get_object_or_404(OrderItem,id=id,order__user=request.user)
    
    if order_item.status !="Delivered":
        messages.error(request, "Order cannot be returned unless it is delivered.")
        return redirect("userorders")
    
    
    try:
        return_reason = request.POST.get("return_reason", "").strip()

        
        if not return_reason:
            messages.error(request, "Cancel reason cannot be empty.")
            return redirect("userorders")
        
        pattern = r"^[a-zA-Z].*[a-zA-Z].*[a-zA-Z].*[a-zA-Z].*$"  
        if not re.match(pattern, return_reason):
            messages.error(request, "Cancel reason must start with an alphabet and contain at least 4 alphabetic characters.")
            return redirect("userorders")

        with transaction.atomic():
           order_item.status= "Returned"
           return_reason=request.POST.get("return_reason", "")
           print(return_reason)
           order_item.return_reason = return_reason
           print(order_item.return_reason)
           order_item.save(update_stock=False)  
            
           order_item.variant.stock += order_item.quantity  
           order_item.variant.save()
           messages.success(request, "Order item has been successfully returned.")
           
    except Exception as e:
        messages.error(request, "An error occurred while returning the order.")
        print(e)

    return redirect("userorders")


def wishlist(request):
    items=Wishlist.objects.filter(user=request.user)
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
        product = variant.product  # Get the product related to the variant
        

        # Check if the product is already in the user's wishlist
        if Wishlist.objects.filter(user=request.user, varients=variant).exists():
            messages.error(request, "This product is already in your wishlist.")
            return redirect(reverse('product_view', kwargs={'pk': product.pk}))

        # Add to wishlist
        Wishlist.objects.create(user=request.user, varients=variant)
        messages.success(request, "Product added to your wishlist.")
        return redirect(reverse('product_view', kwargs={'pk': product.pk}))

    messages.error(request, "Invalid request method.")
    return redirect('product_list')


def delete_wishlist(request, id):
   
    variant = get_object_or_404(Variants, id=id)
    
    
    wishlist_item = Wishlist.objects.filter(user=request.user, varients=variant).first()
    
    if wishlist_item:
        wishlist_item.delete()
        messages.success(request, "Item successfully removed from the wishlist.")
    else:
        messages.error(request, "The item could not be found in your wishlist.")
    
    
    return redirect('wishlist') 