#!/bin/bash

# Script de despliegue para Railway

echo "🚀 Iniciando despliegue en Railway..."

# Verificar que estamos en el directorio correcto
if [ ! -f "manage.py" ]; then
    echo "❌ Error: No se encontró manage.py. Asegúrate de estar en el directorio raíz del proyecto."
    exit 1
fi

# Instalar dependencias
echo "📦 Instalando dependencias..."
pip install -r requirements.txt

# Recolectar archivos estáticos
echo "📁 Recolectando archivos estáticos..."
python manage.py collectstatic --noinput

# Ejecutar migraciones
echo "🗄️ Ejecutando migraciones..."
python manage.py migrate

# Poblar la base de datos con palabras (opcional)
echo "📝 Poblando base de datos con palabras..."
python manage.py populate_words

echo "✅ Despliegue completado!"
echo "🌐 Tu aplicación debería estar disponible en Railway" 