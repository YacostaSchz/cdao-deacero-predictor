"""
Local development mode - Mock GCP services for testing
"""
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class LocalPredictor:
    """Local predictor for testing without GCP"""
    
    def __init__(self):
        self.model_metadata = {
            'version': 'v2.0-local',
            'trained_date': '2025-09-29T17:04:52Z',
            'architecture': 'Two-Stage (LME + Premium)',
            'data_quality': 'Validated with holiday imputation',
            'lme_mape_test': 1.55,
            'premium_mape_test': 1.03
        }
        logger.info("🔧 Local mode: Using mock predictor")
    
    def load_model(self) -> bool:
        """Mock model loading"""
        logger.info("✅ Local model loaded (mock)")
        return True
    
    def get_cached_prediction(self) -> Optional[Dict]:
        """
        Mock cached prediction
        Returns prediction for NEXT BUSINESS DAY
        """
        # Hoy es 29-Sep (lunes), siguiente día hábil es 30-Sep (martes)
        # El modelo predice el CIERRE del día siguiente
        today = datetime.utcnow().date()
        
        # Si hoy es viernes, sábado o domingo, siguiente día hábil es lunes
        if today.weekday() == 4:  # Viernes
            tomorrow = today + timedelta(days=3)  # Lunes
        elif today.weekday() == 5:  # Sábado
            tomorrow = today + timedelta(days=2)  # Lunes
        elif today.weekday() == 6:  # Domingo
            tomorrow = today + timedelta(days=1)  # Lunes
        else:  # Lun-Jue
            tomorrow = today + timedelta(days=1)  # Día siguiente
        
        return {
            'prediction_date': tomorrow.isoformat(),
            'predicted_price_usd_per_ton': 941.0,
            'currency': 'USD',
            'unit': 'metric_ton',
            'model_confidence': 0.95,
            'generated_at': datetime.utcnow().isoformat(),
            'predicted_price_mxn_per_ton': 17700.0,
            'fx_rate': 18.8,
            'lme_base_price': 540.5,
            'mexico_premium': 1.705
        }
    
    def predict(self, return_extended: bool = False) -> Dict:
        """Generate mock prediction"""
        cached = self.get_cached_prediction()
        
        response = {
            "prediction_date": cached['prediction_date'],
            "predicted_price_usd_per_ton": cached['predicted_price_usd_per_ton'],
            "currency": "USD",
            "unit": "metric_ton",
            "model_confidence": cached['model_confidence'],
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        if return_extended:
            response.update({
                "price_level": "retail",
                "predicted_price_mxn_per_ton": cached['predicted_price_mxn_per_ton'],
                "fx_rate": cached['fx_rate'],
                "lme_base_price": cached['lme_base_price'],
                "mexico_premium": cached['mexico_premium'],
                "model_version": "v2.0",
                "data_quality_validated": True,
                "wholesale_price_usd": round(cached['predicted_price_usd_per_ton'] * 0.8874, 2)
            })
        
        return response
    
    def get_model_info(self) -> Dict:
        """Get model metadata"""
        return {
            **self.model_metadata,
            "combined_mape": 1.29,
            "mode": "local_development"
        }


class LocalAuthService:
    """Local auth service - accepts any key starting with 'test-'"""
    
    def __init__(self):
        logger.info("🔧 Local mode: Using mock auth")
    
    def load_api_keys(self):
        """Mock - no loading needed"""
        pass
    
    def verify_api_key(self, api_key: str) -> bool:
        """Accept any key starting with 'test-' or 'dev-'"""
        if not api_key:
            return False
        return api_key.startswith(('test-', 'dev-', 'local-'))


class LocalRateLimiter:
    """Local rate limiter - in-memory only"""
    
    def __init__(self):
        self.counters = {}
        logger.info("🔧 Local mode: Using in-memory rate limiter")
    
    def check_rate_limit(self, api_key: str) -> tuple[bool, dict]:
        """Simple in-memory rate limiting"""
        hour_key = datetime.utcnow().strftime("%Y%m%d%H")
        key = f"{api_key}_{hour_key}"
        
        count = self.counters.get(key, 0)
        
        if count >= 100:
            headers = {
                "X-RateLimit-Limit": "100",
                "X-RateLimit-Remaining": "0",
                "Retry-After": "3600"
            }
            return False, headers
        
        self.counters[key] = count + 1
        
        headers = {
            "X-RateLimit-Limit": "100",
            "X-RateLimit-Remaining": str(99 - count)
        }
        
        return True, headers
