import random
import re
import os
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.core.mail import send_mail


def generate_otp():
    return str(random.randint(10000,99999))

def send_otp(email,otp):
    subject = 'Your OTP Code'
    message = f'Your OTP code is {otp}'
    from_email = os.getenv('EMAIL_HOST_USER')
    recipient_list = [email]
    send_mail(subject, message, from_email, recipient_list)
    
def clean_email(email):
    

    mail_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'

    if not re.fullmatch(mail_regex, email):
        
        raise ValidationError("Invalid email format")
    return True

    
def clean_password(password):
    
    if len(password) < 8:
        raise ValidationError("Password must be at least 8 characters long.")

    if not re.search(r'\d', password):
        raise ValidationError("Password must contain at least one digit.")

    if not re.search(r'[A-Z]', password):
        raise ValidationError("Password must contain at least one uppercase letter.")
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        raise ValidationError("Password must contain at least one special character.")

    return password

from django.core.exceptions import ValidationError

def validate_image(file):
    valid_extensions = ['.png', '.jpg']
    if not any(file.name.endswith(ext) for ext in valid_extensions):
        raise ValidationError("Only image files are allowed (PNG, JPG, JPEG, GIF).")
    
    
def validate_field(value, field_name):
    """
    Utility function to validate fields like address, city, state, country, and label.
    Checks:
    - Minimum 6 characters
    - No digits
    - Only alphabetic characters and spaces
    - Not only spaces
    """
    
    if len(value) < 3:
        raise ValidationError(f"{field_name} must be at least 6 characters long.")
    
    
    if re.search(r'\d', value):
        raise ValidationError(f"{field_name} should not contain any digits.")
    
   
    if not all(c.isalpha() or c.isspace() for c in value):
        raise ValidationError(f"{field_name} should only contain alphabetic characters and spaces.")
    
    
    if value.strip() == "":
        raise ValidationError(f"{field_name} cannot be empty or contain only spaces.")
    
    return value





def validate_data(value):
    if len(value) < 3:
        raise ValidationError("This field must be at least 3 characters long.")
    if re.search(r'\d', value):
        raise ValidationError("This field should not contain any digits.")
    if not all(c.isalpha() or c.isspace() for c in value):
        raise ValidationError("This field should only contain alphabetic characters and spaces.")
    if value.strip() == "":
        raise ValidationError("This field cannot be empty or contain only spaces.")
    
    return value
    

    
def validate_phone(phone):
    
    digits = re.sub(r'\D', '', phone)  

    
    if len(digits) != 10:
        raise ValidationError("Phone number must contain exactly 10 digits.")

    # Ensure phone number is not all zeros
    if digits == "0000000000":
        raise ValidationError("Phone number cannot be all zeros.")

    # Check if the original phone number starts with a space
    if phone.startswith(" "):
        raise ValidationError("Phone number should not start with a space.")
    
    return phone




# def refund_to_wallet( request ,user, amount, product, description):
#     try:
#         from Sko_Adminside.models import Wallet,Transaction
#         # Add the refund amount to the user's wallet
#         wallet = Wallet.objects.get(user=user)
#         wallet.credit(amount)

#         # Create a transaction for the refund
#         Transaction.objects.create(
#              request=request, 
#             wallet=wallet,
#             user=request.user,
#             amount=amount,
#             transaction_type='credit',
#             description=description
#         )
#         messages.success(request, f"₹{amount} has been successfully refunded and added to your wallet.")
#     except Exception as e:
#         messages.error(request, f"An error occurred while refunding to wallet: {str(e)}")