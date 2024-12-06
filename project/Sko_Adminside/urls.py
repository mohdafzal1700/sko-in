from django.urls import path
from . import views

urlpatterns = [
    # Admin Authentication
    path('adminlogin/', views.adminlogin, name='adminlogin'),
    path('adminlogout/', views.admin_logout, name='admin_logout'),

    # Admin Dashboard and General Views
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Customer Management
    path('customers/', views.customers, name='customers'),
    path('toggle_block_user/<int:user_id>/', views.toggle_block_user, name='toggle_block_user'),
    path('searchcustomer', views.searchcustomer, name='searchcustomer'),

    # Category Management
    path('categories/', views.categories, name='category'),
    path('delete_category/<int:pk>/', views.delete_categories, name='delete_category'),
    path('add_category/', views.add_catrgories, name='add_categories'),
    path('edit_category/<int:pk>/', views.edit_categories, name='edit_categories'),
    path('searchCategory/', views.searchCategory, name='searchCategory'),

    # Product Management
    path('products/', views.products, name='products'),
    path('delete_products/<int:pk>/', views.delete_products, name='delete_products'),
    path('add_product/', views.add_product, name='add_product'),
    path('edit_product/<int:pk>/', views.edit_product, name='edit_product'),
    path('searchproduct/', views.searchproduct, name='searchproduct'),

    # Variant Management
    path('variant/delete/<int:variant_id>/', views.delete_variant, name='delete_variant'),
    path('variant/edit/<int:variant_id>/', views.edit_variant, name='edit_variant'),
    path('variant/add/<int:product_id>/', views.add_variant, name='add_variant'),

    # Image Management
    path('send-image-id/', views.delete_image, name='delete_image'),

    # Order Management
    path('adminorders/', views.adminOrders, name='adminorders'),
    path('updatestatus/<int:id>/', views.updatestatus, name='updatestatus'),

    # Offer Management
    path('offer/', views.offer, name='offer'),
    path('add_offer/', views.add_offer, name='add_offer'),
    path('edit_offer/<int:pk>/', views.edit_offer, name='edit_offer'),
    path('toggle_offer_status/<int:pk>/', views.toggle_offer_status, name='toggle_offer_status'),

    # Coupon Management
    path('coupons/', views.coupan, name='coupon_list'),
    path('coupons/toggle/<int:pk>/', views.toggle_coupon_status, name='toggle_coupon_status'),
    path('coupons/edit/<int:pk>/', views.edit_coupan, name='edit_coupon'),
    path('coupons/add/', views.add_coupan, name='add_coupon'),

    # Export Data
    path('export/excel/', views.export_to_excel, name='export_to_excel'),
    path('export/pdf/', views.export_to_pdf, name='export_to_pdf'),

    # Sales Reports
    path('sales/', views.sales_report, name='sales_report'),
     path('process-return-request/<int:id>/<str:action>/', views.process_return_request, name='process_return_request'),
     path('refund/',views.refund,name='refund'),
]
