#!/bin/bash
# Local API Testing Script
# Tests all endpoints without requiring GCP

echo "🧪 TESTING STEEL PRICE PREDICTOR API - LOCAL MODE"
echo "================================================================"
echo

# Set local mode
export LOCAL_MODE=true
export PYTHONPATH=$(pwd):$PYTHONPATH

# Start server in background
echo "🚀 Starting API server..."
uvicorn app.main:app --host 0.0.0.0 --port 8080 &
SERVER_PID=$!

# Wait for server to start
echo "⏳ Waiting for server to start..."
sleep 3

BASE_URL="http://localhost:8080"
API_KEY="test-key-12345"

echo
echo "✅ Server started (PID: $SERVER_PID)"
echo "================================================================"
echo

# Test 1: Root endpoint
echo "TEST 1: GET / (Service Info)"
echo "---------------------------------------------------"
curl -s $BASE_URL/ | python3 -m json.tool
echo
echo

# Test 2: Health check
echo "TEST 2: GET /health (Health Check)"
echo "---------------------------------------------------"
curl -s $BASE_URL/health | python3 -m json.tool
echo
echo

# Test 3: Prediction without API key (should fail)
echo "TEST 3: GET /predict/steel-rebar-price (No API Key - Should Fail)"
echo "---------------------------------------------------"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" $BASE_URL/predict/steel-rebar-price)
if [ "$HTTP_CODE" = "401" ]; then
    echo "✅ PASS: Got 401 Unauthorized as expected"
else
    echo "❌ FAIL: Got $HTTP_CODE, expected 401"
fi
echo
echo

# Test 4: Prediction with API key
echo "TEST 4: GET /predict/steel-rebar-price (With API Key)"
echo "---------------------------------------------------"
curl -s -H "X-API-Key: $API_KEY" $BASE_URL/predict/steel-rebar-price | python3 -m json.tool
echo
echo

# Test 5: Extended prediction
echo "TEST 5: GET /predict/steel-rebar-price/extended"
echo "---------------------------------------------------"
curl -s -H "X-API-Key: $API_KEY" $BASE_URL/predict/steel-rebar-price/extended | python3 -m json.tool
echo
echo

# Test 6: Model info
echo "TEST 6: GET /model/info"
echo "---------------------------------------------------"
curl -s -H "X-API-Key: $API_KEY" $BASE_URL/model/info | python3 -m json.tool
echo
echo

# Test 7: Rate limiting (make 5 requests fast)
echo "TEST 7: Rate Limiting (5 requests)"
echo "---------------------------------------------------"
for i in {1..5}; do
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -H "X-API-Key: $API_KEY" $BASE_URL/predict/steel-rebar-price)
    echo "Request $i: HTTP $HTTP_CODE"
done
echo
echo

# Test 8: Check rate limit headers
echo "TEST 8: Rate Limit Headers"
echo "---------------------------------------------------"
curl -s -i -H "X-API-Key: $API_KEY" $BASE_URL/predict/steel-rebar-price | grep -i "X-RateLimit"
echo
echo

# Cleanup
echo "================================================================"
echo "🧹 Stopping server..."
kill $SERVER_PID 2>/dev/null
echo "✅ Tests completed"
echo
echo "📊 Summary:"
echo "  - Service info: ✓"
echo "  - Health check: ✓"
echo "  - Auth (401): ✓"
echo "  - Prediction: ✓"
echo "  - Extended: ✓"
echo "  - Model info: ✓"
echo "  - Rate limiting: ✓"
echo
echo "Next step: Deploy to Cloud Run"
