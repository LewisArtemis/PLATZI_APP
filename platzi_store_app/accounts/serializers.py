from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import authenticate


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer para el registro de nuevos usuarios.
    Valida y crea un nuevo usuario en el sistema.
    """
    # Campo adicional para confirmar la contraseña
    password2 = serializers.CharField(
        style={'input_type': 'password'}, 
        write_only=True,
        label='Confirmar contraseña'
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2', 'first_name', 'last_name']
        extra_kwargs = {
            'password': {
                'write_only': True,
                'style': {'input_type': 'password'}
            },
            'email': {'required': True}
        }
    
    def validate(self, attrs):
        """
        Valida que las contraseñas coincidan y cumplan los requisitos mínimos.
        """
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({
                'password': 'Las contraseñas no coinciden'
            })
        
        # Validación de longitud mínima de contraseña
        if len(attrs['password']) < 8:
            raise serializers.ValidationError({
                'password': 'La contraseña debe tener al menos 8 caracteres'
            })
        
        return attrs
    
    def validate_email(self, value):
        """
        Valida que el email no esté ya registrado en el sistema.
        """
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                'Ya existe un usuario con este correo electrónico'
            )
        return value
    
    def create(self, validated_data):
        """
        Crea un nuevo usuario con los datos validados.
        """
        # Removemos password2 ya que no es parte del modelo User
        validated_data.pop('password2')
        
        # Creamos el usuario usando el método create_user para hashear la contraseña
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        
        return user


class UserLoginSerializer(serializers.Serializer):
    """
    Serializer para el inicio de sesión de usuarios.
    Valida las credenciales y autentica al usuario.
    """
    username = serializers.CharField(
        max_length=255,
        help_text='Nombre de usuario para iniciar sesión'
    )
    password = serializers.CharField(
        style={'input_type': 'password'},
        write_only=True,
        help_text='Contraseña del usuario'
    )
    
    def validate(self, attrs):
        """
        Valida las credenciales del usuario.
        """
        username = attrs.get('username')
        password = attrs.get('password')
        
        if username and password:
            # Intentamos autenticar al usuario
            user = authenticate(
                request=self.context.get('request'),
                username=username,
                password=password
            )
            
            if not user:
                # Si la autenticación falla, lanzamos un error
                raise serializers.ValidationError(
                    'Credenciales incorrectas. Por favor, verifica tu usuario y contraseña.',
                    code='authentication'
                )
            
            if not user.is_active:
                # Verificamos que el usuario esté activo
                raise serializers.ValidationError(
                    'Esta cuenta está desactivada.',
                    code='inactive'
                )
            
            # Guardamos el usuario autenticado en los datos validados
            attrs['user'] = user
            return attrs
        else:
            # Si faltan campos requeridos
            raise serializers.ValidationError(
                'Debe incluir usuario y contraseña.',
                code='required'
            )


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer para mostrar información del usuario.
    Se usa para devolver datos del usuario después del login o registro.
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'date_joined', 'is_active']
        read_only_fields = ['id', 'date_joined', 'is_active']