# forms.py

from django import forms
import requests

class ProductForm(forms.Form):
    title = forms.CharField(
        max_length=255, 
        label='Título',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Camisa de algodón'})
    )
    description = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Descripción detallada del producto...'}),
        label='Descripción'
    )
    price = forms.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        label='Precio',
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ej. 29.99'})
    )
    category = forms.ChoiceField(
        label='Categoría',
        widget=forms.Select(attrs={'class': 'form-select'}),
        choices=[]
    )
    image = forms.URLField(
        required=False,
        label='URL de la imagen (opcional)',
        widget=forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://ejemplo.com/imagen.jpg'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            # Obtener las categorías de la API para llenar el ChoiceField
            response = requests.get('https://api.escuelajs.co/api/v1/categories')
            if response.status_code == 200:
                categories_data = response.json()
                # Asegura que las opciones sean tuplas de (id, nombre)
                choices = [(str(cat['id']), cat['name']) for cat in categories_data]
                self.fields['category'].choices = choices
            else:
                self.fields['category'].choices = [('', 'Error al cargar categorías')]
        except requests.exceptions.RequestException:
            self.fields['category'].choices = [('', 'Error al cargar categorías')]