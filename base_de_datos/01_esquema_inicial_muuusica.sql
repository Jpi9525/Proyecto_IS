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

-- Crear tabla de reacciones (si no existe)
CREATE TABLE reacciones_canciones (
    reaccion_id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    cancion_id INT NOT NULL,
    tipo ENUM('like', 'dislike') NOT NULL,
    fecha_reaccion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_usuario_cancion (usuario_id, cancion_id),
    FOREIGN KEY (usuario_id) REFERENCES usuarios(usuario_id) ON DELETE CASCADE,
    FOREIGN KEY (cancion_id) REFERENCES canciones(cancion_id) ON DELETE CASCADE
);

-- Verificar
SELECT * FROM reacciones_canciones;

-- Crear tabla ratings_canciones
CREATE TABLE ratings_canciones (
    rating_id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    cancion_id INT NOT NULL,
    valor TINYINT NOT NULL CHECK (valor BETWEEN 1 AND 5),
    fecha_rating TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_usuario_cancion (usuario_id, cancion_id),
    FOREIGN KEY (usuario_id) REFERENCES usuarios(usuario_id) ON DELETE CASCADE,
    FOREIGN KEY (cancion_id) REFERENCES canciones(cancion_id) ON DELETE CASCADE,
    INDEX idx_cancion_id (cancion_id),
    INDEX idx_usuario_id (usuario_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Trigger para validar el valor del rating
DELIMITER //
CREATE TRIGGER check_rating_value BEFORE INSERT ON ratings_canciones
FOR EACH ROW
BEGIN
    IF NEW.valor < 1 OR NEW.valor > 5 THEN
        SIGNAL SQLSTATE '45000' 
        SET MESSAGE_TEXT = 'El rating debe estar entre 1 y 5';
    END IF;
END//
DELIMITER ;

-- Trigger para actualizar también en UPDATE
DELIMITER //
CREATE TRIGGER check_rating_value_update BEFORE UPDATE ON ratings_canciones
FOR EACH ROW
BEGIN
    IF NEW.valor < 1 OR NEW.valor > 5 THEN
        SIGNAL SQLSTATE '45000' 
        SET MESSAGE_TEXT = 'El rating debe estar entre 1 y 5';
    END IF;
END//
DELIMITER ;

-- Vista para obtener el promedio de ratings por canción
CREATE VIEW vista_ratings_canciones AS
SELECT 
    c.cancion_id,
    c.titulo,
    COUNT(r.rating_id) AS total_ratings,
    IFNULL(AVG(r.valor), 0) AS promedio_rating,
    COUNT(CASE WHEN r.valor = 5 THEN 1 END) AS rating_5,
    COUNT(CASE WHEN r.valor = 4 THEN 1 END) AS rating_4,
    COUNT(CASE WHEN r.valor = 3 THEN 1 END) AS rating_3,
    COUNT(CASE WHEN r.valor = 2 THEN 1 END) AS rating_2,
    COUNT(CASE WHEN r.valor = 1 THEN 1 END) AS rating_1
FROM canciones c
LEFT JOIN ratings_canciones r ON c.cancion_id = r.cancion_id
GROUP BY c.cancion_id, c.titulo;

-- Procedimiento para calificar una canción
DELIMITER //
CREATE PROCEDURE sp_calificar_cancion(
    IN p_usuario_id INT,
    IN p_cancion_id INT,
    IN p_valor TINYINT
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SELECT 'Error al calificar la canción' AS mensaje;
    END;
    
    START TRANSACTION;
    
    -- Eliminar rating anterior si existe
    DELETE FROM ratings_canciones 
    WHERE usuario_id = p_usuario_id 
    AND cancion_id = p_cancion_id;
    
    -- Insertar nuevo rating
    INSERT INTO ratings_canciones (usuario_id, cancion_id, valor)
    VALUES (p_usuario_id, p_cancion_id, p_valor);
    
    COMMIT;
    
    SELECT 'Rating guardado exitosamente' AS mensaje;
END//
DELIMITER ;

-- Procedimiento para obtener rating de usuario específico
DELIMITER //
CREATE PROCEDURE sp_obtener_rating_usuario(
    IN p_usuario_id INT,
    IN p_cancion_id INT
)
BEGIN
    SELECT valor 
    FROM ratings_canciones 
    WHERE usuario_id = p_usuario_id 
    AND cancion_id = p_cancion_id;
END//
DELIMITER ;

-- Procedimiento para obtener estadísticas de rating
DELIMITER //
CREATE PROCEDURE sp_obtener_estadisticas_rating(IN p_cancion_id INT)
BEGIN
    SELECT 
        COUNT(*) AS total_ratings,
        IFNULL(AVG(valor), 0) AS promedio,
        IFNULL(STDDEV(valor), 0) AS desviacion_estandar,
        MIN(valor) AS min_rating,
        MAX(valor) AS max_rating
    FROM ratings_canciones 
    WHERE cancion_id = p_cancion_id;
END//
DELIMITER ;
