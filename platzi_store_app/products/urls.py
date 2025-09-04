from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('', views.products_list_view, name='products_list'),
    path('add/', views.products_add_view, name='products_add'),
    path('<int:pk>/', views.products_detail_view, name='products_detail'),
    path('<int:pk>/update-ajax/', views.products_update_ajax, name='products_update_ajax'),
    path('<int:pk>/delete-ajax/', views.products_delete_ajax, name='products_delete_ajax'),
]