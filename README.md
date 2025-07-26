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

## Despliegue en Railway

### Prerrequisitos

1. **Cuenta en Railway**: Regístrate en [railway.app](https://railway.app)
2. **Git**: Asegúrate de que tu código esté en un repositorio Git
3. **Base de datos PostgreSQL**: Railway proporciona PostgreSQL automáticamente
4. **Redis**: Necesario para WebSockets en producción

### Pasos para el Despliegue

1. **Conectar repositorio a Railway**:
   - Ve a [railway.app](https://railway.app)
   - Crea un nuevo proyecto
   - Selecciona "Deploy from GitHub repo"
   - Conecta tu repositorio

2. **Configurar variables de entorno**:
   En Railway, ve a la pestaña "Variables" y configura:
   ```
   SECRET_KEY=tu-clave-secreta-muy-segura
   DEBUG=False
   ALLOWED_HOSTS=tu-app.railway.app
   DATABASE_URL=postgresql://... (Railway lo configura automáticamente)
   REDIS_URL=redis://... (Railway lo configura automáticamente)
   ```

3. **Agregar servicios**:
   - **PostgreSQL**: Railway lo agrega automáticamente
   - **Redis**: Agrega un servicio Redis desde el marketplace

4. **Configurar el comando de inicio**:
   Railway usará automáticamente el `Procfile` que ya tienes configurado.

5. **Desplegar**:
   - Railway detectará automáticamente que es una aplicación Python
   - Ejecutará las migraciones automáticamente
   - Recolectará archivos estáticos
   - Iniciará el servidor ASGI

### Verificar el Despliegue

1. **Migraciones**: Verifica que las migraciones se ejecutaron correctamente
2. **WebSockets**: Prueba que los WebSockets funcionan en producción
3. **Archivos estáticos**: Verifica que CSS/JS se cargan correctamente

### Troubleshooting

- **Error de WebSockets**: Verifica que Redis esté configurado correctamente
- **Error de base de datos**: Verifica las variables de entorno de la base de datos
- **Archivos estáticos no cargan**: Verifica que WhiteNoise esté configurado

### URLs de Producción

- **Aplicación**: `https://tu-app.railway.app`
- **Admin**: `https://tu-app.railway.app/admin`

## Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles. 