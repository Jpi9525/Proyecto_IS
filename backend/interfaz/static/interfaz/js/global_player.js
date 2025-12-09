// ============================================================
// REPRODUCTOR GLOBAL PERSISTENTE - MuuuSica
// Versión SPA - La música NUNCA se detiene
// ============================================================

// Variables globales
let currentSongId = null;
let isPlaying = false;
let audioPlayer = null;
let songsList = [];
let isShuffle = false;
let repeatMode = 'none';
let currentSongData = null;

// ==================== INICIALIZACIÓN ====================
document.addEventListener('DOMContentLoaded', function() {
    audioPlayer = document.getElementById('gAudioPlayer');
    if (!audioPlayer) {
        console.warn('⚠️ No se encontró elemento de audio');
        return;
    }
    
    cargarCancionesEnLista();
    restaurarEstadoReproductor();
    inicializarEventosReproductor();
    
    console.log('✅ Reproductor global inicializado con', songsList.length, 'canciones');
});

// ==================== LISTA DE CANCIONES ====================
function cargarCancionesEnLista() {
    const cancionesEnPagina = [];
    
    document.querySelectorAll('[data-id][data-titulo], [data-id][data-ruta], .song-row[data-id], .song-card[data-id]').forEach((el, index) => {
        const song = {
            id: el.dataset.id,
            titulo: el.dataset.titulo || el.querySelector('.song-title, .song-info h4')?.textContent || 'Sin título',
            artista: el.dataset.artista || el.querySelector('.song-artist, .song-info p')?.textContent || 'Artista desconocido',
            portada: el.dataset.portada || el.querySelector('img')?.src || '',
            ruta: el.dataset.ruta || '',
            index: index
        };
        
        if (!cancionesEnPagina.find(s => s.id === song.id)) {
            cancionesEnPagina.push(song);
        }
    });
    
    // Solo actualizar si hay canciones en la página
    // Si no hay, mantener la lista anterior
    if (cancionesEnPagina.length > 0) {
        songsList = cancionesEnPagina;
        
        // Mantener la canción actual en la lista si no está
        if (currentSongData && !songsList.find(s => s.id == currentSongData.id)) {
            songsList.unshift(currentSongData);
        }
        
        // Guardar lista en localStorage
        localStorage.setItem('muuusica_playlist', JSON.stringify(songsList));
    } else {
        // Si no hay canciones en la página, cargar del localStorage
        const savedPlaylist = localStorage.getItem('muuusica_playlist');
        if (savedPlaylist && songsList.length === 0) {
            try {
                songsList = JSON.parse(savedPlaylist);
            } catch(e) {
                console.warn('Error cargando playlist guardada');
            }
        }
    }
    
    // Marcar canción activa
    if (currentSongId) {
        marcarCancionActiva(currentSongId);
    }
    
    console.log('🎵 Lista actualizada:', songsList.length, 'canciones');
}
// ==================== PERSISTENCIA ====================
function guardarEstadoReproductor() {
    const songData = currentSongData || songsList.find(s => s.id == currentSongId) || null;
    
    const estado = {
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
    // Primero restaurar la playlist
    const savedPlaylist = localStorage.getItem('muuusica_playlist');
    if (savedPlaylist) {
        try {
            const playlist = JSON.parse(savedPlaylist);
            if (playlist && playlist.length > 0) {
                songsList = playlist;
                console.log('📋 Playlist restaurada:', songsList.length, 'canciones');
            }
        } catch(e) {
            console.warn('Error cargando playlist:', e);
        }
    }
    
    // Luego restaurar el estado del reproductor
    const saved = localStorage.getItem('muuusica_player');
    if (!saved) return;
    
    try {
        const estado = JSON.parse(saved);
        
        isShuffle = estado.isShuffle || false;
        repeatMode = estado.repeatMode || 'none';
        actualizarBotonesExtra();
        
        if (estado.songData) {
            currentSongId = estado.songId;
            currentSongData = estado.songData;
            
            // Asegurar que la canción actual esté en la lista
            if (currentSongData && !songsList.find(s => s.id == currentSongData.id)) {
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
                }, { once: true });
                
                audioPlayer.load();
                actualizarVolumenUI(estado.volume || 0.7);
            }
            
            console.log('📂 Estado restaurado:', estado.songData.titulo);
        }
    } catch (e) {
        console.error('Error restaurando estado:', e);
    }
}

// Guardar periódicamente
setInterval(guardarEstadoReproductor, 1000);

// ==================== REPRODUCCIÓN ====================
function reproducirCancion(songId, playlistOverride = null) {
    if (playlistOverride && playlistOverride.length > 0) {
        songsList = playlistOverride;
    }
    
    let song = songsList.find(s => s.id == songId);
    
    if (!song) {
        const el = document.querySelector(`[data-id="${songId}"]`);
        if (el) {
            song = {
                id: songId,
                titulo: el.dataset.titulo || el.querySelector('.song-title, .song-info h4')?.textContent || 'Sin título',
                artista: el.dataset.artista || el.querySelector('.song-artist, .song-info p')?.textContent || 'Artista',
                portada: el.dataset.portada || el.querySelector('img')?.src || '',
                ruta: el.dataset.ruta || ''
            };
            if (!songsList.find(s => s.id === song.id)) {
                songsList.push(song);
            }
        }
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
            .then(() => {
                isPlaying = true;
                actualizarBotonPlay();
                guardarEstadoReproductor();
                console.log('▶️ Reproduciendo:', song.titulo);
            })
            .catch(error => {
                console.log('Error reproduciendo:', error);
                showToast(`Error al reproducir ${song.titulo}`, 'error');
            });
    } else {
        showToast(`Sin archivo de audio: ${song.titulo}`, 'error');
    }
    
    marcarCancionActiva(songId);
    guardarEstadoReproductor();
}

function pausarCancion() {
    if (audioPlayer) {
        audioPlayer.pause();
    }
    isPlaying = false;
    actualizarBotonPlay();
    guardarEstadoReproductor();
}

function reanudarCancion() {
    if (currentSongId && audioPlayer && audioPlayer.src) {
        audioPlayer.play()
            .then(() => {
                isPlaying = true;
                actualizarBotonPlay();
            })
            .catch(() => {
                console.log('No se pudo reanudar');
            });
    }
    guardarEstadoReproductor();
}

function togglePlay() {
    console.log('togglePlay llamado - currentSongId:', currentSongId, 'songsList:', songsList.length);
    
    // Si ya hay una canción cargada
    if (currentSongId && audioPlayer && audioPlayer.src) {
        if (isPlaying) {
            pausarCancion();
        } else {
            reanudarCancion();
        }
        return;
    }
    
    // Si hay canción en currentSongData pero no está cargada en el audio
    if (currentSongData && currentSongData.ruta) {
        console.log('Reproduciendo canción guardada:', currentSongData.titulo);
        reproducirCancion(currentSongData.id);
        return;
    }
    
    // Intentar con la lista actual
    if (songsList.length > 0) {
        console.log('Reproduciendo primera de la lista:', songsList[0].titulo);
        reproducirCancion(songsList[0].id);
        return;
    }
    
    // Intentar con una canción en la página
    const firstSong = document.querySelector('[data-id][data-ruta]');
    if (firstSong && firstSong.dataset.ruta) {
        console.log('Reproduciendo canción de la página');
        reproducirCancion(firstSong.dataset.id);
        return;
    }
    
    // Último intento: restaurar del localStorage
    const saved = localStorage.getItem('muuusica_player');
    if (saved) {
        try {
            const estado = JSON.parse(saved);
            if (estado.songData && estado.songData.ruta) {
                console.log('Restaurando del localStorage:', estado.songData.titulo);
                currentSongData = estado.songData;
                currentSongId = estado.songId;
                if (!songsList.find(s => s.id == currentSongId)) {
                    songsList.push(currentSongData);
                }
                reproducirCancion(currentSongId);
                return;
            }
        } catch(e) {
            console.error('Error parseando localStorage:', e);
        }
    }
    
    showToast('No hay canciones disponibles', 'error');
}


function siguienteCancion() {
    if (songsList.length === 0) return;
    
    let nextIndex;
    const currentIndex = songsList.findIndex(s => s.id == currentSongId);
    
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
                showToast('Fin de la lista');
                return;
            }
        }
    }
    
    reproducirCancion(songsList[nextIndex].id);
}

function anteriorCancion() {
    if (songsList.length === 0) return;
    
    const currentIndex = songsList.findIndex(s => s.id == currentSongId);
    
    if (audioPlayer && audioPlayer.currentTime > 3) {
        audioPlayer.currentTime = 0;
        return;
    }
    
    let prevIndex = currentIndex - 1;
    if (prevIndex < 0) {
        prevIndex = songsList.length - 1;
    }
    
    reproducirCancion(songsList[prevIndex].id);
}

// ==================== CONTROLES EXTRA ====================
function toggleShuffle() {
    isShuffle = !isShuffle;
    actualizarBotonesExtra();
    showToast(isShuffle ? '🔀 Aleatorio activado' : '🔀 Aleatorio desactivado');
    guardarEstadoReproductor();
}

function toggleRepeat() {
    const modes = ['none', 'all', 'one'];
    const currentIndex = modes.indexOf(repeatMode);
    repeatMode = modes[(currentIndex + 1) % modes.length];
    
    actualizarBotonesExtra();
    
    const mensajes = {
        'none': '🔁 Repetir desactivado',
        'all': '🔁 Repetir todo',
        'one': '🔂 Repetir una'
    };
    showToast(mensajes[repeatMode]);
    guardarEstadoReproductor();
}

function actualizarBotonesExtra() {
    const shuffleBtn = document.getElementById('gShuffleBtn');
    const repeatBtn = document.getElementById('gRepeatBtn');
    
    if (shuffleBtn) {
        shuffleBtn.classList.toggle('active', isShuffle);
    }
    
    if (repeatBtn) {
        repeatBtn.classList.toggle('active', repeatMode !== 'none');
        repeatBtn.textContent = repeatMode === 'one' ? '🔂' : '🔁';
    }
}

// ==================== UI ====================
function actualizarUICancion(song) {
    const playerTitle = document.getElementById('gPlayerTitle');
    const playerArtist = document.getElementById('gPlayerArtist');
    const playerCover = document.getElementById('gPlayerCover');
    
    if (playerTitle) playerTitle.textContent = song.titulo || 'Sin título';
    if (playerArtist) playerArtist.textContent = song.artista || 'Artista desconocido';
    
    if (playerCover) {
        if (song.portada && song.portada !== '') {
            playerCover.innerHTML = `<img src="${song.portada}" alt="${song.titulo}">`;
        } else {
            playerCover.innerHTML = '<div class="player-cover-placeholder">🎵</div>';
        }
    }
    
    document.title = song.titulo ? `${song.titulo} - MuuuSica` : 'MuuuSica';
}

function actualizarBotonPlay() {
    const mainPlayBtn = document.getElementById('gPlayPauseBtn');
    if (mainPlayBtn) {
        mainPlayBtn.textContent = isPlaying ? '⏸' : '▶';
        mainPlayBtn.title = isPlaying ? 'Pausar' : 'Reproducir';
    }
}

function marcarCancionActiva(songId) {
    document.querySelectorAll('.song-row, .song-card, [data-id]').forEach(el => {
        el.classList.remove('playing', 'active');
    });
    
    const activeEl = document.querySelector(`[data-id="${songId}"]`);
    if (activeEl) {
        activeEl.classList.add('playing', 'active');
    }
}

function actualizarVolumenUI(volume) {
    const volumeFill = document.getElementById('gVolumeFill');
    const volumeBtn = document.getElementById('gVolumeBtn');
    
    if (volumeFill) {
        volumeFill.style.width = (volume * 100) + '%';
    }
    
    if (volumeBtn) {
        if (volume === 0) {
            volumeBtn.textContent = '🔇';
        } else if (volume < 0.5) {
            volumeBtn.textContent = '🔉';
        } else {
            volumeBtn.textContent = '🔊';
        }
    }
}

function actualizarProgreso() {
    if (!audioPlayer || !audioPlayer.duration) return;
    
    const progress = (audioPlayer.currentTime / audioPlayer.duration) * 100;
    const progressFill = document.getElementById('gProgressFill');
    const currentTimeEl = document.getElementById('gCurrentTime');
    const totalTimeEl = document.getElementById('gTotalTime');
    
    if (progressFill) {
        progressFill.style.width = progress + '%';
    }
    
    if (currentTimeEl) {
        currentTimeEl.textContent = formatTime(audioPlayer.currentTime);
    }
    
    if (totalTimeEl) {
        totalTimeEl.textContent = formatTime(audioPlayer.duration);
    }
}

// ==================== UTILIDADES ====================
function formatTime(seconds) {
    if (isNaN(seconds) || !isFinite(seconds)) return '0:00';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    if (!toast) return;
    
    toast.textContent = message;
    toast.className = `toast ${type} show`;
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// ==================== FAVORITOS ====================
async function toggleFavorito() {
    if (!currentSongId) {
        showToast('Selecciona una canción primero', 'error');
        return;
    }
    
    const likeBtn = document.getElementById('gPlayerLikeBtn');
    
    try {
        const response = await fetch('/api/favorito/toggle/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ cancion_id: currentSongId })
        });
        
        const data = await response.json();
        
        if (data.success) {
            if (likeBtn) {
                likeBtn.textContent = data.es_favorito ? '❤️' : '🤍';
                likeBtn.classList.toggle('liked', data.es_favorito);
            }
            showToast(data.message);
        } else {
            showToast(data.message || 'Error', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showToast('Error al procesar', 'error');
    }
}

// ==================== EVENTOS ====================
function inicializarEventosReproductor() {
    const mainPlayBtn = document.getElementById('gPlayPauseBtn');
    if (mainPlayBtn) {
        mainPlayBtn.addEventListener('click', togglePlay);
    }
    
    const prevBtn = document.getElementById('gPrevBtn');
    if (prevBtn) {
        prevBtn.addEventListener('click', anteriorCancion);
    }
    
    const nextBtn = document.getElementById('gNextBtn');
    if (nextBtn) {
        nextBtn.addEventListener('click', siguienteCancion);
    }
    
    const shuffleBtn = document.getElementById('gShuffleBtn');
    if (shuffleBtn) {
        shuffleBtn.addEventListener('click', toggleShuffle);
    }
    
    const repeatBtn = document.getElementById('gRepeatBtn');
    if (repeatBtn) {
        repeatBtn.addEventListener('click', toggleRepeat);
    }
    
    const likeBtn = document.getElementById('gPlayerLikeBtn');
    if (likeBtn) {
        likeBtn.addEventListener('click', toggleFavorito);
    }
    
    const progressBar = document.getElementById('gProgressBar');
    if (progressBar && audioPlayer) {
        progressBar.addEventListener('click', function(e) {
            if (!audioPlayer.duration) return;
            const rect = this.getBoundingClientRect();
            const percent = (e.clientX - rect.left) / rect.width;
            audioPlayer.currentTime = percent * audioPlayer.duration;
        });
    }
    
    const volumeBar = document.getElementById('gVolumeBar');
    if (volumeBar && audioPlayer) {
        volumeBar.addEventListener('click', function(e) {
            const rect = this.getBoundingClientRect();
            const percent = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
            audioPlayer.volume = percent;
            actualizarVolumenUI(percent);
            guardarEstadoReproductor();
        });
    }
    
    const volumeBtn = document.getElementById('gVolumeBtn');
    let previousVolume = 0.7;
    if (volumeBtn && audioPlayer) {
        volumeBtn.addEventListener('click', function() {
            if (audioPlayer.volume > 0) {
                previousVolume = audioPlayer.volume;
                audioPlayer.volume = 0;
            } else {
                audioPlayer.volume = previousVolume;
            }
            actualizarVolumenUI(audioPlayer.volume);
            guardarEstadoReproductor();
        });
    }
    
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
        
        audioPlayer.addEventListener('error', function(e) {
            console.error('Error de audio:', e);
            showToast('Error al reproducir', 'error');
        });
        
        // Actualizar estado de reproducción
        audioPlayer.addEventListener('play', function() {
            isPlaying = true;
            actualizarBotonPlay();
        });
        
        audioPlayer.addEventListener('pause', function() {
            isPlaying = false;
            actualizarBotonPlay();
        });
    }
    
    // Atajos de teclado
    document.addEventListener('keydown', function(e) {
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
        
        switch(e.code) {
            case 'Space':
                e.preventDefault();
                togglePlay();
                break;
            case 'ArrowRight':
                if (e.ctrlKey || e.metaKey) {
                    e.preventDefault();
                    siguienteCancion();
                } else if (audioPlayer) {
                    audioPlayer.currentTime = Math.min(audioPlayer.duration || 0, audioPlayer.currentTime + 10);
                }
                break;
            case 'ArrowLeft':
                if (e.ctrlKey || e.metaKey) {
                    e.preventDefault();
                    anteriorCancion();
                } else if (audioPlayer) {
                    audioPlayer.currentTime = Math.max(0, audioPlayer.currentTime - 10);
                }
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
                if (audioPlayer) {
                    document.getElementById('gVolumeBtn')?.click();
                }
                break;
            case 'KeyS':
                toggleShuffle();
                break;
            case 'KeyR':
                toggleRepeat();
                break;
        }
    });
}
// ==================== FUNCIONES GLOBALES ====================
window.MuuuPlayer = {
    play: reproducirCancion,
    pause: pausarCancion,
    toggle: togglePlay,
    next: siguienteCancion,
    prev: anteriorCancion,
    setPlaylist: function(playlist) {
        songsList = playlist;
        guardarEstadoReproductor();
    },
    getState: function() {
        return {
            currentSong: songsList.find(s => s.id == currentSongId),
            isPlaying: isPlaying,
            playlist: songsList
        };
    },
    // ⭐ Función para que el SPA actualice la lista de canciones
    actualizarLista: cargarCancionesEnLista,
    marcarActiva: marcarCancionActiva
};

console.log('🎵 MuuuPlayer SPA cargado - Atajos: Espacio=Play/Pause, Flechas=Navegar, M=Mute, S=Shuffle, R=Repeat');