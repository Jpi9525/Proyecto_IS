// ========== REPRODUCTOR GLOBAL PERSISTENTE ==========

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    audioPlayer = document.getElementById('audioPlayer');
    if (!audioPlayer) return;
    
    cargarCancionesEnLista();
    restaurarEstadoReproductor();
    inicializarEventosReproductor();
    
    console.log('✅ Reproductor global inicializado');
});

// Cargar canciones de la página actual a la lista
function cargarCancionesEnLista() {
    songsList = [];
    document.querySelectorAll('.song-card, .song-row').forEach((card, index) => {
        songsList.push({
            id: card.dataset.id,
            titulo: card.querySelector('.song-title')?.textContent || card.dataset.titulo || 'Sin título',
            artista: card.querySelector('.song-artist')?.textContent || card.dataset.artista || 'Artista',
            portada: card.querySelector('.song-cover img, .song-cover-small img')?.src || card.dataset.portada || '',
            ruta: card.dataset.ruta || '',
            index: index
        });
    });
}

// Guardar estado en localStorage
function guardarEstadoReproductor() {
    const estado = {
        songId: currentSongId,
        isPlaying: isPlaying,
        currentTime: audioPlayer ? audioPlayer.currentTime : 0,
        volume: audioPlayer ? audioPlayer.volume : 0.7,
        songData: songsList.find(s => s.id == currentSongId) || null
    };
    localStorage.setItem('reproductorEstado', JSON.stringify(estado));
}

// Restaurar estado desde localStorage
function restaurarEstadoReproductor() {
    const estadoGuardado = localStorage.getItem('reproductorEstado');
    if (!estadoGuardado) return;
    
    try {
        const estado = JSON.parse(estadoGuardado);
        
        if (estado.songData) {
            // Restaurar UI
            const playerTitle = document.getElementById('playerTitle');
            const playerArtist = document.getElementById('playerArtist');
            const playerCover = document.getElementById('playerCover');
            
            if (playerTitle) playerTitle.textContent = estado.songData.titulo;
            if (playerArtist) playerArtist.textContent = estado.songData.artista;
            if (playerCover && estado.songData.portada) {
                playerCover.innerHTML = `<img src="${estado.songData.portada}">`;
            }
            
            currentSongId = estado.songId;
            
            // Restaurar audio si hay ruta
            if (estado.songData.ruta && audioPlayer) {
                audioPlayer.src = estado.songData.ruta;
                audioPlayer.currentTime = estado.currentTime || 0;
                audioPlayer.volume = estado.volume || 0.7;
                
                // Actualizar volumen visual
                const volumeFill = document.querySelector('.volume-fill');
                if (volumeFill) {
                    volumeFill.style.width = (estado.volume * 100) + '%';
                }
                
                // Continuar reproduciendo si estaba reproduciéndose
                if (estado.isPlaying) {
                    audioPlayer.play()
                        .then(() => {
                            isPlaying = true;
                            actualizarBotonPlay();
                        })
                        .catch(() => {
                            console.log('Autoplay bloqueado, click para continuar');
                        });
                }
            }
        }
    } catch (e) {
        console.error('Error restaurando estado:', e);
    }
}

// Guardar estado antes de salir de la página
window.addEventListener('beforeunload', function() {
    guardarEstadoReproductor();
});

// Guardar estado periódicamente
setInterval(guardarEstadoReproductor, 1000);

// ========== FUNCIONES DEL REPRODUCTOR ==========

function reproducirCancion(songId) {
    // Buscar en la lista actual o en localStorage
    let song = songsList.find(s => s.id == songId);
    
    // Si no está en la lista, buscar en el DOM
    if (!song) {
        const card = document.querySelector(`[data-id="${songId}"]`);
        if (card) {
            song = {
                id: songId,
                titulo: card.querySelector('.song-title')?.textContent || card.dataset.titulo || 'Sin título',
                artista: card.querySelector('.song-artist')?.textContent || card.dataset.artista || 'Artista',
                portada: card.querySelector('.song-cover img, .song-cover-small img')?.src || '',
                ruta: card.dataset.ruta || ''
            };
        }
    }
    
    if (!song) return;
    
    // Actualizar UI
    const playerTitle = document.getElementById('playerTitle');
    const playerArtist = document.getElementById('playerArtist');
    const playerCover = document.getElementById('playerCover');
    
    if (playerTitle) playerTitle.textContent = song.titulo;
    if (playerArtist) playerArtist.textContent = song.artista;
    if (playerCover && song.portada) {
        playerCover.innerHTML = `<img src="${song.portada}">`;
    }
    
    currentSongId = songId;
    
    // Reproducir audio
    if (song.ruta && song.ruta !== '' && song.ruta !== 'None' && audioPlayer) {
        audioPlayer.src = song.ruta;
        audioPlayer.play()
            .then(() => {
                isPlaying = true;
                actualizarBotonPlay();
                guardarEstadoReproductor();
            })
            .catch(error => {
                console.log('Error reproduciendo:', error);
                isPlaying = true;
                actualizarBotonPlay();
                showToast(`Reproduciendo: ${song.titulo}`, 'success');
            });
    } else {
        isPlaying = true;
        actualizarBotonPlay();
        showToast(`Reproduciendo: ${song.titulo}`, 'success');
    }
    
    // Marcar canción activa visualmente
    document.querySelectorAll('.song-card, .song-row').forEach(c => c.classList.remove('playing'));
    const activeCard = document.querySelector(`[data-id="${songId}"]`);
    if (activeCard) activeCard.classList.add('playing');
    
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
        audioPlayer.play().catch(() => {});
    }
    isPlaying = true;
    actualizarBotonPlay();
    guardarEstadoReproductor();
}

function togglePlay() {
    if (!currentSongId) {
        const firstCard = document.querySelector('.song-card, .song-row');
        if (firstCard) reproducirCancion(firstCard.dataset.id);
        return;
    }
    
    if (isPlaying) {
        pausarCancion();
    } else {
        reanudarCancion();
    }
}

function siguienteCancion() {
    if (!currentSongId || songsList.length === 0) return;
    const idx = songsList.findIndex(s => s.id == currentSongId);
    const nextIdx = (idx + 1) % songsList.length;
    reproducirCancion(songsList[nextIdx].id);
}

function anteriorCancion() {
    if (!currentSongId || songsList.length === 0) return;
    const idx = songsList.findIndex(s => s.id == currentSongId);
    const prevIdx = idx === 0 ? songsList.length - 1 : idx - 1;
    reproducirCancion(songsList[prevIdx].id);
}

function actualizarBotonPlay() {
    const mainPlayBtn = document.getElementById('mainPlayBtn');
    if (mainPlayBtn) {
        mainPlayBtn.innerHTML = isPlaying ? '⏸' : '▶';
    }
}

function formatTime(seconds) {
    if (isNaN(seconds)) return '0:00';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

// ========== TOAST ==========
function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    if (!toast) return;
    toast.textContent = message;
    toast.className = `toast ${type} show`;
    setTimeout(() => toast.classList.remove('show'), 3000);
}

// ========== INICIALIZAR EVENTOS ==========
function inicializarEventosReproductor() {
    // Botón play principal
    const mainPlayBtn = document.getElementById('mainPlayBtn');
    if (mainPlayBtn) {
        mainPlayBtn.addEventListener('click', togglePlay);
    }
    
    // Botones de navegación
    document.querySelectorAll('.control-buttons-main .player-btn').forEach((btn, i) => {
        btn.addEventListener('click', () => {
            if (i === 0) anteriorCancion();
            if (i === 1 && audioPlayer) audioPlayer.currentTime = Math.max(0, audioPlayer.currentTime - 10);
            if (i === 3 && audioPlayer) audioPlayer.currentTime = Math.min(audioPlayer.duration || 0, audioPlayer.currentTime + 10);
            if (i === 4) siguienteCancion();
        });
    });
    
    // Click en play de cada canción
    document.querySelectorAll('.play-icon').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.stopPropagation();
            const card = this.closest('.song-card, .song-row');
            if (card) reproducirCancion(card.dataset.id);
        });
    });
    
    // Click en filas de canciones (para ver_album, etc.)
    document.querySelectorAll('.song-row').forEach(row => {
        row.addEventListener('click', function() {
            reproducirCancion(this.dataset.id);
        });
    });
    
    // Eventos del audio
    if (audioPlayer) {
        audioPlayer.addEventListener('ended', siguienteCancion);
        
        audioPlayer.addEventListener('timeupdate', function() {
            if (audioPlayer.duration) {
                const progress = (audioPlayer.currentTime / audioPlayer.duration) * 100;
                const progressFill = document.querySelector('.progress-fill');
                if (progressFill) progressFill.style.width = progress + '%';
                
                const times = document.querySelectorAll('.time');
                if (times[0]) times[0].textContent = formatTime(audioPlayer.currentTime);
                if (times[1]) times[1].textContent = formatTime(audioPlayer.duration);
            }
        });
    }
    
    // Barra de progreso
    const progressTrack = document.querySelector('.progress-track');
    if (progressTrack && audioPlayer) {
        progressTrack.addEventListener('click', function(e) {
            if (audioPlayer.duration) {
                const rect = this.getBoundingClientRect();
                const percent = (e.clientX - rect.left) / rect.width;
                audioPlayer.currentTime = percent * audioPlayer.duration;
            }
        });
    }
    
    // Volumen
    const volumeSlider = document.querySelector('.volume-slider');
    if (volumeSlider && audioPlayer) {
        volumeSlider.addEventListener('click', function(e) {
            const rect = this.getBoundingClientRect();
            const percent = (e.clientX - rect.left) / rect.width;
            const volumeFill = document.querySelector('.volume-fill');
            if (volumeFill) volumeFill.style.width = (percent * 100) + '%';
            audioPlayer.volume = percent;
            guardarEstadoReproductor();
        });
    }
}

// ========== CSRF TOKEN ==========
function getCSRFToken() {
    const input = document.querySelector('[name=csrfmiddlewaretoken]');
    return input ? input.value : '';
}