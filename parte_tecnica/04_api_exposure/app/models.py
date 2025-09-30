"""
Pydantic models for API request/response schemas
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., example="healthy")
    model_loaded: bool = Field(..., example=True)
    cache_fresh: bool = Field(..., example=True)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ServiceInfoResponse(BaseModel):
    """Root endpoint service information"""
    service: str = Field(..., example="Steel Rebar Price Predictor")
    version: str = Field(..., example="v2.0")
    documentation_url: str = Field(..., example="https://steel-predictor-xxx.run.app/docs")
    data_sources: List[str] = Field(..., example=["LME", "Banxico", "EPU", "Trade Events"])
    last_model_update: str = Field(..., example="2025-09-29T17:04:52Z")


class PredictionResponse(BaseModel):
    """Main prediction response - Required format from reto_tecnico.txt"""
    prediction_date: str = Field(..., example="2025-09-30", description="Date of the prediction")
    predicted_price_usd_per_ton: float = Field(..., example=941.0, description="Predicted price in USD per metric ton")
    currency: str = Field(default="USD", example="USD")
    unit: str = Field(default="metric_ton", example="metric_ton")
    model_confidence: float = Field(..., ge=0.0, le=1.0, example=0.95)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "prediction_date": "2025-09-30",
                "predicted_price_usd_per_ton": 941.0,
                "currency": "USD",
                "unit": "metric_ton",
                "model_confidence": 0.95,
                "timestamp": "2025-09-29T17:30:00Z"
            }
        }


class ExtendedPredictionResponse(PredictionResponse):
    """Extended prediction with additional metadata"""
    price_level: str = Field(default="retail", example="retail", description="wholesale or retail")
    predicted_price_mxn_per_ton: Optional[float] = Field(None, example=17700.0)
    fx_rate: Optional[float] = Field(None, example=18.8)
    lme_base_price: Optional[float] = Field(None, example=540.5)
    mexico_premium: Optional[float] = Field(None, example=1.705)
    model_version: str = Field(default="v2.0", example="v2.0")
    data_quality_validated: bool = Field(default=True, example=True)
    
    # Alternative pricing levels
    wholesale_price_usd: Optional[float] = Field(None, example=835.0, description="Wholesale price if retail is primary")
    retail_price_usd: Optional[float] = Field(None, example=941.0, description="Retail price if wholesale is primary")


class ExplainabilityResponse(BaseModel):
    """Model explainability response"""
    prediction_date: str
    predicted_price_usd_per_ton: float
    
    feature_importance: dict = Field(..., example={
        "lme_steel_rebar_m01": 0.496,
        "usd_mxn_exchange_rate": 0.061,
        "premium_factor": 0.053,
        "real_interest_rate": 0.009
    })
    
    price_drivers: dict = Field(..., example={
        "base_lme_price": 540.50,
        "mexico_premium": 1.705,
        "fx_adjustment": 0.98,
        "tariff_impact": 0.053
    })
    
    confidence_factors: dict = Field(..., example={
        "model_confidence": 0.95,
        "data_freshness": "current",
        "volatility_level": "low"
    })


class ErrorResponse(BaseModel):
    """Error response schema"""
    error: str = Field(..., example="Invalid API key")
    detail: Optional[str] = Field(None, example="The provided X-API-Key is not valid")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class RateLimitResponse(BaseModel):
    """Rate limit exceeded response"""
    error: str = Field(default="Rate limit exceeded")
    limit: int = Field(..., example=100)
    window: str = Field(..., example="1 hour")
    retry_after: int = Field(..., example=3600, description="Seconds until reset")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
