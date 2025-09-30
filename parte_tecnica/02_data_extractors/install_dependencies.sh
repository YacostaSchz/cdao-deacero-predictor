#!/bin/bash
# Script de instalación de dependencias para descarga de datos macro
# CDO DeAcero Project - 2025-09-28

echo "=== Instalación de Dependencias - Macro Data Fetcher ==="
echo ""

# Verificar si estamos en un entorno virtual
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "✅ Entorno virtual detectado: $VIRTUAL_ENV"
else
    echo "⚠️  No se detectó entorno virtual activo"
    echo "   Recomendado: python -m venv venv && source venv/bin/activate"
    echo ""
    read -p "¿Continuar de todos modos? (s/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Ss]$ ]]; then
        exit 1
    fi
fi

echo ""
echo "📦 Instalando paquetes necesarios..."

# Paquetes esenciales que ya deberían estar
pip install --upgrade pip
pip install pandas>=2.0.0
pip install numpy>=1.24.0
pip install requests>=2.31.0
pip install openpyxl>=3.1.0  # Para leer archivos Excel

# Paquete opcional para FRED API
echo ""
echo "📊 Instalando fredapi (opcional pero recomendado)..."
pip install fredapi

# Verificar instalación
echo ""
echo "🔍 Verificando instalación..."
python -c "import pandas; print(f'✅ pandas {pandas.__version__}')"
python -c "import numpy; print(f'✅ numpy {numpy.__version__}')"
python -c "import requests; print(f'✅ requests {requests.__version__}')"
python -c "import openpyxl; print(f'✅ openpyxl {openpyxl.__version__}')"

# Verificar fredapi
if python -c "import fredapi" 2>/dev/null; then
    python -c "import fredapi; print(f'✅ fredapi instalado')"
else
    echo "⚠️  fredapi no se pudo instalar (opcional)"
fi

echo ""
echo "💡 Para usar FRED API necesitas:"
echo "   1. Obtener API key en: https://fred.stlouisfed.org/docs/api/api_key.html"
echo "   2. Configurar: export FRED_API_KEY='tu_key_aqui'"
echo ""
echo "✅ Instalación completada"
