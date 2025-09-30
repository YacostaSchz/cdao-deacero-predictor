#!/usr/bin/env python3
"""
Stress Test - Steel Price Predictor API
Invoca el servicio agresivamente durante 30 minutos y monitorea estabilidad

Requisitos:
- pip install requests
"""
import requests
import time
import json
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict
import statistics

# Configuración
BASE_URL = "https://steel-predictor-190635835043.us-central1.run.app"
API_KEY = "test-api-key-12345-demo"
DURATION_MINUTES = 30
CONCURRENT_WORKERS = 5  # Requests simultáneos
REQUESTS_PER_MINUTE = 60  # Intensidad

print("🔥 STRESS TEST - Steel Price Predictor API")
print("=" * 80)
print(f"URL: {BASE_URL}")
print(f"Duración: {DURATION_MINUTES} minutos")
print(f"Workers: {CONCURRENT_WORKERS}")
print(f"Requests/minuto: {REQUESTS_PER_MINUTE}")
print(f"Total requests esperados: {DURATION_MINUTES * REQUESTS_PER_MINUTE}")
print("=" * 80)
print()

# Métricas
stats = {
    'total_requests': 0,
    'successful': 0,
    'failed': 0,
    'auth_errors': 0,
    'rate_limit_errors': 0,
    'server_errors': 0,
    'timeouts': 0,
    'response_times': [],
    'status_codes': defaultdict(int),
    'errors': []
}

def make_request(request_id: int) -> dict:
    """Hacer un request al API y registrar métricas"""
    start_time = time.time()
    
    try:
        response = requests.get(
            f"{BASE_URL}/predict/steel-rebar-price",
            headers={"X-API-Key": API_KEY},
            timeout=5
        )
        
        elapsed = time.time() - start_time
        
        return {
            'id': request_id,
            'status_code': response.status_code,
            'response_time': elapsed,
            'success': response.status_code == 200,
            'error': None if response.status_code == 200 else response.text[:100]
        }
        
    except requests.Timeout:
        return {
            'id': request_id,
            'status_code': 0,
            'response_time': 5.0,
            'success': False,
            'error': 'TIMEOUT'
        }
    except Exception as e:
        return {
            'id': request_id,
            'status_code': 0,
            'response_time': time.time() - start_time,
            'success': False,
            'error': str(e)[:100]
        }

def update_stats(result: dict):
    """Actualizar estadísticas"""
    stats['total_requests'] += 1
    
    if result['success']:
        stats['successful'] += 1
    else:
        stats['failed'] += 1
        
        if result['status_code'] == 401:
            stats['auth_errors'] += 1
        elif result['status_code'] == 429:
            stats['rate_limit_errors'] += 1
        elif result['status_code'] >= 500:
            stats['server_errors'] += 1
        elif result['error'] == 'TIMEOUT':
            stats['timeouts'] += 1
        
        if result['error']:
            stats['errors'].append({
                'id': result['id'],
                'error': result['error'],
                'status': result['status_code']
            })
    
    stats['status_codes'][result['status_code']] += 1
    stats['response_times'].append(result['response_time'])

def print_progress():
    """Imprimir progreso actual"""
    if stats['total_requests'] == 0:
        return
    
    success_rate = (stats['successful'] / stats['total_requests']) * 100
    avg_response = statistics.mean(stats['response_times']) if stats['response_times'] else 0
    p95 = statistics.quantiles(stats['response_times'], n=20)[18] if len(stats['response_times']) > 20 else avg_response
    
    print(f"\r📊 Progreso: {stats['total_requests']} requests | "
          f"✅ {stats['successful']} | ❌ {stats['failed']} | "
          f"Success: {success_rate:.1f}% | "
          f"Avg: {avg_response*1000:.0f}ms | "
          f"P95: {p95*1000:.0f}ms", end='', flush=True)

def print_final_report():
    """Imprimir reporte final"""
    print("\n")
    print("=" * 80)
    print("📊 REPORTE FINAL DE STRESS TEST")
    print("=" * 80)
    print()
    
    print(f"⏱️  Duración total: {DURATION_MINUTES} minutos")
    print(f"📤 Total requests: {stats['total_requests']}")
    print()
    
    print("✅ ÉXITO:")
    print(f"   Successful: {stats['successful']} ({stats['successful']/stats['total_requests']*100:.2f}%)")
    print()
    
    print("❌ ERRORES:")
    print(f"   Failed: {stats['failed']} ({stats['failed']/stats['total_requests']*100:.2f}%)")
    print(f"   - Auth errors (401): {stats['auth_errors']}")
    print(f"   - Rate limit (429): {stats['rate_limit_errors']}")
    print(f"   - Server errors (5xx): {stats['server_errors']}")
    print(f"   - Timeouts: {stats['timeouts']}")
    print()
    
    print("⏱️  TIEMPOS DE RESPUESTA:")
    if stats['response_times']:
        avg = statistics.mean(stats['response_times'])
        med = statistics.median(stats['response_times'])
        min_time = min(stats['response_times'])
        max_time = max(stats['response_times'])
        p95 = statistics.quantiles(stats['response_times'], n=20)[18] if len(stats['response_times']) > 20 else avg
        p99 = statistics.quantiles(stats['response_times'], n=100)[98] if len(stats['response_times']) > 100 else avg
        
        print(f"   Promedio: {avg*1000:.0f}ms")
        print(f"   Mediana: {med*1000:.0f}ms")
        print(f"   Min: {min_time*1000:.0f}ms")
        print(f"   Max: {max_time*1000:.0f}ms")
        print(f"   P95: {p95*1000:.0f}ms")
        print(f"   P99: {p99*1000:.0f}ms")
    print()
    
    print("📊 CÓDIGOS DE ESTADO:")
    for code in sorted(stats['status_codes'].keys()):
        count = stats['status_codes'][code]
        pct = (count / stats['total_requests']) * 100
        print(f"   {code}: {count} ({pct:.1f}%)")
    print()
    
    if stats['errors']:
        print("⚠️  PRIMEROS 5 ERRORES:")
        for err in stats['errors'][:5]:
            print(f"   Request {err['id']}: {err['status']} - {err['error']}")
        print()
    
    print("=" * 80)
    print("✅ CONCLUSIÓN:")
    print("=" * 80)
    
    success_rate = (stats['successful'] / stats['total_requests']) * 100
    
    if success_rate >= 99.5:
        print("🟢 EXCELENTE: Success rate >= 99.5%")
        print("   El servicio es altamente estable y production-ready")
    elif success_rate >= 95:
        print("🟡 BUENO: Success rate >= 95%")
        print("   El servicio es estable con errores menores")
    else:
        print("🔴 ATENCIÓN: Success rate < 95%")
        print("   El servicio requiere revisión antes de producción")
    
    print()
    
    if avg*1000 < 200:
        print("🟢 EXCELENTE: P95 < 200ms")
    elif avg*1000 < 500:
        print("🟡 BUENO: P95 < 500ms")
    else:
        print("🔴 ATENCIÓN: P95 > 500ms")
    
    print()

# Ejecutar stress test
print(f"🚀 Iniciando stress test...")
print(f"   Hora inicio: {datetime.now()}")
print()

start_test = time.time()
end_test = start_test + (DURATION_MINUTES * 60)

request_counter = 0

while time.time() < end_test:
    minute_start = time.time()
    
    # Hacer REQUESTS_PER_MINUTE requests en este minuto
    with ThreadPoolExecutor(max_workers=CONCURRENT_WORKERS) as executor:
        futures = []
        
        for i in range(REQUESTS_PER_MINUTE):
            request_counter += 1
            future = executor.submit(make_request, request_counter)
            futures.append(future)
        
        # Recoger resultados
        for future in as_completed(futures):
            result = future.result()
            update_stats(result)
            print_progress()
    
    # Sleep para completar el minuto
    elapsed = time.time() - minute_start
    if elapsed < 60:
        time.sleep(60 - elapsed)

# Reporte final
print()
print()
print_final_report()

# Guardar reporte en JSON
report_file = f"stress_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
with open(report_file, 'w') as f:
    json.dump({
        'test_config': {
            'duration_minutes': DURATION_MINUTES,
            'requests_per_minute': REQUESTS_PER_MINUTE,
            'concurrent_workers': CONCURRENT_WORKERS,
            'total_requests': stats['total_requests']
        },
        'results': {
            'successful': stats['successful'],
            'failed': stats['failed'],
            'success_rate': stats['successful'] / stats['total_requests'] * 100 if stats['total_requests'] > 0 else 0
        },
        'response_times': {
            'average_ms': statistics.mean(stats['response_times']) * 1000 if stats['response_times'] else 0,
            'median_ms': statistics.median(stats['response_times']) * 1000 if stats['response_times'] else 0,
            'p95_ms': statistics.quantiles(stats['response_times'], n=20)[18] * 1000 if len(stats['response_times']) > 20 else 0,
            'p99_ms': statistics.quantiles(stats['response_times'], n=100)[98] * 1000 if len(stats['response_times']) > 100 else 0
        },
        'errors': {
            'auth': stats['auth_errors'],
            'rate_limit': stats['rate_limit_errors'],
            'server': stats['server_errors'],
            'timeout': stats['timeouts']
        },
        'status_codes': dict(stats['status_codes'])
    }, f, indent=2)

print(f"💾 Reporte guardado: {report_file}")
print()
print("✅ Stress test completado")
