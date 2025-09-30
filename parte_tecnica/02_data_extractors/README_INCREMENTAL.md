# Guía de Carga Incremental - Banxico SIE

## 📋 Descripción

El script `banxico_incremental_loader.py` permite actualizar los datos del SIE de Banxico de forma incremental, descargando solo los registros nuevos desde la última carga.

## ✅ Características

### Carga Incremental
- Detecta automáticamente la última fecha cargada para cada serie
- Descarga solo los datos nuevos desde esa fecha
- Evita duplicados y mantiene el historial completo
- Añade timestamp de descarga a todos los registros

### Gestión de Estado
- Mantiene un log de todas las cargas en `incremental_load_log.json`
- Genera reportes detallados de cada ejecución
- Permite consultar el historial de cargas

### Datos con Timestamp
Todos los registros incluyen la columna `fecha_descarga` con el momento exacto de la descarga, facilitando:
- Auditoría de datos
- Reproducibilidad
- Control de versiones de datos
- Debugging de problemas

## 🚀 Uso

### Instalación de Dependencias
```bash
# Si aún no has instalado las dependencias
./install_dependencies.sh
```

### Ejecución

#### Carga Incremental (Recomendado)
```bash
python banxico_incremental_loader.py
# Seleccionar opción 1
```
Solo descarga datos nuevos desde la última carga.

#### Recarga Completa
```bash
python banxico_incremental_loader.py
# Seleccionar opción 2
```
Descarga todos los datos desde 2015 (sobrescribe existentes).

#### Ver Historial
```bash
python banxico_incremental_loader.py
# Seleccionar opción 3
```
Muestra las últimas 10 cargas realizadas.

### Automatización con Cron
Para actualización diaria automática:
```bash
# Editar crontab
crontab -e

# Añadir línea para ejecutar a las 6 AM cada día
0 6 * * * cd /ruta/al/proyecto && /usr/bin/python3 parte_tecnica/02_data_extractors/banxico_incremental_loader.py < echo "1"
```

## 📊 Estructura de Datos

### Archivos Individuales
```
outputs/
├── SF43718_data.csv    # Tipo de cambio USD/MXN
├── SP1_data.csv        # INPC General
├── SF43783_data.csv    # TIIE 28 días
├── SR16734_data.csv    # IGAE
└── SP74665_data.csv    # Inflación no subyacente
```

### Formato de Datos
```csv
serie_id,fecha,valor,fecha_descarga
SF43718,2025-09-26,18.3825,2025-09-28 17:48:52.355628
```

### Archivos de Control
```
outputs/
├── incremental_load_log.json     # Historial de cargas
├── incremental_report_*.txt      # Reportes de cada ejecución
└── banxico_consolidated_data.csv # Dataset consolidado
```

## 📈 Datos Disponibles

| Serie | Descripción | Desde | Hasta | Frecuencia |
|-------|-------------|-------|-------|------------|
| SF43718 | Tipo de cambio FIX | 2015-01-02 | Actualidad | Diaria |
| SP1 | INPC General | 2015-01-01 | Mes anterior | Mensual |
| SF43783 | TIIE 28 días | 2015-01-02 | Actualidad | Diaria |
| SR16734 | IGAE | 2015-01-01 | 2023-05-01* | Mensual |
| SP74665 | Inflación no subyacente | 2015-01-01 | Mes anterior | Mensual |

*IGAE tiene retraso significativo en publicación

## 🔄 Flujo de Trabajo Recomendado

### Primera Vez
1. Ejecutar carga completa (opción 2)
2. Verificar integridad de datos
3. Configurar cron para actualizaciones diarias

### Actualizaciones Regulares
1. Carga incremental automática diaria
2. Revisar reportes semanalmente
3. Recarga completa mensual (opcional, para validación)

## ⚠️ Consideraciones Importantes

### Límites de API
- El script respeta los límites de Banxico
- 200 consultas en 5 minutos para datos históricos
- Pausas automáticas entre requests

### Datos Faltantes
- IGAE (SR16734) tiene retraso de publicación significativo
- Datos mensuales se actualizan con retraso de 1-2 meses
- Valores "N/E" se convierten a NULL

### Mantenimiento
- Revisar logs periódicamente
- Limpiar reportes antiguos mensualmente
- Hacer backup antes de recargas completas

## 🐛 Troubleshooting

### Error: "No se pudo cargar el token"
```bash
# Verificar que existe el archivo
cat docs/sources/banxico-sie/sie.txt
```

### Error: "FileNotFoundError"
```bash
# Ejecutar desde la raíz del proyecto
cd /ruta/al/proyecto
python parte_tecnica/02_data_extractors/banxico_incremental_loader.py
```

### Datos no se actualizan
1. Verificar última fecha en archivos CSV
2. Revisar si Banxico ha publicado nuevos datos
3. Consultar logs de error en reportes

## 📝 Ejemplo de Reporte

```
=== REPORTE DE CARGA INCREMENTAL ===
Timestamp: 2025-09-28 18:00:00
Total nuevos registros: 5

Series actualizadas:

SF43718:
  status: updated
  start_date: 2025-09-27
  end_date: 2025-09-28
  new_records: 2
  total_records: 2703

SP1:
  status: up_to_date
  last_date: 2025-08-01
  new_records: 0
```

---

**Última actualización**: 2025-09-28
**Autor**: Sistema CDO DeAcero
