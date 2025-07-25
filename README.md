# JuegosGrupo - Plataforma de Juegos en Tiempo Real

Una plataforma web para jugar juegos de grupo en tiempo real usando Django y WebSockets.

## Características

- **Juego Blanco**: Un juego de palabras y creatividad con roles ocultos
- **Tiempo Real**: Actualizaciones instantáneas usando WebSockets
- **Interfaz Moderna**: Diseño responsive con Bootstrap
- **Sistema de Puntos**: Puntuación automática según el resultado del juego

## Instalación

1. **Clonar el repositorio**:
   ```bash
   git clone <url-del-repositorio>
   cd JuegosGrupo
   ```

2. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configurar la base de datos**:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

4. **Crear un superusuario (opcional)**:
   ```bash
   python manage.py createsuperuser
   ```

5. **Ejecutar el servidor ASGI** (para WebSockets):

   **En Windows:**
   ```cmd
   # Opción 1: Script batch (recomendado)
   start_windows.bat
   
   # Opción 2: Script PowerShell
   .\start_windows.ps1
   
   # Opción 3: Manual
   venv\Scripts\activate
   python -m daphne partygames.asgi:application
   ```

   **En Linux/Mac:**
   ```bash
   python -m daphne partygames.asgi:application
   ```
   
   ⚠️ **Importante**: Para que los WebSockets funcionen, debes usar el servidor ASGI, no el servidor de desarrollo normal de Django.

## Uso

1. Abre tu navegador y ve a `http://localhost:8000`
2. Regístrate o inicia sesión
3. Crea una partida del juego "Blanco" o únete a una existente
4. Comparte el código de la partida con tus amigos
5. ¡Disfruta del juego en tiempo real!

## Tecnologías Utilizadas

- **Backend**: Django 5.2.4
- **WebSockets**: Django Channels 4.0.0
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **Base de Datos**: SQLite (desarrollo)

## Estructura del Proyecto

```
JuegosGrupo/
├── blanco/                 # App del juego Blanco
│   ├── consumers.py       # Lógica de WebSockets
│   ├── routing.py         # Rutas de WebSocket
│   ├── models.py          # Modelos de datos
│   ├── views.py           # Vistas HTTP
│   └── ...
├── static/
│   ├── css/              # Estilos CSS
│   ├── js/               # JavaScript (incluye websocket.js)
│   └── ...
├── templates/            # Plantillas HTML
├── partygames/          # Configuración principal
│   ├── settings.py      # Configuración de Django
│   ├── asgi.py          # Configuración ASGI para WebSockets
│   └── ...
└── requirements.txt     # Dependencias del proyecto
```

## Características de Tiempo Real

El proyecto utiliza Django Channels para proporcionar actualizaciones en tiempo real:

- **Conexión WebSocket**: Los jugadores se conectan automáticamente a la sala de la partida
- **Actualizaciones Instantáneas**: Los cambios se reflejan inmediatamente en todas las pantallas
- **Notificaciones**: Sistema de notificaciones toast para eventos importantes
- **Reconexión Automática**: Si se pierde la conexión, se intenta reconectar automáticamente

## Desarrollo

Para ejecutar en modo desarrollo con WebSockets:

```bash
python -m daphne partygames.asgi:application
```

El servidor ASGI manejará tanto las peticiones HTTP como las conexiones WebSocket en tiempo real.

## Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles. 