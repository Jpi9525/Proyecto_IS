(function () {
    'use strict';

    // ============================================================
    // UTILIDADES
    // ============================================================
    function getCSRFToken() {
        var input = document.querySelector('[name=csrfmiddlewaretoken]');
        return input ? input.value : '';
    }

    function escapeHtml(text) {
        var div = document.createElement('div');
        div.textContent = text || '';
        return div.innerHTML;
    }

    // Cerrar todos los dropdowns
    function cerrarTodosDropdowns() {
        document.querySelectorAll('.card-dropdown.show').forEach(function(d) {
            d.classList.remove('show');
        });
    }

    // ============================================================
    // DELEGACIÓN DE EVENTOS
    // ============================================================
    document.addEventListener('click', function(e) {
        
        // ========== MENÚ 3 PUNTOS ==========
        if (e.target.closest('.card-menu-btn')) {
            e.stopPropagation();
            var btn = e.target.closest('.card-menu-btn');
            var card = btn.closest('.song-card');
            var dropdown = card.querySelector('.card-dropdown');
            
            // Cerrar otros dropdowns
            document.querySelectorAll('.card-dropdown.show').forEach(function(d) {
                if (d !== dropdown) d.classList.remove('show');
            });
            
            // Toggle este dropdown
            dropdown.classList.toggle('show');
            return;
        }

        // ========== CERRAR DROPDOWN AL HACER CLIC FUERA ==========
        if (!e.target.closest('.card-dropdown')) {
            cerrarTodosDropdowns();
        }

        // ========== PLAY ==========
        if (e.target.closest('.play-btn, .action-play')) {
            e.stopPropagation();
            var card = e.target.closest('.song-card');
            if (card && typeof window.reproducirCancion === 'function') {
                window.reproducirCancion(card.dataset.id);
            }
            return;
        }

        // ========== FAVORITO ==========
        if (e.target.closest('.favorito-btn')) {
            e.stopPropagation();
            var btn = e.target.closest('.favorito-btn');
            var card = btn.closest('.song-card');
            if (!card) return;

            var cancionId = card.dataset.id;
            var icon = btn.querySelector('i');
            var estabaLikeado = btn.classList.contains('liked');

            // Cambio visual inmediato
            if (estabaLikeado) {
                btn.classList.remove('liked');
                if (icon) { icon.classList.remove('fa-solid'); icon.classList.add('fa-regular'); }
            } else {
                btn.classList.add('liked');
                if (icon) { icon.classList.remove('fa-regular'); icon.classList.add('fa-solid'); }
            }

            fetch('/api/favorito/toggle/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCSRFToken() },
                body: JSON.stringify({ cancion_id: cancionId })
            })
            .then(function(r) { return r.json(); })
            .then(function(data) {
                if (data.success) {
                    if (typeof showToast === 'function') showToast(data.message);
                } else {
                    revertirFavorito(btn, icon, estabaLikeado);
                    if (typeof showToast === 'function') showToast(data.message || 'Error', 'error');
                }
            })
            .catch(function() {
                revertirFavorito(btn, icon, estabaLikeado);
                if (typeof showToast === 'function') showToast('Error de conexión', 'error');
            });
            return;
        }

        // ========== AÑADIR A COLA ==========
        if (e.target.closest('.add-queue-btn')) {
            e.stopPropagation();
            var card = e.target.closest('.song-card');
            if (card && typeof window.agregarACola === 'function') {
                window.agregarACola(card.dataset.id);
            }
            return;
        }

        // ========== AÑADIR A PLAYLIST (desde dropdown) ==========
        if (e.target.closest('.add-playlist-btn')) {
            e.stopPropagation();
            var card = e.target.closest('.song-card');
            if (!card) return;
            cerrarTodosDropdowns();
            abrirModalPlaylist(card.dataset.id);
            return;
        }

        // ========== DESCARGAR OFFLINE (desde dropdown) ==========
        if (e.target.closest('.download-btn')) {
            e.stopPropagation();
            var item = e.target.closest('.download-btn');
            var card = item.closest('.song-card');
            if (!card) return;

            var cancionId = card.dataset.id;
            var icon = item.querySelector('i');
            var span = item.querySelector('span');
            var estabaDescargado = card.dataset.downloaded === 'true';

            // Cambio visual inmediato
            if (estabaDescargado) {
                card.dataset.downloaded = 'false';
                if (icon) { icon.classList.remove('fa-check'); icon.classList.add('fa-download'); }
                if (span) span.textContent = 'Descargar offline';
            } else {
                card.dataset.downloaded = 'true';
                if (icon) { icon.classList.remove('fa-download'); icon.classList.add('fa-check'); }
                if (span) span.textContent = 'Quitar de descargas';
            }

            cerrarTodosDropdowns();

            fetch('/api/descargar/cancion/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCSRFToken() },
                body: JSON.stringify({ cancion_id: cancionId })
            })
            .then(function(r) { return r.json(); })
            .then(function(data) {
                if (data.success) {
                    if (typeof showToast === 'function') showToast(data.message);
                } else {
                    // Revertir
                    revertirDescarga(card, icon, span, estabaDescargado);
                    if (typeof showToast === 'function') showToast(data.message || 'Error', 'error');
                }
            })
            .catch(function() {
                revertirDescarga(card, icon, span, estabaDescargado);
                if (typeof showToast === 'function') showToast('Error de conexión', 'error');
            });
            return;
        }

        // ========== RESEÑAS (desde dropdown) ==========
        if (e.target.closest('.resena-btn')) {
            e.stopPropagation();
            var card = e.target.closest('.song-card');
            if (!card) return;
            cerrarTodosDropdowns();
            
            if (typeof window.abrirResenasGlobal === 'function') {
                window.abrirResenasGlobal(
                    card.dataset.id,
                    card.dataset.titulo,
                    card.dataset.artista,
                    card.dataset.portada
                );
            } else {
                if (typeof showToast === 'function') showToast('Sistema de reseñas no disponible', 'error');
            }
            return;
        }

        // ========== CLICK EN TARJETA (reproducir) ==========
        if (e.target.closest('.song-card') && !e.target.closest('button') && !e.target.closest('.card-dropdown')) {
            var card = e.target.closest('.song-card');
            if (card && typeof window.reproducirCancion === 'function') {
                window.reproducirCancion(card.dataset.id);
            }
            return;
        }

        // ========== FILTROS DE GÉNERO ==========
        if (e.target.closest('.genre-filter')) {
            var btn = e.target.closest('.genre-filter');
            var genre = btn.dataset.genre;
            var cards = document.querySelectorAll('.song-card');
            
            if (btn.classList.contains('active')) {
                btn.classList.remove('active');
                cards.forEach(function(c) { c.style.display = ''; });
            } else {
                document.querySelectorAll('.genre-filter').forEach(function(b) { b.classList.remove('active'); });
                btn.classList.add('active');
                cards.forEach(function(c) {
                    var cardGenre = (c.dataset.genre || '').toLowerCase();
                    c.style.display = cardGenre === genre.toLowerCase() ? '' : 'none';
                });
            }
            return;
        }

        // ========== CERRAR MODAL PLAYLIST ==========
        if (e.target.closest('#closePlaylistModal') || e.target.id === 'playlistModalGlobal') {
            if (e.target.id === 'playlistModalGlobal' || e.target.closest('#closePlaylistModal')) {
                cerrarModalPlaylist();
            }
            return;
        }

        // ========== SELECCIONAR PLAYLIST ==========
        if (e.target.closest('.playlist-select-item')) {
            var item = e.target.closest('.playlist-select-item');
            agregarCancionAPlaylist(item.dataset.id);
            return;
        }
    });

    // Cerrar dropdown con ESC
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            cerrarTodosDropdowns();
            cerrarModalPlaylist();
        }
    });

    // ============================================================
    // FUNCIONES AUXILIARES
    // ============================================================
    function revertirFavorito(btn, icon, estadoOriginal) {
        if (estadoOriginal) {
            btn.classList.add('liked');
            if (icon) { icon.classList.add('fa-solid'); icon.classList.remove('fa-regular'); }
        } else {
            btn.classList.remove('liked');
            if (icon) { icon.classList.remove('fa-solid'); icon.classList.add('fa-regular'); }
        }
    }

    function revertirDescarga(card, icon, span, estadoOriginal) {
        if (estadoOriginal) {
            card.dataset.downloaded = 'true';
            if (icon) { icon.classList.add('fa-check'); icon.classList.remove('fa-download'); }
            if (span) span.textContent = 'Quitar de descargas';
        } else {
            card.dataset.downloaded = 'false';
            if (icon) { icon.classList.remove('fa-check'); icon.classList.add('fa-download'); }
            if (span) span.textContent = 'Descargar offline';
        }
    }

    // ============================================================
    // MODAL DE PLAYLIST
    // ============================================================
    var selectedSongId = null;

    function abrirModalPlaylist(cancionId) {
        selectedSongId = cancionId;
        
        var modal = document.getElementById('playlistModalGlobal');
        if (!modal) {
            crearModalPlaylist();
            modal = document.getElementById('playlistModalGlobal');
        }
        
        cargarPlaylistsEnModal();
        modal.classList.add('active');
    }

    function cerrarModalPlaylist() {
        var modal = document.getElementById('playlistModalGlobal');
        if (modal) modal.classList.remove('active');
        selectedSongId = null;
    }

    function crearModalPlaylist() {
        var modalHTML = 
            '<div id="playlistModalGlobal" class="modal-overlay-global">' +
                '<div class="modal-global" style="max-width: 400px;">' +
                    '<div class="modal-header-global">' +
                        '<h2><i class="fa-solid fa-plus" style="color: var(--french-rose);"></i> Añadir a playlist</h2>' +
                        '<button class="modal-close-global" id="closePlaylistModal"><i class="fa-solid fa-xmark"></i></button>' +
                    '</div>' +
                    '<div id="playlistsListContainer" style="max-height: 300px; overflow-y: auto;">' +
                        '<div style="text-align: center; padding: 20px; color: var(--text-muted);"><i class="fa-solid fa-spinner fa-spin"></i> Cargando...</div>' +
                    '</div>' +
                    '<div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid rgba(255,255,255,0.1);">' +
                        '<p style="font-size: 12px; color: var(--text-muted); margin-bottom: 10px;">Crear nueva playlist:</p>' +
                        '<div style="display: flex; gap: 10px;">' +
                            '<input type="text" id="newPlaylistNameInput" placeholder="Nombre de la playlist" style="flex: 1; padding: 10px 12px; background: #1a1a1a; border: 1px solid #333; border-radius: 6px; color: white; font-size: 14px;">' +
                            '<button id="crearNuevaPlaylistBtn" style="padding: 10px 15px; background: var(--french-rose); border: none; border-radius: 6px; color: white; cursor: pointer; font-weight: 600;"><i class="fa-solid fa-plus"></i></button>' +
                        '</div>' +
                    '</div>' +
                '</div>' +
            '</div>';
        
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        
        document.getElementById('crearNuevaPlaylistBtn').addEventListener('click', crearNuevaPlaylist);
        document.getElementById('newPlaylistNameInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') crearNuevaPlaylist();
        });
    }

    function cargarPlaylistsEnModal() {
        var container = document.getElementById('playlistsListContainer');
        if (!container) return;

        fetch('/api/playlists/usuario/')
        .then(function(r) { return r.json(); })
        .then(function(data) {
            if (data.success && data.playlists && data.playlists.length > 0) {
                var html = '';
                data.playlists.forEach(function(p) {
                    html += '<div class="playlist-select-item" data-id="' + p.id + '" style="display: flex; align-items: center; gap: 12px; padding: 12px; border-radius: 6px; cursor: pointer; transition: background 0.2s;">' +
                        '<div style="width: 45px; height: 45px; background: linear-gradient(135deg, var(--french-rose), #8b5cf6); border-radius: 6px; display: flex; align-items: center; justify-content: center;">' +
                            '<i class="fa-solid fa-music" style="color: white;"></i>' +
                        '</div>' +
                        '<div>' +
                            '<div style="font-weight: 600; font-size: 14px;">' + escapeHtml(p.nombre) + '</div>' +
                            '<div style="font-size: 12px; color: var(--text-muted);">' + (p.total_canciones || 0) + ' canciones</div>' +
                        '</div>' +
                    '</div>';
                });
                container.innerHTML = html;
                
                container.querySelectorAll('.playlist-select-item').forEach(function(item) {
                    item.addEventListener('mouseenter', function() { this.style.background = 'var(--bg-hover)'; });
                    item.addEventListener('mouseleave', function() { this.style.background = ''; });
                });
            } else {
                container.innerHTML = '<div style="text-align: center; padding: 30px; color: var(--text-muted);"><i class="fa-solid fa-folder-open" style="font-size: 32px; margin-bottom: 10px; display: block; opacity: 0.5;"></i><p>No tienes playlists</p></div>';
            }
        })
        .catch(function() {
            container.innerHTML = '<div style="text-align: center; padding: 20px; color: #ff4444;">Error al cargar playlists</div>';
        });
    }

    function agregarCancionAPlaylist(playlistId) {
        if (!selectedSongId) return;

        fetch('/api/playlist/agregar-cancion/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCSRFToken() },
            body: JSON.stringify({ playlist_id: playlistId, cancion_id: selectedSongId })
        })
        .then(function(r) { return r.json(); })
        .then(function(data) {
            if (typeof showToast === 'function') showToast(data.message, data.success ? 'success' : 'error');
            if (data.success) cerrarModalPlaylist();
        })
        .catch(function() {
            if (typeof showToast === 'function') showToast('Error de conexión', 'error');
        });
    }

    function crearNuevaPlaylist() {
        var input = document.getElementById('newPlaylistNameInput');
        var nombre = input.value.trim();
        
        if (!nombre) {
            if (typeof showToast === 'function') showToast('Ingresa un nombre', 'error');
            return;
        }

        fetch('/api/playlist/crear/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCSRFToken() },
            body: JSON.stringify({ nombre: nombre })
        })
        .then(function(r) { return r.json(); })
        .then(function(data) {
            if (data.success) {
                input.value = '';
                if (typeof showToast === 'function') showToast('Playlist creada');
                cargarPlaylistsEnModal();
                if (selectedSongId && data.playlist_id) {
                    agregarCancionAPlaylist(data.playlist_id);
                }
            } else {
                if (typeof showToast === 'function') showToast(data.message || 'Error', 'error');
            }
        })
        .catch(function() {
            if (typeof showToast === 'function') showToast('Error de conexión', 'error');
        });
    }

    console.log('🎵 Lista de reproducción inicializada');

})();