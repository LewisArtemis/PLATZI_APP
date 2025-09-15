/**
 * Sistema de autenticación para Platzi Store
 * Maneja login, registro y validaciones en tiempo real
 */

// Configuración de la API
const API_BASE_URL = window.location.origin;
const API_ENDPOINTS = {
    login: '/api/login/',
    register: '/api/register/',
    logout: '/api/logout/',
    checkUsername: '/api/check-username/',
    profile: '/api/profile/'
};

// Utilidades para manejo de tokens
const TokenManager = {
    /**
     * Guarda el token en localStorage
     */
    setToken: function(token) {
        localStorage.setItem('authToken', token);
    },
    
    /**
     * Obtiene el token de localStorage
     */
    getToken: function() {
        return localStorage.getItem('authToken');
    },
    
    /**
     * Elimina el token de localStorage
     */
    removeToken: function() {
        localStorage.removeItem('authToken');
    },
    
    /**
     * Verifica si hay un token guardado
     */
    hasToken: function() {
        return this.getToken() !== null;
    }
};

// Utilidades para manejo de UI
const UIHelpers = {
    /**
     * Muestra un mensaje de alerta
     */
    showAlert: function(elementId, message, type = 'danger') {
        const alertElement = document.getElementById(elementId);
        if (alertElement) {
            alertElement.className = `alert alert-${type} alert-dismissible fade show`;
            document.getElementById(elementId + 'Message').textContent = message;
            alertElement.classList.remove('d-none');
            
            // Auto-ocultar después de 5 segundos
            setTimeout(() => {
                alertElement.classList.add('d-none');
            }, 5000);
        }
    },
    
    /**
     * Muestra/oculta spinner de carga
     */
    toggleLoadingState: function(buttonId, isLoading) {
        const button = document.getElementById(buttonId);
        const textSpan = document.getElementById(buttonId + 'Text');
        const spinnerSpan = document.getElementById(buttonId + 'Spinner');
        
        if (button && textSpan && spinnerSpan) {
            button.disabled = isLoading;
            textSpan.classList.toggle('d-none', isLoading);
            spinnerSpan.classList.toggle('d-none', !isLoading);
        }
    },
    
    /**
     * Valida formato de email
     */
    isValidEmail: function(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    },
    
    /**
     * Calcula la fortaleza de la contraseña
     */
    calculatePasswordStrength: function(password) {
        let strength = 0;
        
        if (password.length >= 8) strength += 25;
        if (password.length >= 12) strength += 25;
        if (/[a-z]/.test(password) && /[A-Z]/.test(password)) strength += 25;
        if (/\d/.test(password)) strength += 12.5;
        if (/[^A-Za-z0-9]/.test(password)) strength += 12.5;
        
        return Math.min(strength, 100);
    }
};

// Manejador de Login
const LoginHandler = {
    /**
     * Inicializa los event listeners del formulario de login
     */
    init: function() {
        const loginForm = document.getElementById('loginForm');
        if (!loginForm) return;
        
        // Manejar submit del formulario
        loginForm.addEventListener('submit', this.handleSubmit.bind(this));
        
        // Toggle para mostrar/ocultar contraseña
        const toggleBtn = document.getElementById('toggleLoginPassword');
        if (toggleBtn) {
            toggleBtn.addEventListener('click', this.togglePasswordVisibility);
        }
        
        // Verificar si hay token guardado al cargar la página
        if (TokenManager.hasToken()) {
            this.checkAuthStatus();
        }
    },
    
    /**
     * Maneja el submit del formulario de login
     */
    handleSubmit: async function(e) {
        e.preventDefault();
        
        const form = e.target;
        
        // Validación del formulario
        if (!form.checkValidity()) {
            form.classList.add('was-validated');
            return;
        }
        
        // Obtener datos del formulario
        const formData = new FormData(form);
        const loginData = {
            username: formData.get('username'),
            password: formData.get('password')
        };
        
        // Mostrar estado de carga
        UIHelpers.toggleLoadingState('loginButton', true);
        
        try {
            // Realizar petición de login
            const response = await fetch(API_BASE_URL + API_ENDPOINTS.login, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify(loginData)
            });
            
            const data = await response.json();
            
            if (response.ok && data.success) {
                // Login exitoso
                TokenManager.setToken(data.token);
                
                // Guardar información del usuario
                if (data.user) {
                    localStorage.setItem('user', JSON.stringify(data.user));
                }
                
                // Mostrar mensaje de éxito
                UIHelpers.showAlert('loginAlert', '¡Inicio de sesión exitoso! Redirigiendo...', 'success');
                
                // Redirigir después de 1 segundo
                setTimeout(() => {
                    window.location.href = '/';
                }, 1000);
            } else {
                // Error en login
                const errorMessage = data.message || 'Error en el inicio de sesión';
                UIHelpers.showAlert('loginAlert', errorMessage, 'danger');
            }
        } catch (error) {
            console.error('Error:', error);
            UIHelpers.showAlert('loginAlert', 'Error de conexión. Por favor intenta nuevamente.', 'danger');
        } finally {
            UIHelpers.toggleLoadingState('loginButton', false);
        }
    },
    
    /**
     * Toggle para mostrar/ocultar contraseña
     */
    togglePasswordVisibility: function() {
        const passwordInput = document.getElementById('loginPassword');
        const icon = document.getElementById('toggleLoginIcon');
        
        if (passwordInput.type === 'password') {
            passwordInput.type = 'text';
            icon.className = 'bi bi-eye-slash';
        } else {
            passwordInput.type = 'password';
            icon.className = 'bi bi-eye';
        }
    },
    
    /**
     * Verifica el estado de autenticación
     */
    checkAuthStatus: async function() {
        const token = TokenManager.getToken();
        if (!token) return;
        
        try {
            const response = await fetch(API_BASE_URL + API_ENDPOINTS.profile, {
                headers: {
                    'Authorization': `Token ${token}`
                }
            });
            
            if (!response.ok) {
                // Token inválido, limpiar
                TokenManager.removeToken();
                localStorage.removeItem('user');
            }
        } catch (error) {
            console.error('Error verificando autenticación:', error);
        }
    },
    
    /**
     * Obtiene el token CSRF de Django
     */
    getCSRFToken: function() {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'csrftoken') {
                return value;
            }
        }
        return '';
    }
};

// Manejador de Registro
const RegisterHandler = {
    /**
     * Inicializa los event listeners del formulario de registro
     */
    init: function() {
        const registerForm = document.getElementById('registerForm');
        if (!registerForm) return;
        
        // Manejar submit del formulario
        registerForm.addEventListener('submit', this.handleSubmit.bind(this));
        
        // Verificación de disponibilidad de username
        const checkUsernameBtn = document.getElementById('checkUsernameBtn');
        if (checkUsernameBtn) {
            checkUsernameBtn.addEventListener('click', this.checkUsernameAvailability.bind(this));
        }
        
        // Validación en tiempo real de username
        const usernameInput = document.getElementById('username');
        if (usernameInput) {
            usernameInput.addEventListener('blur', this.checkUsernameAvailability.bind(this));
        }
        
        // Validación de fortaleza de contraseña
        const passwordInput = document.getElementById('password');
        if (passwordInput) {
            passwordInput.addEventListener('input', this.checkPasswordStrength.bind(this));
        }
        
        // Validación de coincidencia de contraseñas
        const password2Input = document.getElementById('password2');
        if (password2Input) {
            password2Input.addEventListener('input', this.checkPasswordMatch.bind(this));
        }
        
        // Toggle para mostrar/ocultar contraseñas
        const togglePassword = document.getElementById('togglePassword');
        if (togglePassword) {
            togglePassword.addEventListener('click', () => this.togglePasswordVisibility('password', 'togglePasswordIcon'));
        }
        
        const togglePassword2 = document.getElementById('togglePassword2');
        if (togglePassword2) {
            togglePassword2.addEventListener('click', () => this.togglePasswordVisibility('password2', 'togglePassword2Icon'));
        }
    },
    
    /**
     * Maneja el submit del formulario de registro
     */
    handleSubmit: async function(e) {
        e.preventDefault();
        
        const form = e.target;
        
        // Validación del formulario
        if (!form.checkValidity()) {
            form.classList.add('was-validated');
            return;
        }
        
        // Verificar que las contraseñas coincidan
        const password = document.getElementById('password').value;
        const password2 = document.getElementById('password2').value;
        
        if (password !== password2) {
            UIHelpers.showAlert('registerAlert', 'Las contraseñas no coinciden', 'danger');
            return;
        }
        
        // Obtener datos del formulario
        const formData = new FormData(form);
        const registerData = {
            username: formData.get('username'),
            email: formData.get('email'),
            password: formData.get('password'),
            password2: formData.get('password2'),
            first_name: formData.get('first_name'),
            last_name: formData.get('last_name')
        };
    }
}