(function() {
    
    var shareUrl = '{{ share_url }}';
    var songTitle = '{{ cancion.titulo|escapejs }}';
    var artistName = '{{ artista|escapejs }}';
    var qrGenerated = false;
    
    // ========== COMPARTIR EN REDES ==========
    window.compartirWhatsApp = function() {
        var text = '🎵 Escucha "' + songTitle + '" de ' + artistName + ' en MuuuSica: ' + shareUrl;
        window.open('https://wa.me/?text=' + encodeURIComponent(text), '_blank');
    };
    
    window.compartirTwitter = function() {
        var text = '🎵 Escuchando "' + songTitle + '" de ' + artistName + ' en @MuuuSica';
        window.open('https://twitter.com/intent/tweet?text=' + encodeURIComponent(text) + '&url=' + encodeURIComponent(shareUrl), '_blank');
    };
    
    window.compartirFacebook = function() {
        window.open('https://www.facebook.com/sharer/sharer.php?u=' + encodeURIComponent(shareUrl), '_blank');
    };
    
    window.copiarEnlace = function() {
        var input = document.getElementById('shareUrl');
        input.select();
        
        if (navigator.clipboard) {
            navigator.clipboard.writeText(shareUrl).then(function() {
                mostrarMensaje('¡Enlace copiado!');
            });
        } else {
            document.execCommand('copy');
            mostrarMensaje('¡Enlace copiado!');
        }
    };
    
    // ========== QR CODE ==========
    window.toggleQR = function() {
        var container = document.getElementById('qrContainer');
        container.classList.toggle('active');
        
        if (!qrGenerated && container.classList.contains('active')) {
            new QRCode(document.getElementById('qrCode'), {
                text: shareUrl,
                width: 150,
                height: 150,
                colorDark: '#000000',
                colorLight: '#ffffff'
            });
            qrGenerated = true;
        }
    };
    
    // ========== MOSTRAR MENSAJE ==========
    function mostrarMensaje(msg) {
        if (typeof showToast === 'function') {
            showToast(msg, 'success');
        } else {
            // Fallback toast
            var toast = document.createElement('div');
            toast.style.cssText = 'position:fixed;bottom:120px;left:50%;transform:translateX(-50%);background:#333;color:white;padding:12px 24px;border-radius:8px;z-index:9999;';
            toast.textContent = msg;
            document.body.appendChild(toast);
            setTimeout(function() { toast.remove(); }, 3000);
        }
    }
    
    console.log('✅ Página de compartir cargada');
    
})();