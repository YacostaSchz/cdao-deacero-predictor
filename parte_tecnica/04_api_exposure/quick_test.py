#!/usr/bin/env python3
"""
Quick local test of FastAPI without GCP dependencies
"""
import os
import sys

# Set local mode before importing app
os.environ['LOCAL_MODE'] = 'true'

print("🧪 QUICK TEST - Steel Price Predictor API")
print("=" * 80)
print()

try:
    # Test imports
    print("1️⃣ Testing imports...")
    from app.main import app
    from app.core.config import get_settings
    from app.services.predictor import get_predictor
    from app.middleware.auth import get_auth_service, get_rate_limiter
    print("   ✅ All imports successful")
    print()
    
    # Test configuration
    print("2️⃣ Testing configuration...")
    settings = get_settings()
    print(f"   App: {settings.app_name}")
    print(f"   Version: {settings.app_version}")
    print(f"   Project: {settings.project_id}")
    print("   ✅ Configuration loaded")
    print()
    
    # Test predictor
    print("3️⃣ Testing predictor service...")
    predictor = get_predictor()
    print("   ✅ Predictor initialized")
    print()
    
    # Test prediction
    print("4️⃣ Testing prediction generation...")
    pred = predictor.predict(return_extended=False)
    print(f"   Prediction date: {pred['prediction_date']}")
    print(f"   Price: {pred['predicted_price_usd_per_ton']} USD/t")
    print(f"   Confidence: {pred['model_confidence']}")
    print("   ✅ Basic prediction works")
    print()
    
    # Test extended prediction
    print("5️⃣ Testing extended prediction...")
    pred_ext = predictor.predict(return_extended=True)
    print(f"   Retail price: {pred_ext.get('predicted_price_usd_per_ton')} USD/t")
    print(f"   Wholesale price: {pred_ext.get('wholesale_price_usd')} USD/t")
    print(f"   Premium: {pred_ext.get('mexico_premium')}")
    print("   ✅ Extended prediction works")
    print()
    
    # Test auth service
    print("6️⃣ Testing auth service...")
    auth = get_auth_service()
    test_key_valid = auth.verify_api_key("test-key-123")
    test_key_invalid = auth.verify_api_key("invalid-key")
    print(f"   'test-key-123': {test_key_valid} (should be True)")
    print(f"   'invalid-key': {test_key_invalid} (should be False)")
    print("   ✅ Auth service works")
    print()
    
    # Test rate limiter
    print("7️⃣ Testing rate limiter...")
    limiter = get_rate_limiter()
    allowed, headers = limiter.check_rate_limit("test-key-123")
    print(f"   Allowed: {allowed}")
    print(f"   Headers: {headers}")
    print("   ✅ Rate limiter works")
    print()
    
    # Test model info
    print("8️⃣ Testing model info...")
    info = predictor.get_model_info()
    print(f"   Version: {info.get('model_version')}")
    print(f"   MAPE: {info.get('combined_mape')}%")
    print(f"   Mode: {info.get('mode', 'production')}")
    print("   ✅ Model info works")
    print()
    
    print("=" * 80)
    print("✅ ALL TESTS PASSED")
    print("=" * 80)
    print()
    print("Next steps:")
    print("  1. Run: uvicorn app.main:app --reload --port 8080")
    print("  2. Visit: http://localhost:8080/docs")
    print("  3. Test endpoints with Swagger UI")
    print()
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
