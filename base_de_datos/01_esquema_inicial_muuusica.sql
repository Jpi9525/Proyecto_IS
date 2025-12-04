CREATE DATABASE muuusica;
USE muuusica;

CREATE TABLE albumes (
	album_id INT AUTO_INCREMENT,
    PRIMARY KEY(album_id),
    titulo VARCHAR(50),
	imagen_portada_path VARCHAR(500),
    fecha_lanzamiento DATE,
    permitir_descarga BOOLEAN
);

CREATE TABLE canciones (
	cancion_id INT AUTO_INCREMENT,
    PRIMARY KEY(cancion_id),
    album_id INT,
    titulo VARCHAR(15), 
    duracion TIME,
    ruta_archivo VARCHAR(200),
    tamano_archivo BIGINT,
    num_reproducciones INT,
    permitir_descarga BOOLEAN,
    FOREIGN KEY(album_id) REFERENCES albumes(album_id)
);

CREATE TABLE usuarios (
	usuario_id INT AUTO_INCREMENT,
    PRIMARY KEY(usuario_id),
    cancion_id INT, -- Canción de perfil
    nombre VARCHAR(50), 
    apellido VARCHAR(50),
    contrasena VARCHAR(255), #CAMBIAR EL TAMAÑO A 255
	username VARCHAR(50),
    email VARCHAR(30),
    foto_perfil_path VARCHAR(100),
    descripcion VARCHAR(500),
	es_email_verificado BOOLEAN DEFAULT FALSE,
    es_admin BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (cancion_id) REFERENCES canciones(cancion_id)
);

CREATE TABLE generos (
	genero_id INT AUTO_INCREMENT,
    PRIMARY KEY(genero_id),
    nombre VARCHAR(25),
    imagen_path VARCHAR(100)
);  

CREATE TABLE usuarios_generos (
    usuario_genero_id INT AUTO_INCREMENT,
    PRIMARY KEY(usuario_genero_id),
    usuario_id INT,
    genero_id INT,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(usuario_id),
    FOREIGN KEY (genero_id) REFERENCES generos(genero_id),
    UNIQUE KEY unique_usuario_genero (usuario_id, genero_id)
);

CREATE TABLE artistas (
	artista_id INT AUTO_INCREMENT,
    PRIMARY KEY(artista_id),
    nombre VARCHAR(30),
    biografia VARCHAR(500),
    sitio_web_url VARCHAR(100),
    usuario_id INT,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(usuario_id)
);

CREATE TABLE albumes_artistas (
	rol ENUM('Principal', 'Productor'),
    album_id INT,
    artista_id INT,
    FOREIGN KEY (album_id) REFERENCES albumes(album_id),
    FOREIGN KEY (artista_id) REFERENCES artistas(artista_id)
);

CREATE TABLE albumes_generos (
	album_id INT,
    genero_id INT,
    FOREIGN KEY (album_id) REFERENCES albumes(album_id),
    FOREIGN KEY (genero_id) REFERENCES generos(genero_id)
);

CREATE TABLE canciones_artistas (
	tipo_participacion ENUM('Principal', 'Featuring'),
    cancion_id INT,
    artista_id INT,
    FOREIGN KEY (cancion_id) REFERENCES canciones(cancion_id),
    FOREIGN KEY (artista_id) REFERENCES artistas(artista_id)
);

CREATE TABLE canciones_generos (
	cancion_id INT,
    genero_id INT,
    FOREIGN KEY (cancion_id) REFERENCES canciones(cancion_id),
    FOREIGN KEY (genero_id) REFERENCES generos(genero_id)
);

CREATE TABLE favoritos_albumes (
    usuario_id INT,  
    album_id INT,  
    es_favorito BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(usuario_id),  
    FOREIGN KEY (album_id) REFERENCES albumes(album_id)     
);

CREATE TABLE favoritos_canciones (
    usuario_id INT,  
    cancion_id INT,  
    es_favorito BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(usuario_id),  
    FOREIGN KEY (cancion_id) REFERENCES canciones(cancion_id)     
);

CREATE TABLE playlists (
	playlist_id INT AUTO_INCREMENT,
    PRIMARY KEY (playlist_id),
    usuario_id INT,
    nombre VARCHAR(30),
    fecha_creacion DATE,
    imagen_portada VARCHAR(500),
    es_publica BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(usuario_id)  
);

CREATE TABLE playlists_canciones (
	playlist_id INT,
	cancion_id INT,
    orden INT,   
    FOREIGN KEY (playlist_id) REFERENCES playlists(playlist_id),  
    FOREIGN KEY (cancion_id) REFERENCES canciones(cancion_id)
);

CREATE TABLE resenas_albumes (
	resena_album_id INT AUTO_INCREMENT,
    PRIMARY KEY (resena_album_id),
	usuario_id INT,
    album_id INT,
    comentario VARCHAR(200),
    fecha_resena DATE,
    puntuacion_estrellas INT CHECK (puntuacion_estrellas BETWEEN 1 AND 5), 
    FOREIGN KEY (usuario_id) REFERENCES usuarios(usuario_id),
    FOREIGN KEY (album_id) REFERENCES albumes(album_id)
);

CREATE TABLE resenas_canciones (
	resena_cancion_id INT AUTO_INCREMENT,
    PRIMARY KEY (resena_cancion_id),
	usuario_id INT,
    cancion_id INT,
    comentario VARCHAR(200),
    fecha_resena DATE,
    puntuacion_estrellas INT CHECK (puntuacion_estrellas BETWEEN 1 AND 5), 
    FOREIGN KEY (usuario_id) REFERENCES usuarios(usuario_id),
    FOREIGN KEY (cancion_id) REFERENCES canciones(cancion_id)
);

CREATE TABLE reacciones_resenas_canciones (
    usuario_id INT,
    resena_cancion_id INT,
    tipo ENUM('like', 'dislike'),  
    FOREIGN KEY (usuario_id) REFERENCES usuarios(usuario_id),
    FOREIGN KEY (resena_cancion_id) REFERENCES resenas_canciones(resena_cancion_id)
);

CREATE TABLE reacciones_resenas_albumes (
    usuario_id INT,
    resena_album_id INT,
    tipo ENUM('like', 'dislike'),  
    FOREIGN KEY (usuario_id) REFERENCES usuarios(usuario_id),
    FOREIGN KEY (resena_album_id) REFERENCES resenas_albumes(resena_album_id)
);

CREATE TABLE descargas_canciones (
	-- descarga_cancion_id INT AUTO_INCREMENT,
    -- PRIMARY KEY (descarga_cancion_id), 
    usuario_id INT,
    cancion_id INT,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(usuario_id),
    FOREIGN KEY (cancion_id) REFERENCES canciones(cancion_id)
);

CREATE TABLE descargas_albumes (
	-- descarga_album_id INT AUTO_INCREMENT,
    -- PRIMARY KEY (descarga_album_id), 
    usuario_id INT,
    album_id INT,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(usuario_id),
    FOREIGN KEY (album_id) REFERENCES albumes(album_id)
);

CREATE TABLE descargas_playlists (
	-- descarga_playlist_id INT AUTO_INCREMENT,
    -- PRIMARY KEY (descarga_playlist_id), 
    usuario_id INT,
    playlist_id INT,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(usuario_id),
    FOREIGN KEY (playlist_id) REFERENCES playlists(playlist_id)
); 

CREATE TABLE redes_sociales (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    nombre_red VARCHAR(50),
    url VARCHAR(200)
);

CREATE TABLE api_externa ( 
	api_id INT AUTO_INCREMENT,
    PRIMARY KEY (api_id),
	nombre VARCHAR(100),    
	api_key VARCHAR(500),         
	endpoint_url VARCHAR(500),             
	activa BOOLEAN DEFAULT FALSE
);