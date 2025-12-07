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


-- ============================================
-- PASO 1: INSERTAR GÉNEROS (No tiene dependencias)
-- ============================================
INSERT INTO generos (nombre, imagen_path) VALUES
('Rock', '/static/generos/rock.png'),
('Pop', '/static/generos/pop.png'),
('Jazz', '/static/generos/jazz.png'),
('Hip-hop', '/static/generos/hiphop.png'),
('Electronic', '/static/generos/electronic.png'),
('Classical', '/static/generos/classical.png'),
('Reggae', '/static/generos/reggae.png'),
('Metal', '/static/generos/metal.png'),
('Country', '/static/generos/country.png'),
('R&B', '/static/generos/rb.png');

-- ============================================
-- PASO 2: INSERTAR ÁLBUMES (No tiene dependencias)
-- ============================================
INSERT INTO albumes (titulo, imagen_portada_path, fecha_lanzamiento, permitir_descarga) VALUES
('Abbey Road', '/static/portadas/abbey_road.jpg', '1969-09-26', TRUE),
('Dark Side of the Moon', '/static/portadas/dark_side.jpg', '1973-03-01', TRUE),
('Thriller', '/static/portadas/thriller.jpg', '1982-11-30', TRUE),
('Back in Black', '/static/portadas/back_in_black.jpg', '1980-07-25', TRUE),
('The Wall', '/static/portadas/the_wall.jpg', '1979-11-30', TRUE);

-- ============================================
-- PASO 3: INSERTAR CANCIONES (Depende de álbumes)
-- ============================================
INSERT INTO canciones (album_id, titulo, duracion, ruta_archivo, tamano_archivo, num_reproducciones, permitir_descarga) VALUES
-- Abbey Road
(1, 'Come Together', '00:04:20', '/media/canciones/12 - Away Doom.mp3', 4200000, 0, TRUE),
(1, 'Something', '00:03:03', '/media/canciones/12 - Away Doom.mp3', 3500000, 0, TRUE),
(1, 'Here Comes', '00:03:05', '/media/canciones/12 - Away Doom.mp3', 3600000, 0, TRUE),

-- Dark Side of the Moon
(2, 'Money', '00:06:23', '/media/canciones/12 - Away Doom.mp3', 6800000, 0, TRUE),
(2, 'Time', '00:06:53', '/media/canciones/12 - Away Doom.mp3', 7200000, 0, TRUE),
(2, 'Breathe', '00:02:43', '/media/canciones/12 - Away Doom.mp3', 3200000, 0, TRUE),

-- Thriller
(3, 'Thriller', '00:05:57', '/media/canciones/12 - Away Doom.mp3', 6500000, 0, TRUE),
(3, 'Beat It', '00:04:18', '/media/canciones/12 - Away Doom.mp3', 4800000, 0, TRUE),
(3, 'Billie Jean', '00:04:54', '/media/canciones/12 - Away Doom.mp3', 5200000, 0, TRUE),

-- Back in Black
(4, 'Back in Black', '00:04:15', '/media/canciones/12 - Away Doom.mp3', 4700000, 0, TRUE),
(4, 'You Shook Me', '00:03:30', '/media/canciones/12 - Away Doom.mp3', 4000000, 0, TRUE),

-- The Wall
(5, 'Another Brick', '00:03:59', '/media/canciones/12 - Away Doom.mp3', 4500000, 0, TRUE),
(5, 'Comfortably Nu', '00:06:23', '/media/canciones/12 - Away Doom.mp3', 6800000, 0, TRUE);

-- ============================================
-- PASO 4: INSERTAR USUARIOS (Depende de canciones)
-- ============================================
-- Nota: cancion_id es NULL inicialmente, se actualiza después
INSERT INTO usuarios (nombre, apellido, contrasena, email, foto_perfil_path, descripcion, es_email_verificado, es_admin) VALUES
('Juan', 'Pérez', 'password123', 'juan@example.com', '/static/avatars/default.png', 'Amante de la música rock', TRUE, FALSE);


-- ============================================
-- PASO 5: INSERTAR ARTISTAS (Depende de usuarios - opcional)
-- ============================================
INSERT INTO artistas (nombre, biografia, sitio_web_url, usuario_id) VALUES
('The Beatles', 'Banda británica de rock formada en Liverpool en 1960', 'https://thebeatles.com', NULL),
('Pink Floyd', 'Banda británica de rock progresivo', 'https://pinkfloyd.com', NULL),
('Michael Jackson', 'Rey del Pop', 'https://michaeljackson.com', NULL),
('AC/DC', 'Banda australiana de hard rock', 'https://acdc.com', NULL);

-- ============================================
-- PASO 6: RELACIONAR ÁLBUMES CON ARTISTAS
-- ============================================
INSERT INTO albumes_artistas (rol, album_id, artista_id) VALUES
('Principal', 1, 1),  -- Abbey Road -> The Beatles
('Principal', 2, 2),  -- Dark Side of the Moon -> Pink Floyd
('Principal', 3, 3),  -- Thriller -> Michael Jackson
('Principal', 4, 4),  -- Back in Black -> AC/DC
('Principal', 5, 2);  -- The Wall -> Pink Floyd

-- ============================================
-- PASO 7: RELACIONAR ÁLBUMES CON GÉNEROS
-- ============================================
INSERT INTO albumes_generos (album_id, genero_id) VALUES
(1, 1),  -- Abbey Road -> Rock
(2, 1),  -- Dark Side of the Moon -> Rock
(3, 2),  -- Thriller -> Pop
(4, 1),  -- Back in Black -> Rock
(4, 8),  -- Back in Black -> Metal
(5, 1);  -- The Wall -> Rock

-- ============================================
-- PASO 8: RELACIONAR CANCIONES CON ARTISTAS
-- ============================================
INSERT INTO canciones_artistas (tipo_participacion, cancion_id, artista_id) VALUES
-- Abbey Road
('Principal', 1, 1),
('Principal', 2, 1),
('Principal', 3, 1),

-- Dark Side of the Moon
('Principal', 4, 2),
('Principal', 5, 2),
('Principal', 6, 2),

-- Thriller
('Principal', 7, 3),
('Principal', 8, 3),
('Principal', 9, 3),

-- Back in Black
('Principal', 10, 4),
('Principal', 11, 4),

-- The Wall
('Principal', 12, 2),
('Principal', 13, 2);

-- ============================================
-- PASO 9: RELACIONAR CANCIONES CON GÉNEROS
-- ============================================
INSERT INTO canciones_generos (cancion_id, genero_id) VALUES
-- Abbey Road (Rock)
(1, 1), (2, 1), (3, 1),

-- Dark Side of the Moon (Rock)
(4, 1), (5, 1), (6, 1),

-- Thriller (Pop)
(7, 2), (8, 2), (9, 2),

-- Back in Black (Rock/Metal)
(10, 1), (10, 8),
(11, 1), (11, 8),

-- The Wall (Rock)
(12, 1), (13, 1);

-- ============================================
-- PASO 10: CREAR PLAYLISTS DE EJEMPLO
-- ============================================
INSERT INTO playlists (usuario_id, nombre, fecha_creacion, imagen_portada, es_publica) VALUES
(1, 'Mis Favoritos', '2024-01-01', '/static/playlists/favoritos.jpg', TRUE),
(1, 'Rock Clásico', '2024-01-02', '/static/playlists/rock.jpg', TRUE),
(2, 'Pop Hits', '2024-01-03', '/static/playlists/pop.jpg', FALSE);

-- ============================================
-- PASO 11: AGREGAR CANCIONES A PLAYLISTS
-- ============================================
INSERT INTO playlists_canciones (playlist_id, cancion_id, orden) VALUES
-- Playlist "Mis Favoritos"
(1, 1, 1),
(1, 7, 2),
(1, 10, 3),

-- Playlist "Rock Clásico"
(2, 1, 1),
(2, 4, 2),
(2, 10, 3),
(2, 12, 4),

-- Playlist "Pop Hits"
(3, 7, 1),
(3, 8, 2),
(3, 9, 3);

-- ============================================
-- PASO 12: MARCAR FAVORITOS
-- ============================================
INSERT INTO favoritos_canciones (usuario_id, cancion_id, es_favorito) VALUES
(1, 1, TRUE),
(1, 7, TRUE),
(1, 10, TRUE),
(2, 7, TRUE),
(2, 8, TRUE);

INSERT INTO favoritos_albumes (usuario_id, album_id, es_favorito) VALUES
(1, 1, TRUE),
(1, 4, TRUE),
(2, 3, TRUE);

-- ============================================
-- PASO 13: AGREGAR RESEÑAS
-- ============================================
INSERT INTO resenas_canciones (usuario_id, cancion_id, comentario, fecha_resena, puntuacion_estrellas) VALUES
(1, 1, '¡Increíble canción! Un clásico atemporal', '2024-01-10', 5),
(1, 7, 'El rey del pop en su mejor momento', '2024-01-11', 5),
(2, 7, 'Me encanta esta canción', '2024-01-12', 4);

INSERT INTO resenas_albumes (usuario_id, album_id, comentario, fecha_resena, puntuacion_estrellas) VALUES
(1, 1, 'El mejor álbum de The Beatles', '2024-01-10', 5),
(1, 3, 'Thriller es un álbum legendario', '2024-01-11', 5),
(2, 3, 'Pop perfecto', '2024-01-12', 5);

-- ============================================
-- PASO 14: AGREGAR REACCIONES A RESEÑAS
-- ============================================
INSERT INTO reacciones_resenas_canciones (usuario_id, resena_cancion_id, tipo) VALUES
(2, 1, 'like'),
(1, 3, 'like');

INSERT INTO reacciones_resenas_albumes (usuario_id, resena_album_id, tipo) VALUES
(2, 1, 'like'),
(1, 3, 'like');

-- ============================================
-- PASO 15: REGISTRAR DESCARGAS
-- ============================================
INSERT INTO descargas_canciones (usuario_id, cancion_id) VALUES
(1, 1),
(1, 7),
(2, 7);

INSERT INTO descargas_albumes (usuario_id, album_id) VALUES
(1, 1),
(1, 3);

-- ============================================
-- PASO 16: VINCULAR USUARIOS CON GÉNEROS FAVORITOS
-- ============================================
INSERT INTO usuarios_generos (usuario_id, genero_id) VALUES
(1, 1),  -- Juan -> Rock
(1, 8),  -- Juan -> Metal
(1, 3),  -- Juan -> Jazz
(2, 2),  -- María -> Pop
(2, 5),  -- María -> Electronic
(2, 6);  -- María -> Classical
