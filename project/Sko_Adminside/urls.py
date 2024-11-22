from django.urls import path
from . import views


urlpatterns = [
    path('adminlogin/',views.adminlogin,name='adminlogin'),
    path('dashboard/',views.dashboard,name='dashboard'),
    path('adminlogout/',views.admin_logout,name='admin_logout'),
    path('customers/', views.customers,name='customers'),
    path('toggle_block_user/<int:user_id>/', views.toggle_block_user, name='toggle_block_user'),
    path('categories/',views.categories,name='category'),
    path('delete_category/<int:pk>/',views.delete_categories,name='delete_category'),
    path('add_category/',views.add_catrgories,name='add_categories'),
    path('edit_category/<int:pk>/', views.edit_categories, name='edit_categories'),
    path('products/',views.products,name='products'),
    path('delete_products/<int:pk>/',views.delete_products,name='delete_products'),
    path('add_product/',views.add_product,name='add_product'),
    path('edit_product/<int:pk>',views.edit_product,name='edit_product'),
    path('searchproduct/',views.searchproduct,name='searchproduct'),
    path('searchCategory/',views.searchCategory,name='searchCategory'),
    path('searchcustomer',views.searchcustomer,name='searchcustomer'),
    path('variant/delete/<int:variant_id>/', views.delete_variant, name='delete_variant'),
    path('variant/edit/<int:variant_id>/',views.edit_variant, name='edit_variant'),
    path('variant/add/<int:product_id>/', views.add_variant, name='add_variant'),
    path('send-image-id/', views.delete_image, name='delete_image'),
    path('adminorders/',views.adminOrders,name='adminorders'),
    path('updatestatus/<int:id>/',views.updatestatus,name='updatestatus'),
    path('offer/',views.offer,name='offer'),
    path('add_offer/',views.add_offer,name='add_offer'),
    path('edit_offer/<int:pk>/',views.edit_offer,name='edit_offer'),
    path('toggle_offer_status/<int:pk>/', views.toggle_offer_status, name='toggle_offer_status'),
    path('coupan/',views.coupan,name='coupon_list'),
    path('add_coupan/',views.add_coupan,name='add_coupon'),
    path('edit_coupan/<int:pk>',views.edit_coupan,name='edit_coupon'),
    path('toggle_coupon_status/<int:pk>/',views.toggle_coupon_status,name='toggle_coupon_status')
]
