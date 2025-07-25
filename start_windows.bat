@echo off
echo 🚀 Iniciando servidor ASGI para Windows...
echo.

REM Configurar variable de entorno Django
set DJANGO_SETTINGS_MODULE=partygames.settings

REM Activar entorno virtual
call venv\Scripts\activate.bat

REM Ejecutar servidor ASGI
echo 📡 WebSockets habilitados para tiempo real
echo 🌐 Servidor disponible en: http://localhost:8000
echo 🔌 WebSocket disponible en: ws://localhost:8000/ws/
echo.
echo Presiona Ctrl+C para detener el servidor
echo.

python -m daphne partygames.asgi:application

pause 