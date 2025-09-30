"""
Authentication and rate limiting middleware
"""
import json
import logging
import hashlib
import os
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Header, HTTPException, Request
from fastapi.security import APIKeyHeader

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Try to import GCP, fallback to local mode
try:
    from google.cloud import firestore, secretmanager
    GCP_AVAILABLE = True
except ImportError:
    logger.warning("⚠️ GCP libraries not available, using local mode")
    GCP_AVAILABLE = False

# API Key header scheme
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


class AuthService:
    """Authentication service using Secret Manager"""
    
    def __init__(self):
        self.valid_keys = set()
        self.load_api_keys()
    
    def load_api_keys(self):
        """Load valid API keys from Secret Manager"""
        try:
            client = secretmanager.SecretManagerServiceClient()
            name = f"projects/{settings.project_id}/secrets/{settings.api_keys_secret}/versions/latest"
            
            response = client.access_secret_version(request={"name": name})
            secret_data = response.payload.data.decode("UTF-8")
            
            # Parse JSON with keys
            keys_data = json.loads(secret_data)
            self.valid_keys = set(keys_data.get('keys', {}).values())
            
            logger.info(f"✅ Loaded {len(self.valid_keys)} valid API keys")
            
        except Exception as e:
            logger.error(f"❌ Failed to load API keys: {e}")
            # Fallback: Allow requests in dev mode
            if settings.debug:
                logger.warning("⚠️ Debug mode: allowing all requests")
                self.valid_keys.add("debug-key")
    
    def verify_api_key(self, api_key: str) -> bool:
        """Verify if API key is valid"""
        if not api_key:
            return False
        
        # Hash the key for comparison (keys stored hashed in Secret Manager)
        # For demo, direct comparison
        return api_key in self.valid_keys


class RateLimiter:
    """Rate limiting using Firestore"""
    
    def __init__(self):
        self.db = firestore.Client(project=settings.project_id, database=settings.firestore_database)
    
    def check_rate_limit(self, api_key: str) -> tuple[bool, dict]:
        """
        Check if API key has exceeded rate limit
        
        Returns:
            (allowed, headers) tuple
        """
        try:
            # Create key-based identifier
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()[:16]
            doc_ref = self.db.collection(settings.rate_limit_collection).document(key_hash)
            
            # Get current hour window
            now = datetime.utcnow()
            hour_key = now.strftime("%Y%m%d%H")
            
            # Get document
            doc = doc_ref.get()
            
            if doc.exists:
                data = doc.to_dict()
                current_count = data.get(f'requests_{hour_key}', 0)
            else:
                current_count = 0
            
            # Check limit
            if current_count >= settings.rate_limit_requests:
                # Calculate retry-after
                next_hour = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
                retry_after = int((next_hour - now).total_seconds())
                
                headers = {
                    "X-RateLimit-Limit": str(settings.rate_limit_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(next_hour.timestamp())),
                    "Retry-After": str(retry_after)
                }
                
                return False, headers
            
            # Increment counter
            doc_ref.set({
                f'requests_{hour_key}': firestore.Increment(1),
                'last_request': now
            }, merge=True)
            
            # Calculate remaining
            remaining = settings.rate_limit_requests - (current_count + 1)
            
            headers = {
                "X-RateLimit-Limit": str(settings.rate_limit_requests),
                "X-RateLimit-Remaining": str(remaining),
                "X-RateLimit-Reset": str(int((now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0).timestamp()))
            }
            
            return True, headers
            
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            # On error, allow request (fail open)
            return True, {}


# Global instances
_auth_service = None
_rate_limiter = None


def get_auth_service():
    """Get or create auth service singleton"""
    global _auth_service
    if _auth_service is None:
        # Only use local mode if explicitly set
        local_mode = os.getenv('LOCAL_MODE', 'false').lower() == 'true'
        
        if local_mode:
            logger.info("🔧 Using local mode auth (LOCAL_MODE=true)")
            from app.services.local_mode import LocalAuthService
            _auth_service = LocalAuthService()
        else:
            logger.info("🚀 Using production auth with GCP Secret Manager")
            _auth_service = AuthService()
    return _auth_service


def get_rate_limiter():
    """Get or create rate limiter singleton"""
    global _rate_limiter
    if _rate_limiter is None:
        # Only use local mode if explicitly set
        local_mode = os.getenv('LOCAL_MODE', 'false').lower() == 'true'
        
        if local_mode:
            logger.info("🔧 Using local mode rate limiter (in-memory)")
            from app.services.local_mode import LocalRateLimiter
            _rate_limiter = LocalRateLimiter()
        else:
            logger.info("🚀 Using production rate limiter with Firestore")
            _rate_limiter = RateLimiter()
    return _rate_limiter


async def verify_api_key(x_api_key: Optional[str] = Header(None)) -> str:
    """
    FastAPI dependency for API key verification
    """
    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing X-API-Key header",
            headers={"WWW-Authenticate": "ApiKey"}
        )
    
    auth = get_auth_service()
    if not auth.verify_api_key(x_api_key):
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"}
        )
    
    return x_api_key


async def check_rate_limit(request: Request, api_key: str) -> dict:
    """
    FastAPI dependency for rate limiting
    Returns rate limit headers
    """
    limiter = get_rate_limiter()
    allowed, headers = limiter.check_rate_limit(api_key)
    
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Limit: {settings.rate_limit_requests} requests per hour",
            headers=headers
        )
    
    # Add headers to response (will be added by middleware)
    request.state.rate_limit_headers = headers
    return headers
