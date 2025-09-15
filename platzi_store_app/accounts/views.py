# accounts/views.py
import requests
import json
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.conf import settings
from .forms import UserRegistrationForm, UserLoginForm

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserSerializer
)

# URL base de tu API (configurable desde settings)
API_BASE_URL = "http://127.0.0.1:8000/api/"

@api_view(['POST'])
@permission_classes([AllowAny])
def register_api(request):
    """Vista API para el registro de nuevos usuarios."""
    if request.method == 'POST':
        serializer = UserRegistrationSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.save()
            token, created = Token.objects.get_or_create(user=user)
            
            response_data = {
                'success': True,
                'message': 'Usuario registrado satisfactoriamente',
                'user': UserSerializer(user).data,
                'token': token.key
            }
            
            return Response(response_data, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'message': 'Error en el registro',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def login_api(request):
    """Vista API para el inicio de sesión de usuarios."""
    if request.method == 'POST':
        serializer = UserLoginSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            user = serializer.validated_data['user']
            login(request, user)
            token, created = Token.objects.get_or_create(user=user)
            
            response_data = {
                'success': True,
                'message': 'Autenticación satisfactoria',
                'user': UserSerializer(user).data,
                'token': token.key
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
        
        return Response({
            'success': False,
            'message': 'Error en la autenticación',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_api(request):
    """Vista API para cerrar sesión."""
    if request.method == 'POST':
        try:
            request.user.auth_token.delete()
            logout(request)
            
            return Response({
                'success': True,
                'message': 'Sesión cerrada exitosamente'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'message': 'Error al cerrar sesión',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_profile_api(request):
    """Vista API para obtener el perfil del usuario actual."""
    if request.method == 'GET':
        serializer = UserSerializer(request.user)
        
        return Response({
            'success': True,
            'user': serializer.data
        }, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([AllowAny])
def check_username_api(request):
    """Vista API para verificar disponibilidad de nombre de usuario."""
    username = request.GET.get('username', '')
    
    if not username:
        return Response({
            'success': False,
            'message': 'Debe proporcionar un nombre de usuario'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    exists = User.objects.filter(username=username).exists()
    
    return Response({
        'success': True,
        'available': not exists,
        'message': 'Nombre de usuario no disponible' if exists else 'Nombre de usuario disponible'
    }, status=status.HTTP_200_OK)

@csrf_protect
@never_cache
def register_view(request):
    """Vista para el registro de usuarios - SIMPLIFICADA"""
    if request.user.is_authenticated:
        messages.info(request, 'Ya tienes una sesión activa.')
        return redirect('products:products_list')  # Corregido el nombre de la URL
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            try:
                # Crear usuario directamente en Django (sin API externa)
                user = User.objects.create_user(
                    username=form.cleaned_data['username'],
                    email=form.cleaned_data['email'],
                    first_name=form.cleaned_data['first_name'],
                    last_name=form.cleaned_data['last_name'],
                    password=form.cleaned_data['password1']
                )
                
                messages.success(
                    request, 
                    f'¡Registro exitoso! Bienvenido {user.first_name}. Tu cuenta ha sido creada correctamente.'
                )
                return redirect('accounts:login')
                
            except Exception as e:
                if 'username' in str(e).lower():
                    form.add_error('username', 'Este nombre de usuario ya existe.')
                elif 'email' in str(e).lower():
                    form.add_error('email', 'Ya existe un usuario con este email.')
                else:
                    form.add_error(None, f'Error al crear el usuario: {str(e)}')
                        
    else:
        form = UserRegistrationForm()
    
    return render(request, 'register.html', {'form': form})

@csrf_protect
@never_cache
def login_view(request):
    """Vista para el login de usuarios - SIMPLIFICADA"""
    if request.user.is_authenticated:
        messages.info(request, 'Ya tienes una sesión activa.')
        return redirect('products:products_list')  # Corregido el nombre de la URL
    
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            
            # Autenticar directamente con Django
            user = authenticate(request, username=username, password=password)
            
            if user and user.is_active:
                login(request, user)
                messages.success(
                    request, 
                    f'¡Bienvenido de nuevo, {user.first_name or user.username}!'
                )
                
                # Redirigir a donde el usuario quería ir originalmente
                next_url = request.GET.get('next', 'products:products_list')  # Corregido
                return redirect(next_url)
            else:
                form.add_error(None, 'Credenciales inválidas. Verifica tu usuario y contraseña.')
                        
    else:
        form = UserLoginForm()
    
    return render(request, 'login.html', {'form': form})

def logout_view(request):
    """Vista para cerrar sesión"""
    username = request.user.username if request.user.is_authenticated else None
    first_name = request.user.first_name if request.user.is_authenticated else None
    
    # Cerrar sesión en Django
    logout(request)
    
    display_name = first_name or username
    if display_name:
        messages.success(request, f'Has cerrado sesión exitosamente, {display_name}. ¡Hasta pronto!')
    else:
        messages.success(request, 'Has cerrado sesión exitosamente.')
    
    return redirect('home')