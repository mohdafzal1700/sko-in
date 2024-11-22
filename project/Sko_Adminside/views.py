from django.shortcuts import render , redirect
from django.contrib.auth import authenticate,login as admin_log ,logout as logout_admin
from django.contrib import messages
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.forms import modelformset_factory 
from .models import Category ,Product ,Variants ,VarientImage  , OrderItem , Offer ,Coupon
from .forms import ProductForm ,VariantForm, VarientImageForm , OfferForm , CouponForm
from django.contrib.auth.decorators import login_required
import re
from django.db.models import Q, Count
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.core.paginator import Paginator

# <-adminlogin-> #

def adminlogin(request):
    if request.user.is_authenticated  and request.user.is_superuser :
        return redirect('dashboard')
    
    if request.POST:
        username=request.POST['username']
        password=request.POST['password']
        
        user= authenticate(username=username,password=password)
        
        if user is None:
            messages.error(request, "Invalid username or password")
            return render(request , "adminlogin.html" , {'username':username}) 
        elif  user.is_superuser:
            messages.success(request,'sucessfully logged in')
            admin_log(request,user)
            return redirect('dashboard')   
        else:
            messages.error(request, f"{user} have no access to this page")
            return render(request , "adminlogin.html" , {'username':username}) 
    return render(request, "adminlogin.html")   

# <-dashboard-> #     

@login_required(login_url='/adminlogin/')
def dashboard(request):
    if request.user.is_authenticated  and request.user.is_superuser :
      return render(request,'dashboard.html')
    else:
       
        return redirect('adminlogin') 

# <-adminlogout-> #

def admin_logout(request):
    
    logout_admin(request)
    return redirect('adminlogin')

# <-Customers-> #

@login_required
def customers(request):
    if request.user.is_authenticated  and request.user.is_superuser :
    
        users=User.objects.exclude(is_superuser=True).order_by('-date_joined')
      
        return render(request, "customer.html",  {"data": users})
    else:
       
        return redirect('adminlogin') 
    
# <-blockuser-> #

@login_required
def toggle_block_user(request, user_id):
    if request.user.is_authenticated  and request.user.is_superuser :  
        try:
            user = get_object_or_404(User, id=user_id)

            # Toggle the is_active field (True = Unblocked, False = Blocked)
            if user.is_active:
                user.is_active = False
                messages.success(request, "User has been blocked successfully!")
            else:
                user.is_active = True
                messages.success(request, "User has been unblocked successfully!")

            user.save()

        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")

        return redirect('customers')
    else:
       
        return redirect('adminlogin') 


def searchcustomer(request):
    if request.POST:
        search_customer=request.POST['search']
        users=User.objects.filter(username__icontains=search_customer ).exclude(is_superuser=True).order_by('-date_joined')
          
        if not users.exists():  
                messages.error(request, "No categories found matching your search.")
    else:
            users = User.objects.exclude(is_superuser=True)
        
    return render(request, "customer.html",  {"data": users,"search":search_customer})
    



# <-Categories-> #

@login_required
def categories(request):
    if request.user.is_authenticated  and request.user.is_superuser : 
        categories=Category.objects.filter(is_delete=False)
        
        
        return render(request,'categories.html', {"data": categories})
    else:
       
        return redirect('adminlogin') 

# <-add_Categories-> #

@login_required
def add_catrgories(request):
    if request.user.is_authenticated  and request.user.is_superuser : 
        data=Category.objects.all()
        
        if request.POST:
            category=request.POST['category_name']
            print(category)
            if not category:
                messages.error(request,'Enter the category name')
                return redirect("category") 
            
            elif len(category)< 3:
                messages.error(request,"Category name must have atleast 3 letters")
                return redirect("category")
            
            elif not re.match(r'^[A-Za-z]+$', category):
                messages.error(request, "Category name can only contain letters")
                return redirect("category")
                
            elif Category.objects.filter(name__icontains=  category ).exists():
                messages.error(request,"category is already exist")
                return redirect("category")
            else:
                newCategory=Category.objects.create(name=category) 
                newCategory.save()
                messages.success(request, f"New cagetory {newCategory} is created")
            return redirect("category")   
        
        return render(request,'categories.html', {"data": data})
    else:
       
        return redirect('adminlogin') 

# <-delete_Categories-> #

@login_required
def delete_categories(request, pk):
    if request.user.is_authenticated  and request.user.is_superuser : 
        try:
            del_categories=get_object_or_404(Category,pk=pk)
            del_categories.is_delete=True
            del_categories.save()
            messages.success(request,'Sucessfully deleted')
        except  Exception  as e:
            messages.error(request, f"An error occurred: {str(e)}")
        return redirect('category')
    else:
       
        return redirect('adminlogin')   

# <-edit_Categories-> #

@login_required
def edit_categories(request,pk):
    if request.user.is_authenticated  and request.user.is_superuser :
    
        category=get_object_or_404(Category,pk=pk)
         
        if request.POST:
            new_name = request.POST.get("categoryName")
             
            if not new_name:
                messages.error(request,'Enter the category name')
                return redirect("category") 
            
            elif len(new_name)<3:
                messages.error(request,"Category name must have atleast 3 letters")
                return redirect("category") 
            
            elif not new_name.isalpha():  # Ensures only alphabetic characters
                messages.error(request, "Category name must contain only letters")
                return redirect("category")
                
            elif Category.objects.filter(name__icontains=new_name).exists():
                 messages.error(request,"category is already exist")
                 return redirect("category") 
                
            else:
                category.name = new_name  
                category.save()  
                messages.success(request, "Category updated successfully!")
                return redirect('category')
                 
        
        return render(request, 'categories.html',  {'category': category})
    else:
       
        return redirect('adminlogin') 
    
# <-searchCategories-> # 
@login_required
def searchCategory(request):
    if request.user.is_authenticated and request.user.is_superuser:
        if request.method == "POST":
            category = request.POST.get('search', '').strip()
            if category:
              
                searchCategory = Category.objects.filter(name__icontains=category, is_delete=False)
                if not searchCategory.exists():
                    messages.error(request, "No categories found matching your search.")
            else:
                
                searchCategory = Category.objects.filter(is_delete=False)
        else:
            
            searchCategory = Category.objects.filter(is_delete=False)

        context = {"data": searchCategory}    
        return render(request, 'categories.html', context)
    else:
        return redirect('adminlogin')

# <-products-> #
          
@login_required(login_url='/adminlogin/')               

def products(request):
    if request.user.is_superuser:
        
        products_list = Product.objects.filter(
            is_delete=False,
            category__is_delete=False
        ).annotate(
            active_variants_count=Count('variants', filter=Q(variants__is_delete=False))
        ).filter(
            active_variants_count__gt=0  
        ).prefetch_related('variants').order_by('-id')

       
        paginator = Paginator(products_list, 4)  
        page_number = request.GET.get('page')  
        page_obj = paginator.get_page(page_number)  

        print("Products retrieved:", products_list)

       
        return render(request, "products.html", {"page_obj": page_obj})

    else:
        
        return redirect('adminlogin')
 

# <-add_products-> # 
    
@login_required
def add_product(request):
    if request.user.is_authenticated  and request.user.is_superuser :  
        if request.method == 'POST':
            print('Received POST request')

            # Initialize product form with POST data
            product_form = ProductForm(request.POST)

            if product_form.is_valid():
                print('Saving product...')
                product = product_form.save()  # Save the product object

                # Success message and redirect to product list
                messages.success(request, 'Product added successfully!')
                return redirect('add_variant',product_id=product.id)  # Replace 'products' with the correct URL name if needed

            else:
                # Print form errors for debugging
                print('Product Form Errors:', product_form.errors)

        else:
            # Render an empty product form on GET request
            product_form = ProductForm()

        return render(request, 'add_product.html', {
            'product_form': product_form,
        })
    else:
       
        return redirect('adminlogin') 


# <-edit_products-> #

from django.core.exceptions import ValidationError
from User_side.utils import validate_image
@login_required
def edit_product(request, pk):
    if request.user.is_authenticated  and request.user.is_superuser :  
    
        product = get_object_or_404(Product, pk=pk)

        if request.method == 'POST':
            
            product_form = ProductForm(request.POST, request.FILES, instance=product)

            if product_form.is_valid():
            
                product_form.save()
                messages.success(request, 'Product updated successfully!')
                return redirect('add_variant',product_id=product.id)  # Redirect to the products list after saving
            else:
                messages.error(request,'Product Form Errors')
                print('Product Form Errors:', product_form.errors)

        else:
            
            product_form = ProductForm(instance=product)

        return render(request, 'edit_product.html', {
            'product_form': product_form,
            'product': product,
        })
    else:
       
        return redirect('adminlogin') 

    

# <-delete_products-> #

@login_required    
def delete_products(request,pk):
    if request.user.is_authenticated  and request.user.is_superuser :
   
            product=get_object_or_404(Product,pk=pk)
            product.is_delete=True
            product.save()
            messages.success(request,'Sucessfully deleted')
  
            return redirect('products')   
    else:
       
        return redirect('adminlogin') 



# <-delete_products-> #

@login_required        
def searchproduct(request):
    if request.user.is_authenticated and request.user.is_superuser:
        
        product_name = request.GET.get('search', '')  
        if product_name: 
            search_results = Product.objects.filter(name__icontains=product_name)
            if not search_results.exists():  
                messages.error(request, "No products found matching your search.")
        else:
          
            search_results = Product.objects.all()

       
        paginator = Paginator(search_results, 6)  
        page_number = request.GET.get('page')  
        page_obj = paginator.get_page(page_number)

       
        context = {"page_obj": page_obj, "search_query": product_name}
        return render(request, 'products.html', context)
    else:
        return redirect('adminlogin')


# <-add_variant-> #

@login_required
def add_variant(request, product_id):
    if request.user.is_authenticated  and request.user.is_superuser :  
        product = get_object_or_404(Product, pk=product_id)
        image_range = range(4)
        
        SIZE_CHOICES = [
            ('36', '36'), ('38', '38'), ('40', '40'), 
            ('42', '42'), ('43', '43'), ('44', '44'), ('45', '45'),
        ]
        
        COLOR_CHOICES = [
            ('red', 'Red'), ('blue', 'Blue'), ('green', 'Green'),
            ('black', 'Black'), ('white', 'White'), ('yellow', 'Yellow'),
            ('purple', 'Purple'), ('gray', 'Gray'), ('pink', 'Pink'),
            ('orange', 'Orange'),
        ]

        if request.method == 'POST':
            
            sizes = request.POST.getlist('size')
            colors = request.POST.getlist('color')
            stocks = request.POST.getlist('stock')
            prices = request.POST.getlist('price')

           
            uploaded_images = [request.FILES.getlist(f'image_{i}') for i in range(4)]
            uploaded_images = [img for sublist in uploaded_images for img in sublist]  
            uploaded_images = [img for img in uploaded_images if img]  

            
            if len(uploaded_images) < 4:
                messages.error(request, 'Please upload at least 4 images.')
                return render(
                    request, 
                    'addvarient.html', 
                    {'product': product}
                )
                
            for image_file in uploaded_images:
                try:
                    validate_image(image_file)  
                except ValidationError as e:
                    
                    messages.error(request, f"Image validation error: {str(e)}")
                    return render(
                        request, 
                        'addvarient.html', 
                        {'product': product,
                         'SIZE_CHOICES': SIZE_CHOICES,
                         'COLOR_CHOICES': COLOR_CHOICES,}
                    )

            for i in range(len(sizes)):
                size = sizes[i]
                color = colors[i]
                stock = stocks[i]
                price = prices[i]

                try:
                    stock = int(stock)
                    price = float(price)

                    if stock <= 0:
                        raise ValueError("Stock must be greater than zero.")
                    if price <= 0:
                        raise ValueError("Price must be greater than zero.")
                except ValueError as e:
                    messages.error(request, f"Error: {e}")
                    return render(request, 'addvarient.html', {
                        'product': product,
                        'SIZE_CHOICES': SIZE_CHOICES,
                        'COLOR_CHOICES': COLOR_CHOICES,
    })
               
                existing_variant = Variants.objects.filter(
                    product=product,
                    size=size,
                    color=color
                ).first()

                if existing_variant:
                    existing_variant.stock += stock  
                    existing_variant.price = price 
                    existing_variant.save()
                    variant = existing_variant  
                else:
                    # Create a new variant
                    variant = Variants.objects.create(
                        product=product,
                        size=size,
                        color=color,
                        stock=stock,
                        price=price
                    )

                
                
                    for image_file in uploaded_images:
                        img = VarientImage(varient=variant)  
                        img.image.save(image_file.name, image_file)  
                        img.save()
                        

            return redirect('products')

        return render(request, 'addvarient.html', {'product': product, 'SIZE_CHOICES': SIZE_CHOICES,
            'COLOR_CHOICES': COLOR_CHOICES })
    else:
       
        return redirect('adminlogin') 



# <-edit_variant-> #
@login_required
def edit_variant(request, variant_id):
    if request.user.is_authenticated and request.user.is_superuser:
        variant = get_object_or_404(Variants, pk=variant_id)
        product = variant.product
        existing_images = variant.images.all()  # Get existing images for the variant
        
        SIZE_CHOICES = [
            ('36', '36'), ('38', '38'), ('40', '40'), 
            ('42', '42'), ('43', '43'), ('44', '44'), ('45', '45'),
        ]
        
        COLOR_CHOICES = [
            ('red', 'Red'), ('blue', 'Blue'), ('green', 'Green'),
            ('black', 'Black'), ('white', 'White'), ('yellow', 'Yellow'),
            ('purple', 'Purple'), ('gray', 'Gray'), ('pink', 'Pink'),
            ('orange', 'Orange'),
        ]

        if request.method == 'POST':
            # Collecting lists of sizes, colors, stocks, prices
            sizes = request.POST.getlist('size')
            colors = request.POST.getlist('color')
            stocks = request.POST.getlist('stock')
            prices = request.POST.getlist('price')

            # Collect uploaded images
            uploaded_images = [request.FILES.get(f'image_{i}') for i in range(4)]
            uploaded_images = [img for img in uploaded_images if img]  # Filter out None values

            # Check for valid input and ensure at least 3 images are uploaded
            if len(uploaded_images) + len(existing_images) < 4:
                return render(
                    request,
                    'edit_varient.html',
                    {
                        'variant': variant,
                        'product': product,
                        'existing_images': existing_images,
                        'error': 'Please ensure at least 4 images are present.',
                         'SIZE_CHOICES': SIZE_CHOICES,
                        'COLOR_CHOICES': COLOR_CHOICES,
                    }
                )

            try:
                # Validate size and color
                if sizes[0] not in dict(SIZE_CHOICES) or colors[0] not in dict(COLOR_CHOICES):
                    raise ValueError("Invalid size or color selection.")
                
                # Validate stock
                stock = int(stocks[0])
                if stock < 0:
                    raise ValueError("Stock must be greater than or equal to zero.")
                
                # Validate price
                price = float(prices[0])
                if price <= 0:
                    raise ValueError("Price must be greater than or equal to zero.")
                
                # Update variant attributes
                variant.size = sizes[0]
                variant.color = colors[0]
                variant.stock = stock
                variant.price = price
                variant.save()

                # Handle image uploads and replacements
                for i, img in enumerate(uploaded_images):
                    if i < len(existing_images):
                        # Replace existing images with uploaded ones
                        existing_images[i].image.save(img.name, img)
                    else:
                        # Create new images if more than existing
                        VarientImage.objects.create(variant=variant, image=img)

                messages.success(request, 'Variant updated successfully.')
                return redirect('products')
            
            except ValueError as e:
                messages.error(request, f'Invalid input: {e}')
                return render(
                    request,
                    'edit_varient.html',
                    {
                        'variant': variant,
                        'product': product,
                        'existing_images': existing_images,
                        'error': f'Invalid input: {e}',
                         'SIZE_CHOICES': SIZE_CHOICES,
                         'COLOR_CHOICES': COLOR_CHOICES,
                    }
                )

        # Render the form for editing the variant
        return render(request, 'edit_varient.html', {
            'variant': variant,
            'product': product,
            'existing_images': existing_images,
            'SIZE_CHOICES': SIZE_CHOICES,
            'COLOR_CHOICES': COLOR_CHOICES,
        })
    
    else:
        return redirect('adminlogin')


# <-delete_image-> #

@csrf_exempt



def delete_image(request):
    image_id = request.POST.get('image_id')
    new_image = request.FILES.get('new_image')  

    
    if not image_id or not new_image:
        return JsonResponse({"error": "Image ID and new image must be provided."}, status=400)
    
    
    image = get_object_or_404(VarientImage, id=image_id)
    
    
    image_count = VarientImage.objects.filter(varient=image.varient).count()
    if image_count < 3:
        return JsonResponse({"error": "Cannot replace image. Minimum of 3 images required."}, status=400)
    
    
    image.image = new_image  
    image.save()
    
   
    return JsonResponse({"success": "Cannot replace image. Minimum of 3 images required."}, status=200)


# <-delete_vairent-> #

def delete_variant(request, variant_id):
    if request.user.is_authenticated  and request.user.is_superuser :  
        variant = get_object_or_404(Variants, pk=variant_id)

    
        # Soft delete the variant
        variant.is_delete = True
        variant.save()
        messages.success(request,'Sucessfully deleted')
       
        return redirect(products)
    else:
       
        return redirect('adminlogin') 

def adminOrders(request):
        
        orders = OrderItem.objects.select_related('order', 'variant').prefetch_related('order__user').order_by('-last_updated')
        return render(request, 'ad_orders.html', {'orders': orders})
        
        
def updatestatus(request,id):
    
    if request.POST:
        order_item=get_object_or_404(OrderItem,id=id)
        new_status=request.POST.get('status')
        order_item.status = new_status
        order_item.save(update_stock=False)  
        return redirect('adminorders')
  
    
def offer(request):
    
    offers= Offer.objects.all().order_by('-start_date')
    return render(request,'offer.html', {'offers': offers})

def add_offer(request):
    
    if request.POST:
        form=OfferForm(request.POST)
        if form.is_valid():
            offer=form.save(commit=False)
            offer.created_by = request.user  # Set the creator to the logged-in user
            offer.save()
            messages.success(request, "Offer created successfully!")
            return redirect('offer')  # Replace with the name of your list view URL
    else:
        form = OfferForm()
    
    return render(request, 'add_offer.html', {'form': form})

def edit_offer(request,pk):
    offer = get_object_or_404(Offer, pk=pk)
    
    if request.POST:
        form=OfferForm(request.POST,instance=offer)
        if form.is_valid():
            form.save()
            messages.success(request, "Offer updated successfully!")
            return redirect('offer')
        
    else:
        form = OfferForm(instance=offer)
    
    return render(request, 'edit_offer.html', {'form': form, 'offer': offer})

def toggle_offer_status(request, pk):
    offer = get_object_or_404(Offer, pk=pk)
    offer.is_active = not offer.is_active
    offer.save()
    messages.success(request, f"Offer {'activated' if offer.is_active else 'deactivated'} successfully!")
    return redirect('offer')  

def coupan(request):
    coupan = Coupon.objects.all().order_by('-start_date')
    return render(request,'coupan.html', {'coupan': coupan})
    
def add_coupan(request):
    if request.POST:
        form=CouponForm(request.POST)
        if form.is_valid():
            Coupan=form.save()
            messages.success(request, "Coupan created successfully!")
            return redirect('coupon_list')  # Replace with the name of your list view URL
    else:
        form = CouponForm()
    
    return render(request, 'add_coupan.html', {'form': form})

def edit_coupan(request,pk):
    coupan = get_object_or_404(Offer, pk=pk)
    
    if request.POST:
        form=CouponForm(request.POST ,instance=coupan)
        if form.is_valid():
            form.save()
            messages.success(request, "Coupan edit successfully!")
            return redirect('coupon_list')  # Replace with the name of your list view URL
    else:
        form = CouponForm()
    
    return render(request, 'edit_coupan.html', {'form': form , 'coupan':coupan})

            
def toggle_coupon_status(request, pk):
    coupon = get_object_or_404(Coupon, pk=pk)
    coupon.is_active = not coupon.is_active
    coupon.save()
    messages.success(request, f"Coupon {'activated' if coupon.is_active else 'deactivated'} successfully!")
    return redirect('coupon_list')             
    
    
    
    
    

    