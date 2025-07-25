# Script PowerShell para iniciar el servidor ASGI en Windows
Write-Host "🚀 Iniciando servidor ASGI para Windows..." -ForegroundColor Green
Write-Host ""

# Activar entorno virtual
& ".\venv\Scripts\Activate.ps1"

# Ejecutar servidor ASGI
Write-Host "📡 WebSockets habilitados para tiempo real" -ForegroundColor Cyan
Write-Host "🌐 Servidor disponible en: http://localhost:8000" -ForegroundColor Yellow
Write-Host "🔌 WebSocket disponible en: ws://localhost:8000/ws/" -ForegroundColor Yellow
Write-Host ""
Write-Host "Presiona Ctrl+C para detener el servidor" -ForegroundColor Red
Write-Host ""

python -m daphne partygames.asgi:application 