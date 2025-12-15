/* ============================================================
   MUUUSICA - APP PRINCIPAL (Reproductor + Reseñas + SPA)
   ============================================================ */

(function() {
    'use strict';

    if (window.MuuuPlayerLoaded) {
        console.warn('⚠️ El reproductor ya está cargado. Se evitó una duplicación.');
        return;
    }
    window.MuuuPlayerLoaded = true;
    
    // ============================================================
    // LÓGICA DEL REPRODUCTOR DE MÚSICA
    // ============================================================

    // Variables globales
    var currentSongId = null;
    var isPlaying = false;
    var audioPlayer = null;
    var songsList = [];
    var queue = [];
    var isShuffle = false;
    var repeatMode = 'none';
    var currentSongData = null;

    // ==================== INICIALIZACIÓN ====================
    document.addEventListener('DOMContentLoaded', function() {
        audioPlayer = document.getElementById('gAudioPlayer');
        if (!audioPlayer) {
            console.warn('⚠️ No se encontró elemento de audio');
            return;
        }

        // Evitar múltiples listeners si el DOM se recarga parcialmente
        if (audioPlayer.dataset.initialized === 'true') {
             console.log('Audio ya inicializado');
        } else {
             audioPlayer.dataset.initialized = 'true';
             inicializarEventosReproductor();
        }
        
        cargarCancionesEnLista();
        restaurarEstadoReproductor();
        inicializarCola();
        
        console.log('✅ Reproductor global inicializado');
    });

    // ==================== SISTEMA DE COLA ====================
    function inicializarCola() {
        var savedQueue = localStorage.getItem('muuusica_queue');
        if (savedQueue) {
            try {
                queue = JSON.parse(savedQueue);
                actualizarContadorCola();
                console.log('📋 Cola restaurada:', queue.length, 'canciones');
            } catch(e) {
                queue = [];
            }
        }
    }

    function agregarACola(songId) {
        var song = songsList.find(function(s) { return s.id == songId; });
        
        if (!song) {
            var el = document.querySelector('[data-id="' + songId + '"]');
            if (el) {
                song = {
                    id: songId,
                    titulo: el.dataset.titulo || 'Sin título',
                    artista: el.dataset.artista || 'Artista',
                    portada: el.dataset.portada || '',
                    ruta: el.dataset.ruta || ''
                };
            }
        }
        
        if (!song) {
            showToast('Canción no encontrada', 'error');
            return;
        }
        
        var yaEnCola = queue.find(function(s) { return s.id == songId; });
        if (yaEnCola) {
            showToast('Ya está en la cola', 'error');
            return;
        }
        
        queue.push(song);
        guardarCola();
        actualizarContadorCola();
        actualizarUIColaModal();
        showToast('Agregada a la cola');
    }

    function quitarDeCola(index) {
        if (index >= 0 && index < queue.length) {
            var removed = queue.splice(index, 1)[0];
            guardarCola();
            actualizarContadorCola();
            actualizarUIColaModal();
            showToast('Removida de la cola');
        }
    }

    function limpiarCola() {
        queue = [];
        guardarCola();
        actualizarContadorCola();
        actualizarUIColaModal();
        showToast('Cola limpiada');
    }

    function reproducirSiguienteDeCola() {
        if (queue.length === 0) return false;
        
        var nextSong = queue.shift();
        guardarCola();
        actualizarContadorCola();
        actualizarUIColaModal();
        reproducirCancion(nextSong.id);
        
        return true;
    }

    function reproducirColaAhora() {
        if (queue.length === 0) {
            showToast('La cola está vacía', 'error');
            return;
        }
        reproducirSiguienteDeCola();
    }

    function guardarCola() {
        localStorage.setItem('muuusica_queue', JSON.stringify(queue));
    }

    function actualizarContadorCola() {
        var contador = document.getElementById('gQueueCount');
        var badge = document.getElementById('gQueueBadge');
        
        if (contador) contador.textContent = queue.length;
        
        if (badge) {
            badge.textContent = queue.length;
            badge.style.display = queue.length > 0 ? 'flex' : 'none';
        }
    }

    function actualizarNowPlayingEnModal() {
        var coverEl = document.getElementById('gQueueCurrentCover');
        var titleEl = document.getElementById('gQueueCurrentTitle');
        var artistEl = document.getElementById('gQueueCurrentArtist');
        
        if (currentSongData) {
            if (coverEl) {
                // Si hay portada, imagen. Si no, icono musical.
                coverEl.innerHTML = currentSongData.portada ? 
                    '<img src="' + currentSongData.portada + '" alt="">' : 
                    '<i class="fa-solid fa-music"></i>';
            }
            if (titleEl) titleEl.textContent = currentSongData.titulo || 'Sin título';
            if (artistEl) artistEl.textContent = currentSongData.artista || 'Artista desconocido';
        } else {
            if (coverEl) coverEl.innerHTML = '<i class="fa-solid fa-music"></i>';
            if (titleEl) titleEl.textContent = 'Ninguna canción';
            if (artistEl) artistEl.textContent = 'Selecciona una canción';
        }
    }

    function actualizarUIColaModal() {
        var listaContainer = document.getElementById('gQueueList');
        var emptyMessage = document.getElementById('gQueueEmpty');
        var queueActions = document.getElementById('gQueueActions');
        
        if (!listaContainer) return;
        
        if (queue.length === 0) {
            listaContainer.innerHTML = '';
            if (emptyMessage) emptyMessage.style.display = 'block';
            if (queueActions) queueActions.style.display = 'none';
            return;
        }
        
        if (emptyMessage) emptyMessage.style.display = 'none';
        if (queueActions) queueActions.style.display = 'flex';
        
        var html = '';
        for (var i = 0; i < queue.length; i++) {
            var song = queue[i];
            html += '<div class="queue-item" data-index="' + i + '">' +
                '<div class="queue-item-drag" title="Arrastrar"><i class="fa-solid fa-grip-vertical"></i></div>' +
                '<div class="queue-item-cover">' +
                    (song.portada ? '<img src="' + song.portada + '" alt="">' : '<i class="fa-solid fa-music" style="font-size: 0.8rem;"></i>') +
                '</div>' +
                '<div class="queue-item-info">' +
                    '<div class="queue-item-title">' + escapeHtml(song.titulo) + '</div>' +
                    '<div class="queue-item-artist">' + escapeHtml(song.artista) + '</div>' +
                '</div>' +
                '<div class="queue-item-actions">' +
                    '<button class="queue-play-btn" data-index="' + i + '" title="Reproducir"><i class="fa-solid fa-play"></i></button>' +
                    '<button class="queue-remove-btn" data-index="' + i + '" title="Quitar"><i class="fa-solid fa-xmark"></i></button>' +
                '</div>' +
            '</div>';
        }
        listaContainer.innerHTML = html;
        
        listaContainer.querySelectorAll('.queue-play-btn').forEach(function(btn) {
            btn.addEventListener('click', function() {
                reproducirDesdeColaIndex(parseInt(this.dataset.index));
            });
        });
        
        listaContainer.querySelectorAll('.queue-remove-btn').forEach(function(btn) {
            btn.addEventListener('click', function() {
                quitarDeCola(parseInt(this.dataset.index));
            });
        });
    }

    function reproducirDesdeColaIndex(index) {
        if (index >= 0 && index < queue.length) {
            var song = queue[index];
            queue.splice(index, 1);
            guardarCola();
            actualizarContadorCola();
            actualizarUIColaModal();
            reproducirCancion(song.id);
        }
    }

    function escapeHtml(text) {
        var div = document.createElement('div');
        div.textContent = text || '';
        return div.innerHTML;
    }

    // ==================== LISTA DE CANCIONES ====================
    function cargarCancionesEnLista() {
        var cancionesEnPagina = [];
        
        document.querySelectorAll('[data-id][data-titulo], [data-id][data-ruta], .song-row[data-id], .song-card[data-id]').forEach(function(el, index) {
            var song = {
                id: el.dataset.id,
                titulo: el.dataset.titulo || el.querySelector('.song-title, .song-info h4') && el.querySelector('.song-title, .song-info h4').textContent || 'Sin título',
                artista: el.dataset.artista || el.querySelector('.song-artist, .song-info p') && el.querySelector('.song-artist, .song-info p').textContent || 'Artista desconocido',
                portada: el.dataset.portada || (el.querySelector('img') ? el.querySelector('img').src : ''),
                ruta: el.dataset.ruta || '',
                index: index
            };
            
            var existe = cancionesEnPagina.find(function(s) { return s.id === song.id; });
            if (!existe) {
                cancionesEnPagina.push(song);
            }
        });
        
        if (cancionesEnPagina.length > 0) {
            songsList = cancionesEnPagina;
            if (currentSongData) {
                var existeActual = songsList.find(function(s) { return s.id == currentSongData.id; });
                if (!existeActual) {
                    songsList.unshift(currentSongData);
                }
            }
            localStorage.setItem('muuusica_playlist', JSON.stringify(songsList));
        } else {
            var savedPlaylist = localStorage.getItem('muuusica_playlist');
            if (savedPlaylist && songsList.length === 0) {
                try {
                    songsList = JSON.parse(savedPlaylist);
                } catch(e) {}
            }
        }
        
        if (currentSongId) marcarCancionActiva(currentSongId);
    }

    // ==================== PERSISTENCIA ====================
    function guardarEstadoReproductor() {
        var songData = currentSongData || songsList.find(function(s) { return s.id == currentSongId; }) || null;
        
        var estado = {
            songId: currentSongId,
            isPlaying: isPlaying,
            currentTime: audioPlayer ? audioPlayer.currentTime : 0,
            volume: audioPlayer ? audioPlayer.volume : 0.7,
            isShuffle: isShuffle,
            repeatMode: repeatMode,
            songData: songData,
            timestamp: Date.now()
        };
        localStorage.setItem('muuusica_player', JSON.stringify(estado));
    }

    function restaurarEstadoReproductor() {
        var savedPlaylist = localStorage.getItem('muuusica_playlist');
        if (savedPlaylist) {
            try {
                var playlist = JSON.parse(savedPlaylist);
                if (playlist && playlist.length > 0) {
                    songsList = playlist;
                }
            } catch(e) {}
        }
        
        var saved = localStorage.getItem('muuusica_player');
        if (!saved) return;
        
        try {
            var estado = JSON.parse(saved);
            
            isShuffle = estado.isShuffle || false;
            repeatMode = estado.repeatMode || 'none';
            actualizarBotonesExtra();
            
            if (estado.songData) {
                currentSongId = estado.songId;
                currentSongData = estado.songData;
                
                var existeEnLista = songsList.find(function(s) { return s.id == currentSongData.id; });
                if (currentSongData && !existeEnLista) {
                    songsList.unshift(currentSongData);
                }
                
                actualizarUICancion(estado.songData);
                
                if (estado.songData.ruta && audioPlayer) {
                    audioPlayer.src = estado.songData.ruta;
                    audioPlayer.volume = estado.volume || 0.7;
                    
                    audioPlayer.addEventListener('loadedmetadata', function onLoaded() {
                        audioPlayer.removeEventListener('loadedmetadata', onLoaded);
                        if (estado.currentTime > 0 && estado.currentTime < audioPlayer.duration) {
                            audioPlayer.currentTime = estado.currentTime;
                        }
                        isPlaying = false;
                        actualizarBotonPlay();
                    });
                    
                    // No hacemos audioPlayer.load() directo para no autoreproducir al refrescar
                    actualizarVolumenUI(estado.volume || 0.7);
                }
            }
        } catch (e) {
            console.error('Error restaurando estado:', e);
        }
    }

    setInterval(guardarEstadoReproductor, 1000);

    // ==================== REPRODUCCIÓN ====================
    function reproducirCancion(songId, playlistOverride) {
        if (playlistOverride && playlistOverride.length > 0) {
            songsList = playlistOverride;
        }
        
        var song = songsList.find(function(s) { return s.id == songId; });
        
        if (!song) {
            var el = document.querySelector('[data-id="' + songId + '"]');
            if (el) {
                song = {
                    id: songId,
                    titulo: el.dataset.titulo || 'Sin título',
                    artista: el.dataset.artista || 'Artista',
                    portada: el.dataset.portada || '',
                    ruta: el.dataset.ruta || ''
                };
                var existe = songsList.find(function(s) { return s.id === song.id; });
                if (!existe) {
                    songsList.push(song);
                }
            }
        }
        
        if (!song) {
            song = queue.find(function(s) { return s.id == songId; });
        }
        
        if (!song) {
            console.warn('Canción no encontrada:', songId);
            return;
        }
        
        currentSongId = songId;
        currentSongData = song;
        
        actualizarUICancion(song);
        
        if (song.ruta && song.ruta !== '' && song.ruta !== 'None' && audioPlayer) {
            audioPlayer.src = song.ruta;
            audioPlayer.play()
                .then(function() {
                    isPlaying = true;
                    actualizarBotonPlay();
                    guardarEstadoReproductor();
                })
                .catch(function(error) {
                    console.log('Error reproduciendo:', error);
                    showToast('Error al reproducir', 'error');
                });
        } else {
            showToast('Sin archivo de audio', 'error');
        }
        
        marcarCancionActiva(songId);
        guardarEstadoReproductor();
    }

    function pausarCancion() {
        if (audioPlayer) audioPlayer.pause();
        isPlaying = false;
        actualizarBotonPlay();
        guardarEstadoReproductor();
    }

    function reanudarCancion() {
        if (currentSongId && audioPlayer && audioPlayer.src) {
            audioPlayer.play()
                .then(function() {
                    isPlaying = true;
                    actualizarBotonPlay();
                })
                .catch(function() {});
        }
        guardarEstadoReproductor();
    }

    function togglePlay() {
        if (currentSongId && audioPlayer && audioPlayer.src) {
            if (isPlaying) {
                pausarCancion();
            } else {
                reanudarCancion();
            }
            return;
        }
        
        if (currentSongData && currentSongData.ruta) {
            reproducirCancion(currentSongData.id);
            return;
        }
        
        if (queue.length > 0) {
            reproducirSiguienteDeCola();
            return;
        }
        
        if (songsList.length > 0) {
            reproducirCancion(songsList[0].id);
            return;
        }
        
        showToast('No hay canciones disponibles', 'error');
    }

    function siguienteCancion() {
        if (queue.length > 0) {
            reproducirSiguienteDeCola();
            return;
        }
        
        if (songsList.length === 0) return;
        
        var nextIndex;
        var currentIndex = -1;
        for (var i = 0; i < songsList.length; i++) {
            if (songsList[i].id == currentSongId) {
                currentIndex = i;
                break;
            }
        }
        
        if (isShuffle) {
            nextIndex = Math.floor(Math.random() * songsList.length);
            if (songsList.length > 1 && nextIndex === currentIndex) {
                nextIndex = (nextIndex + 1) % songsList.length;
            }
        } else {
            nextIndex = currentIndex + 1;
            if (nextIndex >= songsList.length) {
                if (repeatMode === 'all') {
                    nextIndex = 0;
                } else {
                    isPlaying = false;
                    actualizarBotonPlay();
                    return;
                }
            }
        }
        
        reproducirCancion(songsList[nextIndex].id);
    }

    function anteriorCancion() {
        if (songsList.length === 0) return;
        
        var currentIndex = -1;
        for (var i = 0; i < songsList.length; i++) {
            if (songsList[i].id == currentSongId) {
                currentIndex = i;
                break;
            }
        }
        
        if (audioPlayer && audioPlayer.currentTime > 3) {
            audioPlayer.currentTime = 0;
            return;
        }
        
        var prevIndex = currentIndex - 1;
        if (prevIndex < 0) prevIndex = songsList.length - 1;
        
        reproducirCancion(songsList[prevIndex].id);
    }

    // ==================== CONTROLES EXTRA ====================
    function toggleShuffle() {
        isShuffle = !isShuffle;
        actualizarBotonesExtra();
        showToast(isShuffle ? 'Aleatorio activado' : 'Aleatorio desactivado');
        guardarEstadoReproductor();
    }

    function toggleRepeat() {
        var modes = ['none', 'all', 'one'];
        var currentIndex = modes.indexOf(repeatMode);
        repeatMode = modes[(currentIndex + 1) % modes.length];
        actualizarBotonesExtra();
        
        var mensajes = { 'none': 'Repetir desactivado', 'all': 'Repetir todo', 'one': 'Repetir una' };
        showToast(mensajes[repeatMode]);
        guardarEstadoReproductor();
    }

    function actualizarBotonesExtra() {
        var shuffleBtn = document.getElementById('gShuffleBtn');
        var repeatBtn = document.getElementById('gRepeatBtn');
        
        if (shuffleBtn) {
            if (isShuffle) {
                shuffleBtn.style.color = 'var(--french-rose)';
                shuffleBtn.style.opacity = '1';
            } else {
                shuffleBtn.style.color = 'var(--text-gray)';
                shuffleBtn.style.opacity = '0.8';
            }
        }
    }

    // ==================== UI ====================
    function actualizarUICancion(song) {
        // Reproductor inferior
        var playerTitle = document.getElementById('gPlayerTitle');
        var playerArtist = document.getElementById('gPlayerArtist');
        var playerCover = document.getElementById('gPlayerCover');
        
        if (playerTitle) playerTitle.textContent = song.titulo || 'Sin título';
        if (playerArtist) playerArtist.textContent = song.artista || 'Artista desconocido';
        
        if (playerCover) {
            if (song.portada && song.portada !== '') {
                playerCover.innerHTML = '<img src="' + song.portada + '" alt="' + song.titulo + '">';
            } else {
                playerCover.innerHTML = '<div class="player-cover-placeholder"><i class="fa-solid fa-music" style="font-size: 1.5rem; color: #555;"></i></div>';
            }
        }
        
        // ========== SIDEBAR DERECHO (Ahora Reproduciendo) ==========
        var sideTitle = document.getElementById('sidePlayerTitle');
        var sideArtist = document.getElementById('sidePlayerArtist');
        var sideCover = document.getElementById('sidePlayerCover');
        var nowPlayingWidget = document.querySelector('.now-playing-widget');
        
        if (sideTitle) sideTitle.textContent = song.titulo || 'Sin título';
        if (sideArtist) sideArtist.textContent = song.artista || 'Artista desconocido';
        if (sideCover && song.portada) sideCover.src = song.portada;
        
        // Quitar clase "empty" cuando hay canción
        if (nowPlayingWidget) nowPlayingWidget.classList.remove('empty');
        
        document.title = song.titulo ? song.titulo + ' - MuuuSIC' : 'MuuuSIC';
    }

    function actualizarBotonPlay() {
        var mainPlayBtn = document.getElementById('gPlayPauseBtn');
        if (mainPlayBtn) {
            if (isPlaying) {
                mainPlayBtn.classList.remove('fa-circle-play');
                mainPlayBtn.classList.add('fa-circle-pause');
            } else {
                mainPlayBtn.classList.remove('fa-circle-pause');
                mainPlayBtn.classList.add('fa-circle-play');
            }
        }
    }

    function marcarCancionActiva(songId) {
        document.querySelectorAll('.song-row, .song-card, [data-id]').forEach(function(el) {
            el.classList.remove('playing', 'active');
        });
        
        var activeEl = document.querySelector('[data-id="' + songId + '"]');
        if (activeEl) activeEl.classList.add('playing', 'active');
    }

    function actualizarVolumenUI(volume) {
        var volumeFill = document.getElementById('gVolumeFill');
        var volumeBtn = document.getElementById('gVolumeBtn');
        
        if (volumeFill) volumeFill.style.width = (volume * 100) + '%';
        
        // Cambiar icono de volumen dinámicamente
        if (volumeBtn) {
            // Quitamos todas las posibles clases de volumen
            volumeBtn.classList.remove('fa-volume-high', 'fa-volume-low', 'fa-volume-xmark');
            
            if (volume === 0) {
                volumeBtn.classList.add('fa-volume-xmark');
            } else if (volume < 0.5) {
                volumeBtn.classList.add('fa-volume-low');
            } else {
                volumeBtn.classList.add('fa-volume-high');
            }
        }
    }

    function actualizarProgreso() {
        if (!audioPlayer || !audioPlayer.duration) return;
        
        var progress = (audioPlayer.currentTime / audioPlayer.duration) * 100;
        var progressFill = document.getElementById('gProgressFill');
        var currentTimeEl = document.getElementById('gCurrentTime');
        var totalTimeEl = document.getElementById('gTotalTime');
        
        if (progressFill) progressFill.style.width = progress + '%';
        if (currentTimeEl) currentTimeEl.textContent = formatTime(audioPlayer.currentTime);
        if (totalTimeEl) totalTimeEl.textContent = formatTime(audioPlayer.duration);
    }

    function formatTime(seconds) {
        if (isNaN(seconds) || !isFinite(seconds)) return '0:00';
        var mins = Math.floor(seconds / 60);
        var secs = Math.floor(seconds % 60);
        return mins + ':' + (secs < 10 ? '0' : '') + secs;
    }

    function showToast(message, type) {
        type = type || 'success';
        var toast = document.getElementById('toast');
        if (!toast) return;
        
        // Agregar iconos al toast
        var icon = '';
        if (type === 'error') icon = '<i class="fa-solid fa-circle-exclamation"></i> ';
        else icon = '<i class="fa-solid fa-circle-check"></i> ';
        
        toast.innerHTML = icon + message;
        toast.className = 'toast ' + type + ' show';
        
        setTimeout(function() {
            toast.classList.remove('show');
        }, 3000);
    }

    // ==================== FAVORITOS ====================
    function toggleFavorito() {
        if (!currentSongId) {
            showToast('Selecciona una canción primero', 'error');
            return;
        }
        
        // Buscamos el ICONO dentro del botón
        var likeBtn = document.getElementById('gPlayerLikeBtn');
        var likeIcon = likeBtn ? likeBtn.querySelector('i') : null;

        // Efecto visual inmediato (Optimistic UI)
        // Cambiamos el icono ANTES de que el servidor responda para que se sienta rápido
        var estabaLikeado = likeBtn.classList.contains('liked');
        
        if (estabaLikeado) {
            // Quitar visualmente
            if (likeIcon) { likeIcon.classList.remove('fa-solid'); likeIcon.classList.add('fa-regular'); }
            likeBtn.classList.remove('liked');
        } else {
            // Poner visualmente
            if (likeIcon) { likeIcon.classList.remove('fa-regular'); likeIcon.classList.add('fa-solid'); }
            likeBtn.classList.add('liked');
        }
        
        fetch('/api/favorito/toggle/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ cancion_id: currentSongId })
        })
        .then(function(response) { return response.json(); })
        .then(function(data) {
            if (data.success) {
                if (likeIcon) {
                    if (data.es_favorito) {
                        likeIcon.classList.remove('fa-regular');
                        likeIcon.classList.add('fa-solid'); // Corazón lleno
                        likeBtn.classList.add('liked');
                    } else {
                        likeIcon.classList.remove('fa-solid');
                        likeIcon.classList.add('fa-regular'); // Corazón vacío
                        likeBtn.classList.remove('liked');
                    }
                }
                showToast(data.message);
            }
        })
        .catch(function(error) {
            showToast('Error al procesar', 'error');
        });
    }

    // ==================== COMPARTIR ====================
function abrirModalCompartir() {
    if (!currentSongId || !currentSongData) {
        showToast('Primero reproduce una canción', 'error');
        return;
    }
    
    var modal = document.getElementById('gShareModal');
    var coverImg = document.getElementById('gShareCover');
    var titleEl = document.getElementById('gShareTitle');
    var artistEl = document.getElementById('gShareArtist');
    var inputEl = document.getElementById('gShareInput');
    
    if (!modal) return;
    
    // Llenar datos
    if (coverImg) coverImg.src = currentSongData.portada || '';
    if (titleEl) titleEl.textContent = currentSongData.titulo || 'Sin título';
    if (artistEl) artistEl.textContent = currentSongData.artista || 'Artista';
    
    // Generar URL de compartir
    var shareUrl = window.location.origin + '/compartir/cancion/' + currentSongId + '/';
    if (inputEl) inputEl.value = shareUrl;
    
    // Resetear QR
    var qrContainer = document.getElementById('gShareQRContainer');
    var qrCode = document.getElementById('gShareQRCode');
    if (qrContainer) qrContainer.style.display = 'none';
    if (qrCode) qrCode.innerHTML = '';
    
    // Mostrar modal
    modal.classList.add('active');
}

function cerrarModalCompartir() {
    var modal = document.getElementById('gShareModal');
    if (modal) modal.classList.remove('active');
}

function copiarEnlaceCompartir() {
    var input = document.getElementById('gShareInput');
    if (!input) return;
    
    var url = input.value;
    
    if (navigator.clipboard) {
        navigator.clipboard.writeText(url).then(function() {
            showToast('¡Enlace copiado!');
        });
    } else {
        input.select();
        document.execCommand('copy');
        showToast('¡Enlace copiado!');
    }
}

function toggleQRCompartir() {
    var container = document.getElementById('gShareQRContainer');
    var qrCodeEl = document.getElementById('gShareQRCode');
    var input = document.getElementById('gShareInput');
    
    if (!container || !qrCodeEl) return;
    
    if (container.style.display === 'none') {
        container.style.display = 'block';
        
        // Generar QR solo si está vacío
        if (qrCodeEl.innerHTML === '' && typeof QRCode !== 'undefined') {
            new QRCode(qrCodeEl, {
                text: input.value,
                width: 120,
                height: 120,
                colorDark: '#000000',
                colorLight: '#ffffff'
            });
        }
    } else {
        container.style.display = 'none';
    }
}
    // ==================== MODAL DE COLA ====================
    function toggleQueueModal() {
        var modal = document.getElementById('gQueueModal');
        if (modal) {
            modal.classList.toggle('active');
            if (modal.classList.contains('active')) {
                actualizarNowPlayingEnModal();
                actualizarUIColaModal();
            }
        }
    }

    function cerrarQueueModal() {
        var modal = document.getElementById('gQueueModal');
        if (modal) modal.classList.remove('active');
    }

    // ==================== EVENTOS ====================
    function inicializarEventosReproductor() {
        // Play/Pause
        var playBtn = document.getElementById('gPlayPauseBtn');
        if (playBtn) playBtn.addEventListener('click', togglePlay);
        
        // Controles de navegación
        var prevBtn = document.getElementById('gPrevBtn');
        if (prevBtn) prevBtn.addEventListener('click', anteriorCancion);
        
        var nextBtn = document.getElementById('gNextBtn');
        if (nextBtn) nextBtn.addEventListener('click', siguienteCancion);
        
        var shuffleBtn = document.getElementById('gShuffleBtn');
        if (shuffleBtn) shuffleBtn.addEventListener('click', toggleShuffle);
        
        var likeBtn = document.getElementById('gPlayerLikeBtn');
        if (likeBtn) likeBtn.addEventListener('click', toggleFavorito);
        
        // Cola
        var queueBtn = document.getElementById('gQueueBtn');
        if (queueBtn) queueBtn.addEventListener('click', toggleQueueModal);
        
        var closeQueueBtn = document.getElementById('gCloseQueueModal');
        if (closeQueueBtn) closeQueueBtn.addEventListener('click', cerrarQueueModal);
        
        var clearQueueBtn = document.getElementById('gClearQueueBtn');
        if (clearQueueBtn) clearQueueBtn.addEventListener('click', limpiarCola);
        
        var playQueueBtn = document.getElementById('gPlayQueueBtn');
        if (playQueueBtn) playQueueBtn.addEventListener('click', reproducirColaAhora);
        
        var queueModal = document.getElementById('gQueueModal');
        if (queueModal) {
            queueModal.addEventListener('click', function(e) {
                if (e.target === this) cerrarQueueModal();
            });
        }
        
        // ========== COMPARTIR ==========
        var shareBtn = document.getElementById('gPlayerShareBtn');
        if (shareBtn) shareBtn.addEventListener('click', abrirModalCompartir);

        var closeShareBtn = document.getElementById('gCloseShareModal');
        if (closeShareBtn) closeShareBtn.addEventListener('click', cerrarModalCompartir);

        var copyShareBtn = document.getElementById('gShareCopyBtn');
        if (copyShareBtn) copyShareBtn.addEventListener('click', copiarEnlaceCompartir);

        var toggleQRBtn = document.getElementById('gShareToggleQR');
        if (toggleQRBtn) toggleQRBtn.addEventListener('click', toggleQRCompartir);

        var shareModal = document.getElementById('gShareModal');
        if (shareModal) {
            shareModal.addEventListener('click', function(e) {
                if (e.target === this) cerrarModalCompartir();
            });
        }
        
        // Barra de progreso
        var progressBar = document.getElementById('gProgressBar');
        if (progressBar && audioPlayer) {
            progressBar.addEventListener('click', function(e) {
                if (!audioPlayer.duration) return;
                var rect = this.getBoundingClientRect();
                var percent = (e.clientX - rect.left) / rect.width;
                audioPlayer.currentTime = percent * audioPlayer.duration;
            });
        }
        
        // Barra Volumen
        var volumeBar = document.getElementById('gVolumeBar');
        if (volumeBar && audioPlayer) {
            volumeBar.addEventListener('click', function(e) {
                var rect = this.getBoundingClientRect();
                var percent = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
                audioPlayer.volume = percent;
                actualizarVolumenUI(percent);
                guardarEstadoReproductor();
            });
        }
        
        // Botón Volumen (Mute)
        var previousVolume = 0.7;
        var volumeBtn = document.getElementById('gVolumeBtn');
        if (volumeBtn) {
            volumeBtn.addEventListener('click', function() {
                if (audioPlayer.volume > 0) {
                    previousVolume = audioPlayer.volume;
                    audioPlayer.volume = 0;
                } else {
                    audioPlayer.volume = previousVolume > 0 ? previousVolume : 0.7;
                }
                actualizarVolumenUI(audioPlayer.volume);
                guardarEstadoReproductor();
            });
        }
        
        // Listeners de Audio
        if (audioPlayer) {
            audioPlayer.addEventListener('timeupdate', actualizarProgreso);
            audioPlayer.addEventListener('ended', function() {
                if (repeatMode === 'one') {
                    audioPlayer.currentTime = 0;
                    audioPlayer.play();
                } else {
                    siguienteCancion();
                }
            });
            audioPlayer.addEventListener('error', function() {
                showToast('Error al reproducir', 'error');
            });
            audioPlayer.addEventListener('play', function() {
                isPlaying = true;
                actualizarBotonPlay();
            });
            audioPlayer.addEventListener('pause', function() {
                isPlaying = false;
                actualizarBotonPlay();
            });
        }
        
        // Delegación global para botones "Añadir a Cola" en las cards
        document.addEventListener('click', function(e) {
            var queueBtn = e.target.closest('.add-queue-btn');
            if (queueBtn) {
                e.stopPropagation();
                var card = queueBtn.closest('[data-id]');
                if (card) {
                    var songId = card.dataset.id;
                    agregarACola(songId);
                }
            }
        });
        
        // Atajos de teclado (Espacio, Flechas)
        document.addEventListener('keydown', function(e) {
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
            
            switch(e.code) {
                case 'Space':
                    e.preventDefault();
                    togglePlay();
                    break;
                case 'ArrowRight':
                    if (e.ctrlKey) { e.preventDefault(); siguienteCancion(); } 
                    else if (audioPlayer) audioPlayer.currentTime += 10;
                    break;
                case 'ArrowLeft':
                    if (e.ctrlKey) { e.preventDefault(); anteriorCancion(); } 
                    else if (audioPlayer) audioPlayer.currentTime = Math.max(0, audioPlayer.currentTime - 10);
                    break;
                case 'ArrowUp':
                    e.preventDefault();
                    if (audioPlayer) {
                        audioPlayer.volume = Math.min(1, audioPlayer.volume + 0.1);
                        actualizarVolumenUI(audioPlayer.volume);
                    }
                    break;
                case 'ArrowDown':
                    e.preventDefault();
                    if (audioPlayer) {
                        audioPlayer.volume = Math.max(0, audioPlayer.volume - 0.1);
                        actualizarVolumenUI(audioPlayer.volume);
                    }
                    break;
                case 'KeyM':
                    var muteBtn = document.getElementById('gVolumeBtn');
                    if (muteBtn) muteBtn.click();
                    break;
            }
        });
    }

    // ==================== EXPONER GLOBALMENTE ====================
    window.agregarACola = agregarACola;
    window.quitarDeCola = quitarDeCola;
    window.reproducirDesdeColaIndex = reproducirDesdeColaIndex;
    window.reproducirCancion = reproducirCancion;
    window.showToast = showToast;
    window.cargarCancionesEnLista = cargarCancionesEnLista;
    window.marcarCancionActiva = marcarCancionActiva;

    // ✅ NUEVO: Exponer funciones para obtener canción actual (para reseñas)
    window.getMuuuCurrentId = function() {
        return currentSongId;
    };
    window.getMuuuCurrentSongData = function() {
        return currentSongData;
    };

    console.log('🐮 MuuuPlayer Limpio y Cargado');

})();

/* ==========================================
   2. LÓGICA DEL SISTEMA DE RESEÑAS
   ========================================== */
(function() {
    var globalReviewModal = document.getElementById('globalReviewModal');
    var currentUserRatingGlobal = 0;

    function getCSRFToken() {
        var input = document.querySelector('[name=csrfmiddlewaretoken]');
        if (input) return input.value;
        var cookie = document.cookie.split(';').find(function(c) {
            return c.trim().startsWith('csrftoken=');
        });
        return cookie ? cookie.split('=')[1] : '';
    }

    // BOTÓN COMENTARIO/RESEÑA DEL PLAYER
    var reviewBtn = document.getElementById('gPlayerReviewBtn');
    if (reviewBtn) {
        reviewBtn.addEventListener('click', function() {
            // 1. Obtener ID real desde el módulo Player
            var songId = window.getMuuuCurrentId ? window.getMuuuCurrentId() : null;
            var songData = window.getMuuuCurrentSongData ? window.getMuuuCurrentSongData() : null;

            if (!songId) {
                if(window.showToast) window.showToast('Primero reproduce una canción', 'error');
                return;
            }

            // 2. Llenar modal con datos
            var title = songData ? songData.titulo : 'Canción';
            var artist = songData ? songData.artista : 'Artista';
            var cover = songData ? songData.portada : '';

            document.getElementById('gReviewSongTitle').textContent = title;
            document.getElementById('gReviewSongArtist').textContent = artist;
            document.getElementById('gReviewSongCover').src = cover || 'https://via.placeholder.com/70?text=🎵';
            
            // 3. Resetear formulario
            currentUserRatingGlobal = 0;
            actualizarEstrellasGlobal(0);
            document.getElementById('gCommentInput').value = '';
            
            // 4. Guardar ID en el modal para usarlo al enviar
            globalReviewModal.dataset.currentSongId = songId;
            
            // 5. Cargar reseñas existentes
            cargarResenasGlobal(songId);
            
            // 6. Mostrar modal
            globalReviewModal.classList.add('active');
        });
    }

    var closeBtn = document.getElementById('closeGlobalReviewModal');
    if (closeBtn) {
        closeBtn.addEventListener('click', function() {
            globalReviewModal.classList.remove('active');
        });
    }

    if (globalReviewModal) {
        globalReviewModal.addEventListener('click', function(e) {
            if (e.target === this) {
                this.classList.remove('active');
            }
        });
    }

    var ratingInput = document.getElementById('gRatingInput');
    if (ratingInput) {
        ratingInput.querySelectorAll('.star-input').forEach(function(star) {
            star.addEventListener('click', function(e) {
                e.preventDefault();
                currentUserRatingGlobal = parseInt(this.dataset.rating);
                actualizarEstrellasGlobal(currentUserRatingGlobal);
            });
            star.addEventListener('mouseenter', function() {
                var rating = parseInt(this.dataset.rating);
                ratingInput.querySelectorAll('.star-input').forEach(function(s, i) {
                    s.textContent = (i < rating) ? '★' : '☆';
                });
            });
        });
        ratingInput.addEventListener('mouseleave', function() {
            actualizarEstrellasGlobal(currentUserRatingGlobal);
        });
    }

    function actualizarEstrellasGlobal(rating) {
        document.querySelectorAll('#gRatingInput .star-input').forEach(function(star, index) {
            star.textContent = (index < rating) ? '★' : '☆';
            star.classList.toggle('active', index < rating);
        });
    }

    function cargarResenasGlobal(cancionId) {
        fetch('/api/resenas/cancion/' + cancionId + '/')
            .then(function(response) { return response.json(); })
            .then(function(data) {
                if (data.success) {
                    document.getElementById('gRatingPromedio').textContent = data.promedio_rating.toFixed(1);
                    document.getElementById('gTotalRatings').textContent = data.total_ratings;
                    actualizarRatingStarsGlobal(data.promedio_rating);
                    if (data.user_rating > 0) {
                        currentUserRatingGlobal = data.user_rating;
                        actualizarEstrellasGlobal(currentUserRatingGlobal);
                    }
                    calcularDistribucionGlobal(data.resenas);
                    mostrarResenasGlobal(data.resenas);
                    var reviewBtn = document.getElementById('gPlayerReviewBtn');
                    if (reviewBtn) {
                        reviewBtn.classList.toggle('has-review', data.user_rating > 0);
                    }
                }
            })
            .catch(function(error) {
                console.error('Error cargando reseñas:', error);
            });
    }

    function actualizarRatingStarsGlobal(promedio) {
        var starsHtml = '';
        for (var i = 1; i <= 5; i++) {
            starsHtml += (i <= Math.round(promedio)) ? '★' : '☆';
        }
        document.getElementById('gRatingStarsBig').textContent = starsHtml;
    }

    function calcularDistribucionGlobal(resenas) {
        var distribucion = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0};
        var total = 0;
        resenas.forEach(function(r) {
            if (r.rating) {
                distribucion[r.rating]++;
                total++;
            }
        });
        for (var i = 1; i <= 5; i++) {
            var porcentaje = total > 0 ? (distribucion[i] / total) * 100 : 0;
            var bar = document.getElementById('gBar' + i);
            if (bar) bar.style.width = porcentaje + '%';
        }
    }

    function mostrarResenasGlobal(resenas) {
        var lista = document.getElementById('gReviewsList');
        var count = document.getElementById('gReviewsCount');
        count.textContent = resenas.length + ' reseña' + (resenas.length !== 1 ? 's' : '');
        if (resenas.length === 0) {
            lista.innerHTML = '<div class="no-reviews-global">' +
                '<div class="no-reviews-icon"><i class="fa-regular fa-comment-dots"></i></div>' +
                '<p>Sé el primero en dejar una reseña</p>' +
            '</div>';
            return;
        }
        lista.innerHTML = resenas.map(function(r) {
            var avatar = r.foto_perfil ?
                '<img src="' + r.foto_perfil + '" alt="">' :
                r.nombre.charAt(0).toUpperCase();
            var starsHtml = '';
            for (var i = 1; i <= 5; i++) {
                starsHtml += (i <= r.rating) ? '★' : '☆';
            }
            return '<div class="review-item-global" data-id="' + r.id + '">' +
                '<div class="review-header-global">' +
                    '<div class="review-user-global">' +
                        '<div class="review-avatar-global">' + avatar + '</div>' +
                        '<div class="review-user-info-global">' +
                            '<h5>' + r.nombre + (r.apellido ? ' ' + r.apellido.charAt(0) + '.' : '') + '</h5>' +
                            '<span class="review-date-global">' + r.fecha + '</span>' +
                        '</div>' +
                    '</div>' +
                    '<div class="review-stars-global">' + starsHtml + '</div>' +
                '</div>' +
                (r.comentario ? '<p class="review-comment-global">' + escapeHtml(r.comentario) + '</p>' : '') +
                '<div class="review-actions-global">' +
                    '<button class="review-action-btn-global like-btn-g' + (r.user_liked ? ' liked' : '') + '" data-id="' + r.id + '">' +
                        '<i class="fa-solid fa-thumbs-up"></i> <span>' + r.likes + '</span>' +
                    '</button>' +
                    '<button class="review-action-btn-global dislike-btn-g' + (r.user_disliked ? ' disliked' : '') + '" data-id="' + r.id + '">' +
                        '<i class="fa-solid fa-thumbs-down"></i> <span>' + r.dislikes + '</span>' +
                    '</button>' +
                '</div>' +
            '</div>';
        }).join('');
        lista.querySelectorAll('.like-btn-g').forEach(function(btn) {
            btn.addEventListener('click', function() {
                reaccionarResenaGlobal(this.dataset.id, 'like');
            });
        });
        lista.querySelectorAll('.dislike-btn-g').forEach(function(btn) {
            btn.addEventListener('click', function() {
                reaccionarResenaGlobal(this.dataset.id, 'dislike');
            });
        });
    }

    function escapeHtml(text) {
        var div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    var submitBtn = document.getElementById('gSubmitReviewBtn');
    if (submitBtn) {
        submitBtn.addEventListener('click', function() {
            var songId = globalReviewModal.dataset.currentSongId;

            if (currentUserRatingGlobal === 0) {
                showToast('Selecciona una calificación', 'error');
                return;
            }
            if (!songId) {
                showToast('Error: No hay canción seleccionada', 'error');
                return;
            }
            var comentario = document.getElementById('gCommentInput').value.trim();
            this.disabled = true;
            this.textContent = 'Publicando...';
            var btn = this;
            fetch('/api/resena/agregar/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                },
                body: JSON.stringify({
                    cancion_id: songId,
                    rating: currentUserRatingGlobal,
                    comentario: comentario
                })
            })
            .then(function(response) { return response.json(); })
            .then(function(data) {
                btn.disabled = false;
                btn.textContent = 'Publicar reseña';
                if (data.success) {
                    showToast(data.message);
                    document.getElementById('gCommentInput').value = '';
                    cargarResenasGlobal(songId);
                } else {
                    showToast(data.message || 'Error', 'error');
                }
            })
            .catch(function(error) {
                btn.disabled = false;
                btn.textContent = 'Publicar reseña';
                showToast('Error de conexión', 'error');
            });
        });
    }

    function reaccionarResenaGlobal(resenaId, tipo) {
        var songId = globalReviewModal.dataset.currentSongId;
        fetch('/api/resena/like/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify({
                resena_id: resenaId,
                tipo: tipo
            })
        })
        .then(function(response) { return response.json(); })
        .then(function(data) {
            if (data.success && songId) {
                cargarResenasGlobal(songId);
            }
        })
        .catch(function(error) {
            console.error(error);
        });
    }

    window.abrirResenasGlobal = function(songId, titulo, artista, portada) {
        if (!songId) return;
        document.getElementById('gReviewSongTitle').textContent = titulo || 'Canción';
        document.getElementById('gReviewSongArtist').textContent = artista || 'Artista';
        document.getElementById('gReviewSongCover').src = portada || 'https://via.placeholder.com/70?text=🎵';
        currentUserRatingGlobal = 0;
        actualizarEstrellasGlobal(0);
        document.getElementById('gCommentInput').value = '';
        globalReviewModal.dataset.currentSongId = songId; // Guardar ID
        cargarResenasGlobal(songId);
        globalReviewModal.classList.add('active');
    };
    console.log('💬 Sistema de reseñas global inicializado');
})();


/* ==========================================
   3. LÓGICA DEL SPA (SINGLE PAGE APPLICATION)
   ========================================== */
(function() {
    var spaContent = document.getElementById('spaContent');
    var spaLoading = document.getElementById('spaLoading');
    var scriptCounter = 0;

    function esURLInterna(url) {
        try {
            var urlObj = new URL(url, window.location.origin);
            return urlObj.origin === window.location.origin &&
                   url.indexOf('/admin/') === -1 &&
                   url.indexOf('/static/') === -1 &&
                   url.indexOf('/media/') === -1 &&
                   url.indexOf('.js') === -1 &&
                   url.indexOf('.css') === -1 &&
                   url.indexOf('.png') === -1 &&
                   url.indexOf('.jpg') === -1;
        } catch(e) {
            return false;
        }
    }

    function mostrarLoading() {
        if (spaLoading) spaLoading.classList.add('active');
    }

    function ocultarLoading() {
        if (spaLoading) spaLoading.classList.remove('active');
    }

    function limpiarScriptsAnteriores() {
        document.querySelectorAll('script[data-spa-script]').forEach(function(s) {
            s.remove();
        });
    }

    // ========== NUEVO: Limpiar CSS de páginas anteriores ==========
    function limpiarCSSAnteriores() {
        // Eliminar estilos de página específicos
        var pageStyles = document.getElementById('pageStyles');
        if (pageStyles) pageStyles.remove();
        
        // Eliminar CSS externos de páginas específicas (como perfil_usuario.css)
        document.querySelectorAll('link[data-spa-css]').forEach(function(link) {
            link.remove();
        });
    }

    function ejecutarScript(codigo) {
        scriptCounter++;
        var script = document.createElement('script');
        script.setAttribute('data-spa-script', 'true');
        script.id = 'spa-script-' + scriptCounter;
        var codigoLimpio = codigo
            .replace(/\blet\s+/g, 'var ')
            .replace(/\bconst\s+/g, 'var ');
        script.textContent = '(function(){try{' + codigoLimpio + '}catch(e){console.error("Error SPA script:",e);}})();';
        document.body.appendChild(script);
    }

    async function cargarPagina(url, pushState) {
        if (pushState === undefined) pushState = true;
        mostrarLoading();
        
        try {
            var response = await fetch(url, {
                headers: { 'X-SPA-Request': 'true' }
            });
            if (!response.ok) throw new Error('Error al cargar');
            var html = await response.text();
            var parser = new DOMParser();
            var doc = parser.parseFromString(html, 'text/html');
            var nuevoContenido = doc.getElementById('spaContent');
            if (!nuevoContenido) {
                nuevoContenido = doc.querySelector('.app-container') || doc.body;
            }
            
            // ========== LIMPIAR ANTES DE CARGAR NUEVO CONTENIDO ==========
            limpiarScriptsAnteriores();
            limpiarCSSAnteriores();
            
            var contenidoHTML = nuevoContenido.innerHTML;
            var tempDiv = document.createElement('div');
            tempDiv.innerHTML = contenidoHTML;
            var scripts = [];
            tempDiv.querySelectorAll('script').forEach(function(s) {
                if (!s.src || s.src.indexOf('global_player') === -1) {
                    scripts.push(s.textContent);
                }
                s.remove();
            });
            doc.querySelectorAll('script[data-page-script]').forEach(function(s) {
                if (!s.src || s.src.indexOf('global_player') === -1) {
                    scripts.push(s.textContent);
                }
            });
            
            spaContent.innerHTML = tempDiv.innerHTML;
            
            // Actualizar título
            var nuevoTitulo = doc.querySelector('title');
            if (nuevoTitulo) {
                document.title = nuevoTitulo.textContent;
            }
            
            // ========== CARGAR CSS EXTERNOS (como perfil_usuario.css) ==========
            doc.querySelectorAll('link[rel="stylesheet"]').forEach(function(link) {
                var href = link.getAttribute('href');
                // Solo cargar CSS específicos de página (no main.css ni font-awesome)
                if (href && 
                    href.indexOf('main.css') === -1 && 
                    href.indexOf('font-awesome') === -1 &&
                    href.indexOf('fonts.googleapis') === -1) {
                    
                    // Verificar si ya existe
                    var existente = document.querySelector('link[href="' + href + '"]');
                    if (!existente) {
                        var nuevoLink = document.createElement('link');
                        nuevoLink.rel = 'stylesheet';
                        nuevoLink.href = href;
                        nuevoLink.setAttribute('data-spa-css', 'true');
                        document.head.appendChild(nuevoLink);
                        console.log('CSS cargado:', href);
                    }
                }
            });
            
            // ========== CARGAR ESTILOS INLINE ==========
            var styles = doc.querySelectorAll('style');
            if (styles.length > 0) {
                var pageStyles = document.createElement('style');
                pageStyles.id = 'pageStyles';
                styles.forEach(function(style) {
                    pageStyles.textContent += style.textContent;
                });
                document.head.appendChild(pageStyles);
            }
            
            if (pushState) {
                history.pushState({ url: url }, '', url);
            }
            window.scrollTo(0, 0);
            
            // Reconectar con el Reproductor
            if (typeof window.cargarCancionesEnLista === 'function') {
                window.cargarCancionesEnLista();
            }
            
            // Ejecutar scripts de la página
            setTimeout(function() {
                scripts.forEach(function(codigo) {
                    if (codigo.trim()) {
                        ejecutarScript(codigo);
                    }
                });
                vincularEventosCanciones();
                
                // ========== REINICIALIZAR SISTEMA DE RESEÑAS ==========
                reinicializarResenas();
                
                console.log('Página cargada via SPA:', url);
            }, 100);
            
        } catch (error) {
            console.error('Error SPA:', error);
            window.location.href = url;
        } finally {
            ocultarLoading();
        }
    }

    // ========== NUEVO: Reinicializar sistema de reseñas ==========
    function reinicializarResenas() {
        var reviewBtn = document.getElementById('gPlayerReviewBtn');
        var globalReviewModal = document.getElementById('globalReviewModal');
        
        if (reviewBtn && globalReviewModal) {
            // Clonar para eliminar eventos anteriores
            var nuevoBtn = reviewBtn.cloneNode(true);
            reviewBtn.parentNode.replaceChild(nuevoBtn, reviewBtn);
            
            nuevoBtn.addEventListener('click', function() {
                var songId = window.getMuuuCurrentId ? window.getMuuuCurrentId() : null;
                var songData = window.getMuuuCurrentSongData ? window.getMuuuCurrentSongData() : null;

                if (!songId) {
                    if(window.showToast) window.showToast('Primero reproduce una canción', 'error');
                    return;
                }

                if (typeof window.abrirResenasGlobal === 'function') {
                    window.abrirResenasGlobal(
                        songId,
                        songData ? songData.titulo : 'Canción',
                        songData ? songData.artista : 'Artista',
                        songData ? songData.portada : ''
                    );
                }
            });
        }
    }

    function vincularEventosCanciones() {
        document.querySelectorAll('.song-row, .song-card').forEach(function(el) {
            if (el.dataset.spaVinculado) return;
            el.dataset.spaVinculado = 'true';
            el.addEventListener('click', function(e) {
                if (e.target.closest('button, .control-btn, .remove-btn, .menu-btn, .dropdown-menu, .rating, .star, a')) {
                    return;
                }
                var songId = this.dataset.id;
                if (songId && typeof window.reproducirCancion === 'function') {
                    window.reproducirCancion(songId);
                }
            });
        });
        document.querySelectorAll('.play-overlay, .play-icon').forEach(function(el) {
            if (el.dataset.spaVinculado) return;
            el.dataset.spaVinculado = 'true';
            el.addEventListener('click', function(e) {
                e.stopPropagation();
                var card = this.closest('[data-id]');
                if (card && typeof window.reproducirCancion === 'function') {
                    window.reproducirCancion(card.dataset.id);
                }
            });
        });
    }

    document.addEventListener('click', function(e) {
        var link = e.target.closest('a');
        if (!link) return;
        var href = link.getAttribute('href');
        if (!href ||
            href.indexOf('#') === 0 ||
            href.indexOf('javascript:') === 0 ||
            href.indexOf('mailto:') === 0 ||
            href.indexOf('tel:') === 0 ||
            link.target === '_blank' ||
            link.hasAttribute('download') ||
            !esURLInterna(href)) {
            return;
        }
        e.preventDefault();
        cargarPagina(href);
    });

    window.addEventListener('popstate', function(e) {
        if (e.state && e.state.url) {
            cargarPagina(e.state.url, false);
        } else {
            cargarPagina(window.location.href, false);
        }
    });

    history.replaceState({ url: window.location.href }, '', window.location.href);
    setTimeout(vincularEventosCanciones, 100);
    window.navegarSPA = cargarPagina;
    window.vincularEventosCanciones = vincularEventosCanciones;
    console.log('Sistema SPA inicializado');
})();

// === SIDEBAR === //
document.addEventListener('DOMContentLoaded', function() {
    
    const sidebar = document.querySelector('.sidebar');
    const toggleBtn = document.getElementById('sidebarToggleBtn');

    if (sidebar && toggleBtn) {
        toggleBtn.addEventListener('click', function() {
            // Esta línea es la que hace la magia:
            sidebar.classList.toggle('collapsed');
        });
    }

});

// ============================================================
    //  ACTUALIZAR LA LISTA VISUAL DE LA COLA (VERSIÓN DASHBOARD)
    // ============================================================
    function actualizarUIColaModal() {
        var listaContainer = document.getElementById('gQueueList');
        
        if (!listaContainer) return;
        
        // 1. Si la cola está vacía, mostramos el mensaje bonito
        if (queue.length === 0) {
            listaContainer.innerHTML = 
                '<div class="queue-empty-state" style="text-align: center; padding: 40px 20px; color: #666;">' +
                    '<i class="fa-solid fa-music" style="font-size: 24px; margin-bottom: 10px; display: block;"></i>' +
                    '<p style="font-size: 13px;">La cola está vacía</p>' +
                '</div>';
            return;
        }
        
        // 2. Si hay canciones, generamos el HTML con las clases "mini-..."
        var html = '';
        for (var i = 0; i < queue.length; i++) {
            var song = queue[i];
            
            // Portada o Ícono si no tiene
            var imgHtml = song.portada 
                ? '<img src="' + song.portada + '" alt="" style="width:100%; height:100%; object-fit:cover;">' 
                : '<div style="width:100%; height:100%; display:flex; align-items:center; justify-content:center; background:#222;"><i class="fa-solid fa-music" style="color:#555;"></i></div>';

            html += '<div class="mini-queue-item" data-index="' + i + '">' +
                        // A. Portada Pequeña
                        '<div class="mini-cover">' + imgHtml + '</div>' +
                        
                        // B. Info (Título y Artista)
                        '<div class="mini-info">' +
                            '<div class="mini-title">' + escapeHtml(song.titulo) + '</div>' +
                            '<div class="mini-artist">' + escapeHtml(song.artista) + '</div>' +
                        '</div>' +
                        
                        // C. Botón Eliminar (X)
                        '<button class="btn-icon queue-remove-btn" data-index="' + i + '" title="Quitar de la cola" style="opacity:0.6;">' +
                            '<i class="fa-solid fa-xmark"></i>' +
                        '</button>' +
                    '</div>';
        }
        listaContainer.innerHTML = html;
        
        // 3. Vincular eventos (Click para borrar)
        listaContainer.querySelectorAll('.queue-remove-btn').forEach(function(btn) {
            btn.addEventListener('click', function(e) {
                e.stopPropagation(); // Para que no reproduzca la canción al borrarla
                quitarDeCola(parseInt(this.dataset.index));
            });
        });

        // 4. Vincular eventos (Click para reproducir esa canción)
        listaContainer.querySelectorAll('.mini-queue-item').forEach(function(item) {
            item.addEventListener('click', function(e) {
                // Si el click fue en el botón de borrar, no hacemos nada aquí
                if (e.target.closest('.queue-remove-btn')) return;
                
                reproducirDesdeColaIndex(parseInt(this.dataset.index));
            });
        });
    }