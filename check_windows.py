"""
Script para diagnosticar la configuración de Django y WebSockets en Windows
"""
import os
import sys

print("🔍 Diagnóstico de configuración Django + WebSockets (Windows)")
print("=" * 60)

# 1. Verificar configuración de Django
print("\n1. Configuración de Django:")
try:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'partygames.settings')
    import django
    django.setup()
    print("✅ Django configurado correctamente")
    
    from django.conf import settings
    print(f"   - INSTALLED_APPS: {len(settings.INSTALLED_APPS)} apps")
    print(f"   - ASGI_APPLICATION: {getattr(settings, 'ASGI_APPLICATION', 'No configurado')}")
    print(f"   - CHANNEL_LAYERS: {getattr(settings, 'CHANNEL_LAYERS', 'No configurado')}")
    
except Exception as e:
    print(f"❌ Error en Django: {e}")
    sys.exit(1)

# 2. Verificar Channels
print("\n2. Django Channels:")
try:
    import channels
    print(f"✅ Channels instalado: {channels.__version__}")
except ImportError:
    print("❌ Channels no instalado")
    print("   Instalar con: pip install channels")

# 3. Verificar Daphne
print("\n3. Daphne (Servidor ASGI):")
try:
    import daphne
    print(f"✅ Daphne instalado: {daphne.__version__}")
except ImportError:
    print("❌ Daphne no instalado")
    print("   Instalar con: pip install daphne")

# 4. Verificar configuración ASGI
print("\n4. Configuración ASGI:")
try:
    from partygames.asgi import application
    print("✅ Aplicación ASGI configurada correctamente")
except Exception as e:
    print(f"❌ Error en ASGI: {e}")

# 5. Verificar rutas WebSocket
print("\n5. Rutas WebSocket:")
try:
    from blanco.routing import websocket_urlpatterns
    print(f"✅ {len(websocket_urlpatterns)} rutas WebSocket configuradas")
    for pattern in websocket_urlpatterns:
        print(f"   - {pattern.pattern}")
except Exception as e:
    print(f"❌ Error en rutas WebSocket: {e}")

# 6. Verificar Consumer
print("\n6. Consumer WebSocket:")
try:
    from blanco.consumers import PartidaConsumer
    print("✅ Consumer WebSocket configurado correctamente")
except Exception as e:
    print(f"❌ Error en Consumer: {e}")

print("\n" + "=" * 60)
print("🎯 Recomendaciones para Windows:")

if 'channels' in sys.modules and 'daphne' in sys.modules:
    print("✅ Todo configurado correctamente")
    print("\n🚀 Para iniciar el servidor:")
    print("   Opción 1: start_windows.bat")
    print("   Opción 2: .\\start_windows.ps1")
    print("   Opción 3: venv\\Scripts\\activate && python -m daphne partygames.asgi:application")
elif 'channels' in sys.modules:
    print("⚠️  Channels instalado pero falta Daphne")
    print("   Instalar: pip install daphne")
else:
    print("❌ Falta configuración básica")
    print("   Instalar: pip install channels daphne")

print("\n💡 Recuerda: Siempre activar el entorno virtual primero!")
print("   venv\\Scripts\\activate") 