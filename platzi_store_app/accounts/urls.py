from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    #Urls de la API de autentificación
    path('api/register/', views.register_api, name='api_register'),
    path('api/login/', views.login_api, name='api_login'),
    path('api/logout/', views.logout_api, name='api_logout'),
    path('api/profile/', views.user_profile_api, name= 'api_profile'),
    path('api/check-username/', views.check_username_api, name='api_check_username'),
]