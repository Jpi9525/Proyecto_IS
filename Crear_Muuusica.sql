CREATE DATABASE BD_Muuusica;
USE BD_Muuusica; 

DELIMITER $$
CREATE PROCEDURE SP_CREA_BD_Muuusica ()
BEGIN

CREATE TABLE Usuario(
	UsuarioID int auto_increment,
    primary key(UsuarioID),
    NombreUsuario varchar(50), 
    ApellidoUsuario varchar(50),
    ContrasenaUsuario varchar(50),
    EmaiUsuario varchar(30),
    Foto_Perfil_URL varchar(100),
    DescripcionUsuario varchar(500),
    CancionPerfilUsuario varchar(100),
    Email_Verificado boolean default false,
    Es_Admin boolean default false
);

CREATE TABLE Genero (
	GeneroID int auto_increment,
    primary key(GeneroID),
    Nombre_Genero varchar(25),
    Imagen_Genero varchar(100)
);  

CREATE TABLE Genero_Usuario (
    GeneroUsuarioID int auto_increment,
    primary key(GeneroUsuarioID),
    R_Usuario int,
    R_Genero int,
    FOREIGN KEY (R_Usuario) REFERENCES Usuario(UsuarioID),
    FOREIGN KEY (R_Genero) REFERENCES Genero(GeneroID),
    UNIQUE KEY unique_usuario_genero (R_Usuario, R_Genero)
);

CREATE TABLE Artista (
	ArtistaID int auto_increment,
    primary key(ArtistaID),
    NombreArtista varchar(30),
    ShipperPhone varchar(15)
);

CREATE TABLE Album (
	AlbumID int auto_increment,
    primary key(AlbumID),
    R_Artista int,
    R_Genero int,
    Titulo_Album varchar(50),
    Portada_Album varchar(500),
	FOREIGN KEY (R_Artista) REFERENCES Artista(ArtistaID),
    FOREIGN KEY (R_Genero) REFERENCES Genero(GeneroID)
);

CREATE TABLE Musica (
	MusicaID int auto_increment,
    primary key(MusicaID),
    R_Artista int, 
    R_Album int,
    Titulo_Cancion varchar(15), 
    Duracion int,
    Ruta_Archivo_M varchar(200),
    Tamano_Archivo_M int,
    Num_Reproducciones int,
    FOREIGN KEY(R_Artista) REFERENCES Artista(ArtistaID),  
    FOREIGN KEY(R_Album) REFERENCES Album(AlbumID)
);

CREATE TABLE Favorito (
	FavoritoID int auto_increment, 
    primary key(FavoritoID),
    R_Usuario int,  
    R_Musica int,  
    Es_Corazon boolean default false,
    FOREIGN KEY(R_Usuario) REFERENCES Usuario(UsuarioID),  
    FOREIGN KEY(R_Musica) REFERENCES Musica(MusicaID)     
);

CREATE TABLE Playlist (
	PlaylistID int auto_increment,
    primary key(PlaylistID),
    R_Usuario int,
    Nombre_Playlist varchar(30),
    Es_Publica boolean default false,
    FOREIGN KEY (R_Usuario) REFERENCES Usuario(UsuarioID)  
);

CREATE TABLE Playlist_Cancion (
	R_Playlist int,
	R_Musica int,
    Orden int,
	PRIMARY KEY (R_Playlist, R_Musica),    
    FOREIGN KEY (R_Playlist) REFERENCES Playlist(PlaylistID),  
    FOREIGN KEY (R_Musica) REFERENCES Musica(MusicaID)
);

CREATE TABLE Resena(
    ResenaID int auto_increment,
    primary key(ResenaID),
	R_Usuario int,
	R_Musica int,
    R_Album int,
    Titulo_Resena varchar(30),
    Contenido_Resena varchar(200),
    Calificacion_Estrellas int check (Calificacion_Estrellas between 1 and 3), 
    FOREIGN KEY (R_Usuario) REFERENCES Usuario(UsuarioID),
    FOREIGN KEY (R_Musica) REFERENCES Musica(MusicaID),
    FOREIGN KEY (R_Album) REFERENCES Album(AlbumID)
);  

CREATE TABLE Reaccion_Resena (
	ReaccionID int auto_increment,
    Primary key(ReaccionID),  
    R_Usuario int,
    R_Resena int,
    Tipo_Reaccion ENUM('like', 'dislike'),  
    FOREIGN KEY (R_Usuario) REFERENCES Usuario(UsuarioID),
    FOREIGN KEY (R_Resena) REFERENCES Resena(ResenaID)
);

CREATE TABLE Calificacion (
	CalificacionID int auto_increment,
    Primary key(CalificacionID),  
    R_Usuario int,
    R_Musica int,
    R_Album int,
    Puntuacion int check(Puntuacion between 1 and 5), 
    FOREIGN KEY (R_Usuario) REFERENCES Usuario(UsuarioID),
    FOREIGN KEY (R_Musica) REFERENCES Musica(MusicaID),
    FOREIGN KEY (R_Album) REFERENCES Album(AlbumID)
); 

CREATE TABLE Descarga (
	DescargaID int auto_increment,
    Primary key(DescargaID), 
    R_Usuario int,
    R_Musica int,
    FOREIGN KEY (R_Usuario) REFERENCES Usuario(UsuarioID),
    FOREIGN KEY (R_Musica) REFERENCES Musica(MusicaID)
);  

CREATE TABLE API_Externa ( 
	APIID int auto_increment,
    primary key(APIID),
	Nombre_API varchar(100),    
	API_Key varchar(500),         
	Endpoint_URL varchar(500),             
	Activa boolean default false
); 

END $$
DELIMITER ;

CALL SP_CREA_BD_Muuusica();