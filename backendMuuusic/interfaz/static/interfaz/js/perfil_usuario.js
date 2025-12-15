document.addEventListener('DOMContentLoaded', function() {
    
    // ======================================================
    // 1. LÓGICA DE MODALES (Editar Perfil & Solicitar Artista)
    // ======================================================
    
    function setupModal(modalId, btnOpenId, btnCloseId, btnCancelId) {
        const modal = document.getElementById(modalId);
        const btnOpen = document.getElementById(btnOpenId);
        const btnClose = document.getElementById(btnCloseId);
        const btnCancel = document.getElementById(btnCancelId);

        if (btnOpen) {
            btnOpen.addEventListener('click', (e) => {
                e.preventDefault();
                modal.classList.add('active');
            });
        }

        const closeModal = () => {
            if(modal) modal.classList.remove('active');
        };

        if (btnClose) btnClose.addEventListener('click', closeModal);
        if (btnCancel) btnCancel.addEventListener('click', closeModal);
        
        if (modal) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) closeModal();
            });
        }
    }

    // Configurar los dos modales
    setupModal('editModal', 'btnEditarPerfil', 'closeEditModal', 'cancelarEdicion');
    setupModal('artistModal', 'btnOpenArtistModal', 'closeArtistModal', 'cancelarArtista');


    // ======================================================
    // 2. BUSCADOR DE CANCIÓN (ANTHEM)
    // ======================================================
    
    // Obtenemos los datos pasados desde el HTML
    const catalogo = window.perfilData ? window.perfilData.catalogoCanciones : [];
    
    const inputSearch = document.getElementById('searchAnthemInput');
    const inputId = document.getElementById('anthemIdInput');
    const resultsBox = document.getElementById('anthemResults');

    if (inputSearch && resultsBox) {
        
        inputSearch.addEventListener('input', function() {
            const texto = this.value.toLowerCase();
            resultsBox.innerHTML = '';

            if (texto.length < 1) {
                resultsBox.classList.remove('active');
                return;
            }

            const coincidencias = catalogo.filter(c => 
                c.titulo.toLowerCase().includes(texto) || 
                c.artista.toLowerCase().includes(texto)
            ).slice(0, 10);

            if (coincidencias.length > 0) {
                resultsBox.classList.add('active');
                
                coincidencias.forEach(c => {
                    const div = document.createElement('div');
                    div.className = 'result-item';
                    div.innerHTML = `<strong>${c.titulo}</strong><small>${c.artista}</small>`;
                    
                    div.addEventListener('click', function() {
                        inputSearch.value = c.titulo;
                        inputId.value = c.id;
                        resultsBox.classList.remove('active');
                    });
                    
                    resultsBox.appendChild(div);
                });
            } else {
                resultsBox.classList.remove('active');
            }
        });

        // Cerrar lista al hacer click fuera
        document.addEventListener('click', function(e) {
            if (!inputSearch.contains(e.target) && !resultsBox.contains(e.target)) {
                resultsBox.classList.remove('active');
            }
        });
    }

    // Función para limpiar selección
    window.limpiarSeleccionAnthem = function() {
        if (inputSearch) inputSearch.value = '';
        if (inputId) inputId.value = '';
    };

    console.log('✅ JS de Perfil cargado');
});

// ======================================================
// 3. FUNCIONES GLOBALES (Fuera del DOMContentLoaded)
// ======================================================
// Necesarias para que los botones onclick="..." del HTML las encuentren

// A. COMPARTIR
window.compartirCancion = function(cancionId) {
    const url = window.location.origin + '/cancion/' + cancionId + '/compartir/';
    
    if (navigator.share) {
        navigator.share({
            title: 'MuuuSica',
            text: 'Escucha esta canción',
            url: url
        }).catch(err => copiarAlPortapapeles(url));
    } else {
        copiarAlPortapapeles(url);
    }
};

function copiarAlPortapapeles(texto) {
    navigator.clipboard.writeText(texto).then(() => {
        if(typeof showToast === 'function') showToast('Enlace copiado 📋');
        else alert('Enlace copiado');
    }).catch(() => {
        console.error('Error al copiar');
    });
}

// B. REPRODUCIR (Wrapper de seguridad)
// Llama a la función del reproductor global si existe
if (typeof window.reproducirCancion === 'undefined') {
    window.reproducirCancion = function(id) {
        console.error('El reproductor global no está cargado.');
        if(typeof showToast === 'function') showToast('Reproductor no listo', 'error');
    };
}