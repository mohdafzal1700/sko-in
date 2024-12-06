from django import forms
from .models import Product, Variants, VarientImage , Category ,Address , Coupon 
import re
from User_side.utils import validate_field
from django.core.exceptions import ValidationError

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'category', 'is_active' ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5, 'cols': 15}),
            'is_active': forms.CheckboxInput(),
        }
             
    def __init__(self, *args, **kwargs):
        super(ProductForm, self).__init__(*args, **kwargs)

        # Filter out deleted categories (assuming `is_delete` is the field marking deletion)
        self.fields['category'].queryset = Category.objects.filter(is_delete=False)
        
        

class VariantForm(forms.ModelForm):
    class Meta:
        model = Variants
        fields = [ 'size', 'color', 'stock', 'price', 'is_delete', 'variant_image']
        widgets = {
            'size': forms.TextInput(attrs={'placeholder': 'Enter size'}),
            'color': forms.TextInput(attrs={'placeholder': 'Enter color'}),
            'stock': forms.NumberInput(attrs={'min': 0}),
            'price': forms.NumberInput(attrs={'min': 0}),
            'is_delete': forms.CheckboxInput(),
        }

class VarientImageForm(forms.ModelForm):
    class Meta:
        model = VarientImage
        fields = ['varient', 'image', 'is_primary']
        widgets = {
            'image': forms.ClearableFileInput(attrs={'multiple': False}),
            'is_primary': forms.CheckboxInput(),
        }

    
class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = [
            'address_line_1',
            'address_line_2',
            'city',
            'state',
            'postal_code',
            'country',
            'address_type',
            'label'
        ]
        widgets = {
            'address_line_1': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter address line 1'}),
            'address_line_2': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter address line 2'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter city'}),
            'state': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter state'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter postal code'}),
            'country': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter country'}),
            'address_type': forms.Select(attrs={'class': 'form-control'}),
            'label': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter label (optional)'}),
        }
        
        
    def clean_address_line_1(self):
        address_line_1 = self.cleaned_data.get('address_line_1')
        return validate_field(address_line_1, "Address line 1")

    def clean_city(self):
        city = self.cleaned_data.get('city')
        return validate_field(city, "City")

    def clean_state(self):
        state = self.cleaned_data.get('state')
        return validate_field(state, "State")

    def clean_country(self):
        country = self.cleaned_data.get('country')
        return validate_field(country, "Country")

    def clean_label(self):
        label = self.cleaned_data.get('label')
        if label:  # Only validate label if it is provided
            return validate_field(label, "Label")
        return label
    
    def clean_postal_code(self):
        postal_code = self.cleaned_data.get('postal_code')

       
        if len(postal_code) != 6 or not postal_code.isdigit():
            raise ValidationError("Postal code must contain exactly 6 digits.")

        
        if postal_code.startswith(" "):
            raise ValidationError("Postal code should not start with a space.")

        
        if postal_code == '0' * len(postal_code):
            raise ValidationError("Postal code cannot be all zeros.")

        return postal_code

from django.utils import timezone
from .models import Offer

class OfferForm(forms.ModelForm):
    class Meta:
        model = Offer
        fields = [
            'offer_type',
            'discount_type',
            'name',
            'description',
            'start_date',
            'end_date',
            'discount_values',
            'product',
            'category',
            'is_active',
        ]
        widgets = {
            'start_date': forms.DateTimeInput(attrs={'class': 'flatpickr-input'}),
            'end_date': forms.DateTimeInput(attrs={'class': 'flatpickr-input'}),
        }

    def __init__(self, *args, **kwargs):
        super(OfferForm, self).__init__(*args, **kwargs)

        # Set form-control class for all fields except CheckboxInput fields
        for field_name, field in self.fields.items():
            if field.widget.__class__.__name__ != 'CheckboxInput':
                field.widget.attrs['class'] = 'form-control'
            else:
                field.widget.attrs['class'] = 'form-check-input'

        # Set date input fields with the specific IDs for Flatpickr
        self.fields['start_date'].widget.attrs.update({
            'id': 'start_date',
            'placeholder': 'Pick a start date'
        })
        self.fields['end_date'].widget.attrs.update({
            'id': 'end_date',
            'placeholder': 'Pick an end date'
        })

        # Exclude products where is_delete=True
        self.fields['product'].queryset = Product.objects.filter(is_delete=False)
        
        # Exclude categories where is_delete=True
        self.fields['category'].queryset = Category.objects.filter(is_delete=False)

    # Add date input formats to match Flatpickr format
    def clean_start_date(self):
        start_date = self.cleaned_data.get('start_date')
        if start_date < timezone.now():
            raise forms.ValidationError("The start date cannot be in the past.")
        return start_date

    def clean_end_date(self):
        end_date = self.cleaned_data.get('end_date')
        start_date = self.cleaned_data.get('start_date')
        if end_date and start_date and end_date <= start_date:
            raise forms.ValidationError("The end date must be after the start date.")
        return end_date
    
    def clean_name(self):
        name = self.cleaned_data.get('name')
        if len(name) < 3:
            raise forms.ValidationError("The name must have at least 3 characters.")
        if name[0] in ['*', '#', '@', '!', '$']:  # Add other special characters as needed
            raise forms.ValidationError("The name cannot start with a special character like * or #.")
        return name

    # Discount Value Validation
    def clean_discount_values(self):
        discount_values = self.cleaned_data.get('discount_values')
        discount_type = self.cleaned_data.get('discount_type')
        
        if discount_values < 0:
            raise ValidationError("Discount value cannot be negative.")

        if discount_type == 'PERCENTAGE':
            if discount_values > 100:
                raise forms.ValidationError("The discount percentage cannot exceed 100%.")
        elif discount_type == 'FIXED':
            if discount_values < 0:
                raise ValidationError("The fixed discount value cannot be negative.")
            if discount_values > 99999 :  # Limit to 5 digits (99999)
                raise forms.ValidationError("The discount value cannot exceed 5 digits for fixed amount.")
        
        return discount_values



class CouponForm(forms.ModelForm):
    class Meta:
        model = Coupon
        fields = ['code', 'discount_type', 'value', 'minimum_purchase_amount', 
                  'maximum_discount', 'start_date', 'end_date', 'usage_limit', 
                   'is_active']
        widgets = {
            'start_date': forms.DateTimeInput(attrs={'class': 'flatpickr-input'}),
            'end_date': forms.DateTimeInput(attrs={'class': 'flatpickr-input'}),
            'applicable_products': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'applicable_categories': forms.SelectMultiple(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Set form-control class for all fields except CheckboxInput fields
        for field_name, field in self.fields.items():
            if field.widget.__class__.__name__ != 'CheckboxInput':
                field.widget.attrs['class'] = 'form-control'
            else:
                field.widget.attrs['class'] = 'form-check-input'

        # Set date input fields with the specific IDs for Flatpickr
        self.fields['start_date'].widget.attrs.update({
            'id': 'start_date',
            'placeholder': 'Pick a start date'
        })
        self.fields['end_date'].widget.attrs.update({
            'id': 'end_date',
            'placeholder': 'Pick an end date'
        })

        # Exclude products where is_delete=True
        

    # Add date input formats to match Flatpickr format
    def clean_start_date(self):
        start_date = self.cleaned_data.get('start_date')
        if start_date and start_date < timezone.now():
            raise ValidationError("The start date cannot be in the past.")
        return start_date

    def clean_end_date(self):
        end_date = self.cleaned_data.get('end_date')
        start_date = self.cleaned_data.get('start_date')
        if end_date and start_date and end_date <= start_date:
            raise ValidationError("The end date must be after the start date.")
        return end_date
    
    def clean_code(self):
        code = self.cleaned_data.get('code')
        if len(code) < 3:
            raise ValidationError("The coupon code must have at least 3 characters.")
        if code[0] in ['*', '#', '@', '!', '$']:  # Add other special characters as needed
            raise ValidationError("The coupon code cannot start with a special character like * or #.")
        return code

    # Discount Value Validation
    def clean_value(self):
        value = self.cleaned_data.get('value')
        discount_type = self.cleaned_data.get('discount_type')

        if discount_type == 'PERCENTAGE':
            if value > 100:
                raise ValidationError("The discount percentage cannot exceed 100%.")
        elif discount_type == 'FIXED':
            if value > 99999:  # Limit to 5 digits (99999)
                raise ValidationError("The discount value cannot exceed 5 digits for fixed amount.")
        
        return value
    
    def clean_minimum_purchase_amount(self):
        minimum_purchase_amount = self.cleaned_data.get('minimum_purchase_amount')
        if minimum_purchase_amount is not None and minimum_purchase_amount < 0:
            raise ValidationError("The minimum purchase amount cannot be negative.")
        return minimum_purchase_amount