
// ====================
// CONFIGURACIÓN INICIAL
// ====================

// IMPORTANTE: Reemplaza estos valores con tus credenciales de EmailJS
const EMAIL_PUBLIC_KEY = "0zri3Dlk3nYr8r92J";  // Ejemplo: "user_abc123xyz"
const EMAIL_SERVICE_ID = "service_1u89fni";  // Ejemplo: "service_gmail"
const EMAIL_TEMPLATE_ID = "template_cdhq3t9"; // Ejemplo: "template_verification"

// Inicializar EmailJS
(function() {
    console.log("Inicializando EmailJS...");
    emailjs.init(EMAIL_PUBLIC_KEY);
    console.log("EmailJS inicializado correctamente");
})();

// Variables globales
let codigoGenerado = '';
let datosUsuario = {};

// ====================
// EVENTO PRINCIPAL DEL FORMULARIO
// ====================

document.addEventListener('DOMContentLoaded', function() {
    console.log("DOM cargado, configurando eventos...");
    
    const form = document.getElementById('registroForm');
    if (!form) {
        console.error("ERROR: No se encontró el formulario con id 'registroForm'");
        return;
    }
    
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        console.log("Formulario enviado");
        
        // Obtener los datos del formulario
        const name = document.getElementById('name').value.trim();
        const email = document.getElementById('email').value.trim();
        const username = document.getElementById('username').value.trim();
        const password = document.getElementById('password').value;
        
        console.log("Datos del formulario:", { name, email, username });
        
        // Validaciones básicas
        if (name.length < 3) {
            alert('El nombre debe tener al menos 3 caracteres');
            return;
        }
        
        if (username.length < 4) {
            alert('El nombre de usuario debe tener al menos 4 caracteres');
            return;
        }
        
        if (password.length < 6) {
            alert('La contraseña debe tener al menos 6 caracteres');
            return;
        }
        
        // Validar formato de email
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(email)) {
            alert('Por favor ingresa un email válido');
            return;
        }
        
        // Guardar datos del usuario temporalmente
        datosUsuario = {
            name: name,
            email: email,
            username: username,
            password: password
        };
        
        // Generar código de 6 dígitos
        codigoGenerado = Math.floor(100000 + Math.random() * 900000).toString();
        console.log("Código generado:", codigoGenerado);
        
        // Mostrar email en el modal
        document.getElementById('userEmail').textContent = email;
        
        // Enviar email con el código
        enviarCodigoEmail(email, name, codigoGenerado);
    });
});

// ====================
// FUNCIÓN PARA ENVIAR EMAIL
// ====================

function enviarCodigoEmail(email, nombre, codigo) {
    console.log("Intentando enviar email a:", email);
    
    // Deshabilitar el botón de registro mientras se envía
    const submitBtn = document.getElementById('submitBtn');
    submitBtn.disabled = true;
    submitBtn.value = 'Enviando código...';
    
    // Verificar que EmailJS esté disponible
    if (typeof emailjs === 'undefined') {
        console.error("ERROR: EmailJS no está cargado");
        alert('Error: El servicio de email no está disponible. Por favor recarga la página.');
        submitBtn.disabled = false;
        submitBtn.value = 'Registrarse';
        return;
    }
    
    // Parámetros para el template de EmailJS
    const templateParams = {
        email: email,
        name: nombre,
        code: codigo,
        from_name: 'Muuviews'
    };
    
    console.log("Enviando email con parámetros:", templateParams);
    
    // Enviar email usando EmailJS
    emailjs.send(EMAIL_SERVICE_ID, EMAIL_TEMPLATE_ID, templateParams)
        .then(function(response) {
            console.log('✅ Email enviado exitosamente:', response.status, response.text);
            alert('¡Código enviado! Revisa tu email (incluyendo spam)');
            
            // Mostrar modal de verificación
            mostrarModal();
            
            submitBtn.disabled = false;
            submitBtn.value = 'Registrarse';
        })
        .catch(function(error) {
            console.error('❌ Error al enviar email:', error);
            alert('Error al enviar el código de verificación. Error: ' + JSON.stringify(error));
            submitBtn.disabled = false;
            submitBtn.value = 'Registrarse';
        });
}

// ====================
// FUNCIONES DEL MODAL
// ====================

function mostrarModal() {
    console.log("Mostrando modal...");
    const modal = document.getElementById('verificationModal');
    if (modal) {
        modal.style.display = 'flex';
        console.log("Modal mostrado");
    } else {
        console.error("ERROR: No se encontró el modal con id 'verificationModal'");
    }
}

function closeModal() {
    console.log("Cerrando modal...");
    const modal = document.getElementById('verificationModal');
    if (modal) {
        modal.style.display = 'none';
    }
    document.getElementById('verificationCode').value = '';
    document.getElementById('messageDiv').innerHTML = '';
    document.getElementById('messageDiv').style.display = 'none';
}

// ====================
// VERIFICACIÓN DEL CÓDIGO
// ====================

function verifyCode() {
    console.log("Verificando código...");
    const codigoIngresado = document.getElementById('verificationCode').value.trim();
    
    console.log("Código ingresado:", codigoIngresado);
    console.log("Código esperado:", codigoGenerado);
    
    if (codigoIngresado.length !== 6) {
        mostrarMensajeModal('Por favor ingresa los 6 dígitos', 'error');
        return;
    }
    
    if (codigoIngresado === codigoGenerado) {
        console.log("✅ Código correcto");
        mostrarMensajeModal('Código correcto. Registrando usuario...', 'success');
        // Código correcto - Registrar usuario en la base de datos
        setTimeout(() => {
            registrarUsuario();
        }, 1000);
    } else {
        console.log("❌ Código incorrecto");
        mostrarMensajeModal('Código incorrecto. Verifica e intenta de nuevo.', 'error');
        document.getElementById('verificationCode').value = '';
    }
}

// ====================
// REGISTRO EN BASE DE DATOS
// ====================

function registrarUsuario() {
    console.log("Registrando usuario en base de datos...");
    
    // Deshabilitar botón de verificar
    const verifyBtn = document.getElementById('verifyBtn');
    verifyBtn.disabled = true;
    verifyBtn.textContent = 'Registrando...';
    
    // Obtener el token CSRF
    const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    
    console.log("Datos a enviar:", datosUsuario);
    
    // Enviar datos al servidor
    fetch('/guardar-usuario/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken
        },
        body: JSON.stringify(datosUsuario)
    })
    .then(response => {
        console.log("Respuesta del servidor:", response.status);
        return response.json();
    })
    .then(data => {
        console.log("Datos recibidos:", data);
        if (data.success) {
            mostrarMensajeModal('¡Registro exitoso! Redirigiendo al login...', 'success');
            setTimeout(() => {
                window.location.href = '/';
            }, 2000);
        } else {
            mostrarMensajeModal(data.message, 'error');
            verifyBtn.disabled = false;
            verifyBtn.textContent = 'Verificar';
        }
    })
    .catch(error => {
        console.error('Error al registrar:', error);
        mostrarMensajeModal('Error al registrar usuario. Intenta nuevamente.', 'error');
        verifyBtn.disabled = false;
        verifyBtn.textContent = 'Verificar';
    });
}

// ====================
// FUNCIONES DE MENSAJES
// ====================

function mostrarMensajeModal(mensaje, tipo) {
    const messageDiv = document.getElementById('messageDiv');
    messageDiv.textContent = mensaje;
    messageDiv.className = tipo === 'error' ? 'error-message' : 'success-message';
    messageDiv.style.display = 'block';
    
    if (tipo === 'error') {
        setTimeout(() => {
            messageDiv.style.display = 'none';
        }, 3000);
    }
}

// ====================
// VALIDACIÓN DE INPUT
// ====================

// Permitir solo números en el input de verificación
document.addEventListener('DOMContentLoaded', function() {
    const verificationInput = document.getElementById('verificationCode');
    if (verificationInput) {
        verificationInput.addEventListener('input', function(e) {
            this.value = this.value.replace(/[^0-9]/g, '');
        });
    }
});
