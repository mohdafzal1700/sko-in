from django.urls import path
from . import views

urlpatterns = [
    # User Authentication and Account Management
    path('', views.user_sign, name='user_sign'),
    path('login/', views.user_login, name='user_login'),
    path('otp/', views.otp, name='otp'),
    path('resend_otp/', views.resend_otp, name='resend_otp'),
    path('logout/', views.user_logout, name='user_logout'),

    # Password Recovery and Reset
    path('forget_pass_email/', views.forget_pass_send_otp, name='forget_pass_send_otp'),
    path('pass_otp_validation', views.otp_pass_validation, name='otp_pass_validation'),
    path('reset_password/', views.reset_password, name='reset_password'),

    # Home and Product Pages
    path('home/', views.home, name='home'),
    path('product_list/', views.productlist, name='product_list'),
    path('product_view/<int:pk>/', views.product_view, name='product_view'),
    path('product/search/', views.product_search, name='product_search'),
 
    
    # Category Views
    path('categoryview/<str:category_name>/', views.category_view, name='categoryview'),

    # User Profile Management
    path('Userprofile/', views.Userprofile, name="Userprofile"),
    path('editprofile/', views.editprofile, name='editprofile'),
    
    # Address Management
    path('address/', views.address, name='address'),   
    path('add_address', views.add_address, name='add_address'),
    path('delete_address/<int:pk>/', views.delete_address, name='delete_address'),
    path('edit_address/<int:pk>/', views.edit_address, name='edit_address'),
    path('set_primary_address/', views.set_primary_address, name='set_primary_address'),

    # Password Change
    path('change the password/', views.change_password, name='change_password'),

    # Cart and Checkout
    path('delete_cart/<int:pk>/', views.delete_cart, name='delete_cart'),
    path('cart_view/', views.cart_view, name='cart_view'),
    path('add_to_cart/', views.add_to_cart, name='add_to_cart'),
    path('update-cart-item/', views.update_cart_item, name='update_cart_item'),
    path('checkout/', views.checkout, name='checkout'),
    path('placeorder/', views.placeorder, name="placeorder"),

    # Orders and Order Management
    path('userorders/', views.userorders, name='userorders'),
    path('cancel-order/<int:id>/', views.cancelorder, name='cancelorder'),
    path('return-order/<int:id>/', views.returnorder, name='returnorder'),

    # Wishlist Management
    path('wishlist/', views.wishlist, name='wishlist'),
    path('add_to_wishlist/', views.add_to_wishlist, name='add_to_wishlist'),
    path('delete_wishlist/<int:id>/', views.delete_wishlist, name='delete_wishlist'),

    # Coupon Management in Checkout
    path('apply-coupon-checkout/', views.apply_coupon_checkout, name='apply_coupon_checkout'),
    path('remove_coupon/', views.remove_coupon_from_checkout, name='remove_coupon_from_checkout'),

    # Payment Handling
    path('payment-confirmation/', views.payment_confirmation_view, name='payment_confirmation'),
    path('verify-payment/', views.verify_payment, name='verify_payment'),

    # Wallet Management
    path('wallet/', views.wallet, name='wallet'),
    path('wallet_recharge/', views.wallet_recharge, name='wallet_recharge'),
    path('wallet_recharge_success/', views.wallet_recharge_success, name='wallet_recharge_success'),

    # Variant and Product Details
    path('get_variant_details/<int:variant_id>/', views.get_variant_details, name='get_variant_details'),
    path('download-invoice/<int:order_id>/', views.download_invoice, name='download_invoice'),
]
