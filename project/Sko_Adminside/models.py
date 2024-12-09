from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from User_side.utils import  validate_image , validate_field, validate_phone 
from django.utils import timezone
from django.utils.timezone import now
from django.db import transaction
from django.contrib import messages



# Create your models here.

    
class Category(models.Model):
    name=models.CharField(max_length=250)
    is_delete=models.BooleanField(default=False)
    
   
    def delete(self, using = None, keep_parents = False):
        self.is_delete= True
        self.save()
    
    def __str__(self):
        return self.name
    

    

class Product(models.Model):
    name=models.CharField(max_length=230,)
    description=models.TextField()
    category=models.ForeignKey(Category , on_delete=models.CASCADE)
    is_active=models.BooleanField(default=True)
    is_delete=models.BooleanField(default=False)
   
    def __str__(self):
        return self.name
    

    
    def delete(self, using = None, keep_parents = False):
        self.is_delete= True
        self.save()
        
    def get_active_offer(self):
        # First check if there’s a product-specific offer
        product_offer = Offer.objects.filter(
            product=self,
            start_date__lte=now(),
            end_date__gte=now()
        ).first()

        if product_offer:
            return product_offer

        # If no product-specific offer, check category-level offer
        category_offer = Offer.objects.filter(
            category=self.category,
            start_date__lte=now(),
            end_date__gte=now()
        ).first()

        return category_offer

    def has_active_offer(self):
        return self.get_active_offer() is not None


   
 


class Variants(models.Model):
    SIZE_CHOICES = [
        ('36', '36'),
        ('38', '38'),
        ('40', '40'),
        ('42', '42'),
        ('43', '43'),
        ('44', '44'),
        ('45', '45'),
        # Add any other sizes as needed
    ]
    
    COLOR_CHOICES = [
    ('red', 'Red'),
    ('blue', 'Blue'),
    ('green', 'Green'),
    ('black', 'Black'),
    ('white', 'White'),
    ('yellow', 'Yellow'),
    ('purple', 'Purple'),
    ('gray', 'Gray'),
    ('pink', 'Pink'),
    ('orange', 'Orange'),
    # Add any other colors as needed
]
    product = models.ForeignKey(Product, related_name='variants', on_delete=models.CASCADE)
    size = models.CharField(max_length=10,choices=SIZE_CHOICES)  # e.g., '7', '8', '9'
    color = models.CharField(max_length=50,choices=COLOR_CHOICES)  # e.g., 'Black', 'White'
    stock = models.PositiveIntegerField(default=0)  # Quantity in stock
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_delete = models.BooleanField(default=False)
    variant_image = models.ForeignKey(
        'VarientImage', 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL, 
        related_name='products'
    )

    def clean(self):
        """Custom validation for stock and price fields."""
        if self.stock <= 0:
            raise ValidationError("Stock must be greater than zero.")
        if self.price <= 0:
            raise ValidationError("Price must be greater than zero.")
        
        
    def get_discounted_price(self):
        """Calculate the discounted price for this variant based on any active offers."""
        original_price = self.price

        # Product-level offer
        product_offer = Offer.objects.filter(
            offer_type=Offer.PRODUCT_OFFER,
            product=self.product,
            is_active=True
        ).first()
        product_discounted_price = (
            product_offer.apply_discount(original_price) 
            if product_offer and product_offer.is_valid() else original_price
        )
        try:
            product_discounted_price = (
                product_offer.apply_discount(original_price) 
                if product_offer and product_offer.is_valid() else original_price
        )
        except ValidationError as e:
            # If the offer is invalid, use the original price and log the error
            product_discounted_price = original_price
            print(f"Error with product offer: {e}")

        
        

        # Category-level offer
        category_offer = Offer.objects.filter(
            offer_type=Offer.CATEGORY_OFFER,
            category=self.product.category,
            is_active=True
        ).first()
        category_discounted_price = (
            category_offer.apply_discount(original_price) 
            if category_offer and category_offer.is_valid() else original_price
        )
        
        try:
            category_discounted_price = (
                category_offer.apply_discount(original_price) 
                if category_offer and category_offer.is_valid() else original_price
            )
        except ValidationError as e:
            # If the offer is invalid, use the original price and log the error
            category_discounted_price = original_price
            print(f"Error with category offer: {e}")
        
        

        # Return the minimum discounted price available
        return min(product_discounted_price, category_discounted_price)


    def __str__(self):
        return f"{self.product.name} - {self.color} / Size: {self.size}"

    def delete(self, using=None, keep_parents=False):
        """Soft delete: Mark as deleted instead of actually deleting."""
        self.is_delete = True
        self.save()
    
    class Meta:
        unique_together = ('product', 'size', 'color')  # Prevent duplicate variants

   
class VarientImage(models.Model):
    varient =models.ForeignKey(Variants, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='variant_images/')
    is_primary = models.BooleanField(default=False)

    def __str__(self):
       return f"Image for {self.varient.product.name} - {self.varient.color} / Size: {self.varient.size}"




class userprofile(models.Model):
    user=models.OneToOneField(User,related_name='profile',on_delete=models.CASCADE)
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    bio = models.TextField(blank=True, null=True)  # Optional bio field
    mobile = models.CharField(max_length=15, blank=True, null=True , validators=[validate_phone])

    
class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="addresses")
    address_line_1 = models.CharField(max_length=255)
    address_line_2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    address_type = models.CharField(
        max_length=50,
        choices=[
            ('home', 'Home'),
            ('work', 'Work'),
            ('billing', 'Billing'),
            ('shipping', 'Shipping'),
        ],
        default='home'
    )
    label = models.CharField(max_length=50, blank=True, null=True)  # New field for naming
    is_delete = models.BooleanField(default=False)
    is_primary= models.BooleanField(default=False)

    def __str__(self):
        return f"{self.label or self.address_type} address for {self.user.username} {self.is_primary}"
    
    
    def delete(self, using=None, keep_parents=False):
        """Soft delete: Mark as deleted instead of actually deleting."""
        self.is_delete = True
        self.save()




     
class Offer(models.Model):
    PRODUCT_OFFER = 'P'
    CATEGORY_OFFER = 'C'

    OFFER_TYPES = [
        (PRODUCT_OFFER, 'Product Offer'),
        (CATEGORY_OFFER, 'Category Offer'),
    ]
    
    PERCENTAGE_DISCOUNT = 'P'
    FIXED_DISCOUNT = 'F'

    DISCOUNT_TYPES = [
        (PERCENTAGE_DISCOUNT, 'Percentage Discount'),
        (FIXED_DISCOUNT, 'Fixed Discount'),
    ]
    
    
    offer_type=models.CharField(max_length=20,choices=OFFER_TYPES,default=PRODUCT_OFFER)
    discount_type = models.CharField(max_length=1, choices=DISCOUNT_TYPES, default=PERCENTAGE_DISCOUNT)
    name=models.CharField(max_length=255)
    description=models.TextField(blank=True, null=True)
    start_date= models.DateTimeField()
    end_date= models.DateTimeField()
    discount_values=models.DecimalField(max_digits=10, decimal_places=2)
    
    product = models.ForeignKey(Product, null=True, blank=True, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, null=True, blank=True, on_delete=models.CASCADE)
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    
    

    def is_valid(self):
        # Get the current local time (according to the time zone setting)
        now = timezone.localtime(timezone.now())

        # Convert the offer start and end dates to local time (if necessary)
        start_date = timezone.localtime(self.start_date)
        end_date = timezone.localtime(self.end_date)
        
        # print(f"Offer Start Date: {start_date}, End Date: {end_date}, Current Time: {now}")
        
        return self.is_active and start_date <= now <= end_date

        

    
    def apply_discount(self, product_price):
        """Check if the discount is valid for the product's price, then apply the discount."""
        # Check if the offer is valid
        if not self.is_valid():
            raise ValidationError("This offer is no longer valid.")
        
        # Handle the discount logic
        if self.discount_type == self.FIXED_DISCOUNT:
            if self.discount_values > product_price:
                print(f"Fixed discount exceeds product price. Returning original price of {product_price}")
                return product_price
            discount_price = product_price - self.discount_values
        
        elif self.discount_type == self.PERCENTAGE_DISCOUNT:
            if self.discount_values >= 100:
                print(f"Percentage discount cannot be 100% or more. Returning original price of {product_price}")
           
                return product_price
            discount_price = product_price * (1 - self.discount_values / 100)
        
        else:
            discount_price = product_price

        # Ensure the discount doesn't lead to a negative price
        return max(discount_price, 0)
    
    
    def __str__(self):
        return f"{self.name} ({self.get_offer_type_display()}, {self.get_discount_type_display()})"
    
    

class Cart(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE,related_name='cart')
    added_date=models.DateField(default=timezone.now)
    is_active=models.BooleanField(default=False)
    
    def __str__(self):
        return f" Cart for {self.user.username} (Created: {self.added_date})"
    
    
    
    @property
    def total_price(self):
        return sum(item.total_price for item in self.cart_items.all())


class CartItem(models.Model):
    cart=models.ForeignKey(Cart,on_delete=models.CASCADE,related_name='cart_items')
    variant=models.ForeignKey(Variants,on_delete=models.CASCADE,related_name='varient_cart_items')
    quantity=models.PositiveIntegerField()
    
     
    @property
    def total_price(self):
        return self.quantity * self.variant.get_discounted_price()
    
    @property
    def total_official(self):
        return self.quantity * self.variant.price
    
    def __str__(self):
        return f"{self.cart.user.username} - {self.variant.product.name} (Quantity: {self.quantity})"
 
    
class PaymentMethod(models.Model):
    name=models.CharField(max_length=250)
    
    def  __str__(self):
        return self.name        
   
from decimal import Decimal   
class Coupon(models.Model):
    COUPON_TYPES = (
        ('PERCENTAGE', 'Percentage'),
        ('FIXED', 'Fixed Amount'),
        ('FREE_SHIPPING', 'Free Shipping'),
    )
    
    code = models.CharField(max_length=20, unique=True)  # Coupon code
    discount_type = models.CharField(choices=COUPON_TYPES, max_length=15)  # Type of coupon (percentage/fixed/free)
    value = models.DecimalField(max_digits=10, decimal_places=2)  # Discount value
    minimum_purchase_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # Minimum purchase to use coupon
    maximum_discount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    start_date = models.DateTimeField(default=timezone.now)  # Validity start date
    end_date = models.DateTimeField()  # Validity end date
    usage_limit = models.PositiveIntegerField(default=1)  # How many times coupon can be used
    used_count = models.PositiveIntegerField(default=0)  # Track how many times it has been used
    is_active = models.BooleanField(default=True)  # If the coupon is still active
    
   
  
    def __str__(self):
        return self.code

    
    def is_valid(self, total_amount):
        """Check if the coupon is valid based on the total amount."""
        if not self.is_active:
            print(f"Coupon {self.code} is inactive.")
            return False, "Coupon is inactive."
        
        if self.start_date > timezone.now():
            print(f"Coupon {self.code} hasn't started yet.")
            return False, "Coupon has not started yet."
        
        if self.end_date < timezone.now():
            print(f"Coupon {self.code} has expired.")
            return False, "Coupon has expired."
        
        if self.used_count > self.usage_limit-1:
            print(f"Coupon {self.code} usage limit reached. Used count: {self.used_count}")
            return False, "Coupon usage limit exceeded."
        
        if self.minimum_purchase_amount > total_amount:
            print(f"Coupon {self.code} requires a minimum purchase of {self.minimum_purchase_amount}, but total is {total_amount}.")
            return False, "Coupon doesn't meet minimum purchase requirement."
        
        return True, ""


    def can_be_used(self):
        # Check if coupon has been used within the limit
        return self.used_count < self.usage_limit 
    
    def calculate_discount(self, total_amount, shipping_cost=None):
        """Calculate the discount amount based on the coupon type and value."""
        discount = Decimal(0)
        
        if self.discount_type == 'PERCENTAGE':
            discount = total_amount * (self.value / Decimal(100))
        elif self.discount_type == 'FIXED':
            discount = self.value
        elif self.discount_type == 'FREE_SHIPPING' and shipping_cost:
            discount = shipping_cost

        # Apply maximum discount limit if defined
        if self.maximum_discount:
            discount = min(discount, self.maximum_discount)

        return discount 
    
    def increment_usage(self):
        """Increment the used count of the coupon."""
        self.used_count = models.F('used_count') + 1
        self.save(update_fields=['used_count'])
 


from django.db import transaction

class Order(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE,related_name='order')
    added_date=models.DateField(default=timezone.now)
    paymentmethod=models.ForeignKey(PaymentMethod,on_delete=models.SET_NULL,null=True,default=1)  
    total_amount=models.DecimalField(max_digits=10, decimal_places=2)
    shipping_address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True, blank=True)
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True)
    is_paid = models.BooleanField(default=False)
    discount_applied = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    




    def apply_coupon(self):
    
       if self.coupon and not hasattr(self, '_coupon_applied'):
            is_valid, message = self.coupon.is_valid(self.total_amount)
            if not is_valid:
                print(message)  # Log the invalid coupon message
                return False, message 
           
            print(f"Applying coupon: {self.coupon.code}, Current Used Count: {self.coupon.used_count}")
            self.coupon.used_count += 1
            self.coupon.save()
            print(f"Updated Used Count: {self.coupon.used_count}")
            self._coupon_applied = True  # Flag to prevent multiple increments

    def save(self, *args, **kwargs):
        with transaction.atomic():
            self.apply_coupon()  # Apply the coupon if applicable
            super().save(*args, **kwargs)
 
 
class OrderItem(models.Model):
    order=models.ForeignKey(Order,on_delete=models.CASCADE, related_name="order_items")
    variant = models.ForeignKey(Variants, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    product_name = models.CharField(max_length=255)
    status = models.CharField(max_length=50, choices=[
        ("Pending", "Pending"), 
        ("Processing", "Processing"), 
        ("Delivered", "Delivered"),
        ("Cancelled", "Cancelled"),
        ("Returned", "Returned"),
        ("Refunded", "Refunded"),
        ("Return Requested", "Return Requested"),
        ("Return Rejected", "Return Rejected"),
        ("Failed", "Failed")
    ], default="Pending")
    
    cancellation_reason = models.TextField(null=True,blank=True)
    return_reason = models.TextField(null=True,blank=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    def get_total_price(self):
        return self.quantity *  self.variant.get_discounted_price()
    
    def save(self, *args, update_stock=True, **kwargs):
        if update_stock:
            if self.quantity > self.variant.stock:
                raise ValidationError("Not enough stock available.")
            
            if not self.pk:  
                self.variant.stock -= self.quantity
            else: 
                old_quantity = OrderItem.objects.get(pk=self.pk).quantity
                stock_difference = self.quantity - old_quantity
                
                if stock_difference > 0 and stock_difference > self.variant.stock:
                    raise ValidationError("Not enough stock available for the updated quantity.")
                
                self.variant.stock -= stock_difference

            self.variant.save()
        
        super().save(*args, **kwargs)
        
    def delete(self, *args, **kwargs):
      
        if not self.is_delete:  
            self.is_delete = True
            self.variant.stock += self.quantity
            self.variant.save() 

        super().delete(*args, **kwargs)
        

class Wishlist(models.Model):
    user= models.ForeignKey(User,on_delete=models.CASCADE,related_name='wishlists')
    varients=models.ForeignKey(Variants,on_delete=models.CASCADE,related_name='wishlists')
    added_on = models.DateTimeField(auto_now_add=True) 

    def __str__(self):
        return f"{self.user.username} - {self.varients}"

    class Meta:
        unique_together = ('user', 'varients') 
        
        
        

class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.user.username}'s Wallet"

    def credit(self, amount):
        """Add money to the wallet (credit)"""
        # amount = Decimal(amount)
        self.balance += amount
        self.save()

    def debit(self, amount):
        """Deduct money from the wallet (debit)"""
        # amount = Decimal(amount)
        if self.balance >= amount:
            self.balance -= amount
            self.save()
            return True
        else:
            return False
        
class Transaction(models.Model):
    TRANSACTION_TYPE = (
        ('credit', 'Credit'),
        ('debit', 'Debit'),
    )
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE) 
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPE)
    timestamp = models.DateTimeField(auto_now_add=True)
    description = models.TextField()

    def __str__(self):
        return f"Transaction {self.id} by {self.user.username}"
        
