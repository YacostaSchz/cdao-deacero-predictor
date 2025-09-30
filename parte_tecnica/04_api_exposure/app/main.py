"""
Steel Rebar Price Predictor API
FastAPI application for CDO DeAcero technical challenge
"""
import logging
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.models import (
    ServiceInfoResponse,
    PredictionResponse,
    ExtendedPredictionResponse,
    HealthResponse,
    ErrorResponse
)
from app.services.predictor import get_predictor
from app.middleware.auth import verify_api_key, check_rate_limit

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle management - load model on startup"""
    logger.info("🚀 Starting Steel Price Predictor API")
    
    # Load model on startup
    predictor = get_predictor()
    logger.info("✅ Model loaded and ready")
    
    yield
    
    logger.info("🛑 Shutting down API")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="API REST para predicción de precios de varilla corrugada",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Middleware to add rate limit headers
@app.middleware("http")
async def add_rate_limit_headers(request: Request, call_next):
    response = await call_next(request)
    
    # Add rate limit headers if available
    if hasattr(request.state, 'rate_limit_headers'):
        for key, value in request.state.rate_limit_headers.items():
            response.headers[key] = value
    
    return response


@app.get("/", response_model=ServiceInfoResponse, tags=["Info"])
async def root():
    """
    Service information endpoint
    Required by reto_tecnico.txt Section 3.3.5
    """
    predictor = get_predictor()
    model_info = predictor.get_model_info()
    
    return ServiceInfoResponse(
        service=settings.app_name,
        version=settings.app_version,
        documentation_url="/docs",
        data_sources=settings.data_sources,
        last_model_update=model_info.get('trained_date', '2025-09-29T17:04:52Z')
    )


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint for monitoring"""
    predictor = get_predictor()
    
    # Check if model is loaded
    model_loaded = predictor.model is not None
    
    # Check cache freshness (simplified)
    cache_fresh = True  # Would check actual cache age
    
    return HealthResponse(
        status="healthy" if model_loaded else "degraded",
        model_loaded=model_loaded,
        cache_fresh=cache_fresh
    )


@app.get(
    "/predict/steel-rebar-price",
    response_model=PredictionResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Invalid or missing API key"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"}
    },
    tags=["Prediction"]
)
async def predict_steel_price(
    request: Request,
    response: Response,
    api_key: str = Depends(verify_api_key)
):
    """
    Main prediction endpoint - Required by reto_tecnico.txt
    
    Returns next-day steel rebar price prediction for Mexico
    
    Required header: X-API-Key
    Rate limit: 100 requests/hour per API key
    """
    # Check rate limit
    await check_rate_limit(request, api_key)
    
    # Get prediction
    predictor = get_predictor()
    prediction = predictor.predict(return_extended=False)
    
    # Log prediction served
    logger.info(f"Prediction served for {prediction['prediction_date']}")
    
    return prediction


@app.get("/predict/steel-rebar-price/extended", response_model=ExtendedPredictionResponse, tags=["Prediction"])
async def predict_steel_price_extended(
    request: Request,
    response: Response,
    api_key: str = Depends(verify_api_key)
):
    """
    Extended prediction endpoint with wholesale/retail breakdown
    
    Includes:
    - Both wholesale and retail prices
    - Premium factors
    - FX rates
    - Model metadata
    """
    await check_rate_limit(request, api_key)
    
    predictor = get_predictor()
    prediction = predictor.predict(return_extended=True)
    
    return prediction


@app.get("/model/info", tags=["Model"])
async def model_info(api_key: str = Depends(verify_api_key)):
    """Get model metadata and performance metrics"""
    predictor = get_predictor()
    return predictor.get_model_info()


# Error handlers
@app.exception_handler(401)
async def unauthorized_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=401,
        content={
            "error": "Unauthorized",
            "detail": str(exc.detail),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    )


@app.exception_handler(429)
async def rate_limit_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=429,
        content={
            "error": "Rate limit exceeded",
            "detail": str(exc.detail),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        },
        headers=exc.headers
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
