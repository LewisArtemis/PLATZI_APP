from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
import requests
import json
from .forms import ProductForm

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
    
    # Obtener los parámetros de la URL
    product_title = request.GET.get('product_title')
    category_name = request.GET.get('category_name')

    try:
        # Búsqueda por nombre de producto
        if product_title:
            response = requests.get(f"{base_url}products/?title={product_title}")
            if response.status_code == 200:
                products = response.json()
                if not products:
                    messages.warning(request, f"No se encontraron productos con el nombre: '{product_title}'")
            else:
                messages.error(request, f"Error al buscar productos por nombre. Código de estado: {response.status_code}")
                
        # Búsqueda por nombre de categoría
        elif category_name:
            # Primero, buscar el ID de la categoría por su nombre
            category_response = requests.get(f"{base_url}categories/?name={category_name}")
            if category_response.status_code == 200:
                categories = category_response.json()
                if categories:
                    # Suponemos que el primer resultado es el correcto
                    category_id = categories[0]['id']
                    # Ahora, buscar los productos por el ID de la categoría
                    products_response = requests.get(f"{base_url}categories/{category_id}/products")
                    if products_response.status_code == 200:
                        products = products_response.json()
                        messages.success(request, f"Mostrando productos de la categoría: '{category_name}'")
                    else:
                        messages.error(request, f"Error al buscar productos por categoría. Código de estado: {products_response.status_code}")
                else:
                    messages.warning(request, f"No se encontró una categoría con el nombre: '{category_name}'")
            else:
                messages.error(request, f"Error al buscar la categoría por nombre. Código de estado: {category_response.status_code}")

        # Si no hay parámetros de búsqueda, mostrar todos los productos
        else:
            response = requests.get(f"{base_url}products/")
            if response.status_code == 200:
                products = response.json()
            else:
                messages.error(request, f"Error al cargar la lista de productos. Código de estado: {response.status_code}")
    
    except requests.exceptions.RequestException as e:
        messages.error(request, f'Error de conexión con la API: {str(e)}')
    
    return render(request, 'products/products_list.html', {'products': products})


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