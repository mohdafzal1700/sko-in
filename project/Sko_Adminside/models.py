from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from User_side.utils import  validate_image , validate_field, validate_phone 
from django.utils import timezone




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
    
    
    Offer_type=models.CharField(max_length=20,choices=OFFER_TYPES,default=PRODUCT_OFFER)
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
    
    
    def  is_valid(self):
        now=timezone.now()
        return self.is_active and self.start_date <= now <= self.end_date
    
    def apply_discount(self, price):
        """Apply discount to a given price."""
        if self.discount_type == self.PERCENTAGE_DISCOUNT:
            return price * (1 - self.discount_values / 100)
        elif self.discount_type == self.FIXED_DISCOUNT:
            return price - self.discount_values
        return price  
    
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
    
    def get_discounted_price(self):
        """Calculate the discounted price for this cart item."""
        original_price = self.variant.price
        
        
        product_offer=Offer.objects.filter(
            offer_type=Offer.PRODUCT_OFFER,
            product=self.variant.product,
            is_active=True
        ).first()
        product_discounted_price = product_offer.apply_discount(original_price) if product_offer and product_offer.is_valid() else original_price
        
        category_offer=Offer.objects.filter(
            offer_type=Offer.CATEGORY_OFFER,
            category=self.variant.product.category,
            is_active=True
        ).first()
        
        category_discounted_price = category_offer.apply_discount(original_price) if category_offer and category_offer.is_valid() else original_price
    
        return min(product_discounted_price, category_discounted_price)   
    
     
    @property
    def total_price(self):
        return self.quantity * self.get_discounted_price()
    
    def __str__(self):
        return f"{self.cart.user.username} - {self.variant.product.name} (Quantity: {self.quantity})"
 
    
class PaymentMethod(models.Model):
    name=models.CharField(max_length=250)
    
    def  __str__(self):
        return self.name        
   
   
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

    def is_valid(self):
        # Check if coupon is active and within date range
        return self.is_active and self.start_date <= timezone.now() <= self.end_date

    def can_be_used(self):
        # Check if coupon has been used within the limit
        return self.used_count < self.usage_limit   
 

class Order(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE,related_name='order')
    added_date=models.DateField(default=timezone.now)
    paymentmethod=models.ForeignKey(PaymentMethod,on_delete=models.SET_NULL,null=True,default=1)  
    total_amount=models.DecimalField(max_digits=10, decimal_places=2)
    shipping_address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True, blank=True)
    # coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True)
    
    
    def __str__(self):
        return f"Order {self.id} - {self.user.username}"
    
    def apply_coupon(self):
        """Calculate discount and apply coupon if valid."""
        if self.coupon and self.coupon.is_valid():
            # Check if order qualifies for coupon
            if self.total_amount >= self.coupon.minimum_purchase_amount and self.coupon.can_be_used():
                discount = 0
                if self.coupon.discount_type == 'PERCENTAGE':
                    discount = self.total_amount * (self.coupon.value / 100)
                elif self.coupon.discount_type == 'FIXED':
                    discount = self.coupon.value
                elif self.coupon.discount_type == 'FREE_SHIPPING':
                    discount = self.shipping_cost  # assuming shipping cost is defined elsewhere

                # Apply the maximum discount limit, if defined
                if self.coupon.maximum_discount:
                    discount = min(discount, self.coupon.maximum_discount)
                
                # Apply the discount but ensure total_amount doesn't go negative
                self.total_amount -= min(discount, self.total_amount)
                self.coupon.used_count += 1  # Increment used count
                self.coupon.save()
            else:
                raise ValidationError("Coupon conditions are not met.")
        else:
            raise ValidationError("Coupon is not valid.")

    def save(self, *args, **kwargs):
        self.apply_coupon()  # Apply coupon before saving
        super().save(*args, **kwargs)
    
class OrderItem(models.Model):
    order=models.ForeignKey(Order,on_delete=models.CASCADE, related_name="order_items")
    variant = models.ForeignKey(Variants, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    product_name = models.CharField(max_length=255)
    status = models.CharField(max_length=50, choices=[
        ("Pending", "Pending"), 
        ("Delivered", "Delivered"),
        ("Cancelled", "Cancelled"),
        ("Returned", "Returned"),
        ("Refunded", "Refunded"),
        ("Failed", "Failed")
    ], default="Pending")
    
    cancellation_reason = models.TextField(null=True,blank=True)
    return_reason = models.TextField(null=True,blank=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    def get_total_price(self):
        return self.price * self.quantity
    
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
        
