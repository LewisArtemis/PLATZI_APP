from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
import requests
import json
from .forms import ProductForm
from django.contrib.auth.decorators import login_required
from django.db.models import Q

# Create your views here.
base_url = "https://api.escuelajs.co/api/v1/"

def home_view(request):
    """Vista para la página de inicio"""
    return render(request, 'home.html')

def products_list_view(request):
    """
    Vista para mostrar la lista de productos desde la API, con funcionalidad de búsqueda
    por nombre de categoría o nombre de producto.
    """
    products = []
    categories = []
    
    # Obtener las categorías para el dropdown
    try:
        categories_response = requests.get(f"{base_url}categories/")
        if categories_response.status_code == 200:
            categories = categories_response.json()
    except requests.exceptions.RequestException as e:
        messages.error(request, f'Error al cargar categorías: {str(e)}')
    
    # Obtener los parámetros de la URL
    product_title = request.GET.get('product_title')
    category_id = request.GET.get('category_id')  # Cambio: ahora usamos category_id

    try:
        # Búsqueda por nombre de producto
        if product_title:
            # Obtener todos los productos y filtrar por título
            response = requests.get(f"{base_url}products/")
            if response.status_code == 200:
                all_products = response.json()
                # Filtrar productos que contengan el título buscado (case insensitive)
                products = [p for p in all_products if product_title.lower() in p.get('title', '').lower()]
                if not products:
                    messages.warning(request, f"No se encontraron productos con el nombre: '{product_title}'")
                else:
                    messages.success(request, f"Se encontraron {len(products)} productos con '{product_title}'")
            else:
                messages.error(request, f"Error al buscar productos. Código de estado: {response.status_code}")
                
        # Búsqueda por ID de categoría
        elif category_id:
            try:
                category_id_int = int(category_id)
                # Buscar productos por ID de categoría
                products_response = requests.get(f"{base_url}categories/{category_id_int}/products")
                if products_response.status_code == 200:
                    products = products_response.json()
                    # Encontrar el nombre de la categoría seleccionada
                    selected_category = next((cat for cat in categories if cat['id'] == category_id_int), None)
                    category_name = selected_category['name'] if selected_category else 'Desconocida'
                    messages.success(request, f"Mostrando {len(products)} productos de la categoría: '{category_name}'")
                else:
                    messages.error(request, f"Error al buscar productos por categoría. Código de estado: {products_response.status_code}")
            except ValueError:
                messages.error(request, "ID de categoría inválido")

        # Si no hay parámetros de búsqueda, mostrar todos los productos
        else:
            response = requests.get(f"{base_url}products/")
            if response.status_code == 200:
                products = response.json()
            else:
                messages.error(request, f"Error al cargar la lista de productos. Código de estado: {response.status_code}")
    
    except requests.exceptions.RequestException as e:
        messages.error(request, f'Error de conexión con la API: {str(e)}')
    
    # Pasar las categorías y los valores seleccionados al template
    context = {
        'products': products,
        'categories': categories,
        'selected_category_id': category_id,
        'selected_product_title': product_title,
    }
    
    return render(request, 'products/products_list.html', context)


def products_detail_view(request, pk):
    """Vista para mostrar el detalle de un producto específico"""
    try:
        # Hacer la petición a la API para un producto específico
        response = requests.get(f"{base_url}products/{pk}")
        
        if response.status_code == 200:
            product = response.json()
        else:
            product = None
            messages.error(request, 'Producto no encontrado')
    
    except requests.exceptions.RequestException as e:
        product = None
        messages.error(request, f'Error de conexión: {str(e)}')
    
    context = {
        'product': product
    }
    return render(request, 'products/products_detail.html', context)

@login_required(login_url='accounts:login')
def products_add_view(request):
    """Vista para agregar un producto"""
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            title = form.cleaned_data['title']
            description = form.cleaned_data['description']
            category_id = int(form.cleaned_data['category'])
            image = form.cleaned_data['image']

            # Manejar el precio con un bloque try-except
            try:
                price = float(form.cleaned_data['price'])
            except (ValueError, TypeError):
                # Si el precio no es un número válido, asigna un valor por defecto
                price = 0.0

            # Preparar los datos para la API
            new_product_data = {
                "title": title,
                "description": description,
                "price": price,
                "categoryId": category_id,
                "images": [image]
            }

            try:
                # Enviar la petición POST a la API para crear el producto
                response = requests.post(f"{base_url}products/", json=new_product_data)
                
                if response.status_code == 201:
                    messages.success(request, 'Producto agregado exitosamente a la API.')
                    return redirect('products:products_list')
                else:
                    messages.error(request, f'Error al agregar el producto a la API. Código de estado: {response.status_code}')

            except requests.exceptions.RequestException as e:
                messages.error(request, f'Error de conexión con la API: {str(e)}')
    else:
        form = ProductForm()

    return render(request, 'products/products_add.html', {'form': form})


@csrf_exempt
@login_required(login_url='accounts:login')
def products_update_ajax(request, pk):
    """Vista AJAX para actualizar un producto"""
    if request.method == 'GET':
        try:
            # Obtener datos del producto para el modal
            response = requests.get(f"{base_url}products/{pk}")
            if response.status_code == 200:
                product = response.json()
                return JsonResponse({
                    'success': True,
                    'product': product
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Producto no encontrado'
                })
        except requests.exceptions.RequestException as e:
            return JsonResponse({
                'success': False,
                'message': f'Error de conexión: {str(e)}'
            })
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Datos para enviar a la API
            product_data = {
                'title': data.get('title'),
                'description': data.get('description'),
                'price': float(data.get('price', 0)),
                'categoryId': int(data.get('category', 1)),
                'images': [data.get('image', '')]
            }

            # Enviar petición PUT a la API
            response = requests.put(
                f"{base_url}products/{pk}",
                json=product_data,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                updated_product = response.json()
                return JsonResponse({
                    'success': True,
                    'message': 'Producto actualizado exitosamente',
                    'product': updated_product
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Error al actualizar el producto en la API'
                })
        except requests.exceptions.RequestException as e:
            return JsonResponse({
                'success': False,
                'message': f'Error de conexión: {str(e)}'
            })
        except (ValueError, KeyError) as e:
            return JsonResponse({
                'success': False,
                'message': f'Datos inválidos: {str(e)}'
            })


@csrf_exempt
@login_required(login_url='accounts:login')
def products_delete_ajax(request, pk):
    """Vista AJAX para eliminar un producto"""
    if request.method == 'GET':
        try:
            # Obtener datos del producto para mostrar en el modal de confirmación
            response = requests.get(f"{base_url}products/{pk}")
            if response.status_code == 200:
                product = response.json()
                return JsonResponse({
                    'success': True,
                    'product': product
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Producto no encontrado'
                })
        except requests.exceptions.RequestException as e:
            return JsonResponse({
                'success': False,
                'message': f'Error de conexión: {str(e)}'
            })
    
    elif request.method == 'DELETE':
        try:
            # Enviar petición DELETE a la API
            response = requests.delete(f"{base_url}products/{pk}")
            
            if response.status_code == 200:
                return JsonResponse({
                    'success': True,
                    'message': 'Producto eliminado exitosamente'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Error al eliminar el producto de la API'
                })
        except requests.exceptions.RequestException as e:
            return JsonResponse({
                'success': False,
                'message': f'Error de conexión: {str(e)}'
            })