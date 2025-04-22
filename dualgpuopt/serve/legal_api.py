"""
FastAPI server for legal LLM model with RAG integration.
"""
from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import logging
import os
import time
from typing import List, Dict, Any, Optional, Generator
import asyncio
import secrets
from functools import lru_cache

# DualGPUOptimizer imports
try:
    from dualgpuopt.engine.pool.core import EnginePool
    from dualgpuopt.rag import retrieve
    HAVE_DUALGPU = True
except ImportError:
    HAVE_DUALGPU = False
    print("Warning: DualGPUOptimizer not found, running with limited functionality")
    EnginePool = None
    retrieve = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
API_KEY = os.getenv('LEGAL_API_KEY', 'dev_key')  # Default for development
MODEL_PATH = os.getenv('LEGAL_MODEL', 'models/qc_legal')
INDEX_PATH = os.getenv('FAISS_INDEX', 'rag/qc.faiss')
ENABLE_RAG = os.getenv('ENABLE_RAG', 'true').lower() in ('true', '1', 't', 'yes')
MAX_TOKENS = int(os.getenv('MAX_TOKENS', '512'))
MAX_CONTEXT_TOKENS = int(os.getenv('MAX_CONTEXT_TOKENS', '2048'))

# Rate limiting settings
RATE_LIMIT = int(os.getenv('RATE_LIMIT', '60'))  # requests per minute
RATE_WINDOW = 60  # seconds
TOKEN_EXPIRY = 86400  # 24 hours in seconds

# In-memory stores for API keys and rate limiting
# In production, consider using Redis or a database
api_tokens = {}  # token -> expiry_timestamp
rate_limits = {}  # token -> [(timestamp, count), ...]

# Models
class ChatRequest(BaseModel):
    """Chat request model."""
    prompt: str = Field(..., description="User prompt for the LLM")
    use_rag: bool = Field(True, description="Whether to use RAG for this request")
    max_tokens: Optional[int] = Field(None, description="Maximum number of tokens to generate")
    temperature: Optional[float] = Field(0.7, description="Temperature for generation")
    model_params: Optional[Dict[str, Any]] = Field(None, description="Additional model parameters")

class TokenRequest(BaseModel):
    """Token request model."""
    admin_key: str = Field(..., description="Admin key for generating tokens")
    expires_in: Optional[int] = Field(TOKEN_EXPIRY, description="Token expiry in seconds")

class TokenResponse(BaseModel):
    """Token response model."""
    token: str = Field(..., description="API token")
    expires_at: int = Field(..., description="Expiry timestamp (Unix time)")

# Create FastAPI app
app = FastAPI(
    title="Legal API",
    description="Legal LLM API with RAG capabilities",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize model engine if DualGPUOptimizer is available
engine = None
if HAVE_DUALGPU:
    try:
        logger.info(f"Initializing model from {MODEL_PATH}")
        engine = EnginePool.get(MODEL_PATH)
        logger.info("Model initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing model: {e}")
        engine = None

# -----------------------------------------------------------------------------
# Authentication and rate limiting
# -----------------------------------------------------------------------------

def verify_token(x_api_key: str = Header(...)) -> str:
    """Verify API token and check expiry."""
    if x_api_key not in api_tokens:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    # Check token expiry
    if api_tokens[x_api_key] < time.time():
        api_tokens.pop(x_api_key, None)  # Remove expired token
        raise HTTPException(status_code=401, detail="Expired API key")
    
    return x_api_key

def check_rate_limit(token: str = Depends(verify_token)) -> str:
    """Check rate limits for the given token."""
    current_time = time.time()
    
    # Initialize rate limit tracking for this token if not exists
    if token not in rate_limits:
        rate_limits[token] = []
    
    # Remove timestamps older than the rate window
    rate_limits[token] = [ts for ts in rate_limits[token] if current_time - ts < RATE_WINDOW]
    
    # Check if rate limit exceeded
    if len(rate_limits[token]) >= RATE_LIMIT:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    # Record this request
    rate_limits[token].append(current_time)
    
    return token

# -----------------------------------------------------------------------------
# Helper functions
# -----------------------------------------------------------------------------

@lru_cache(maxsize=100)
def get_template() -> str:
    """
    Get the prompt template for the legal assistant.
    Cached to avoid file system access on every request.
    """
    try:
        template_path = os.path.join(os.path.dirname(MODEL_PATH), "template.txt")
        if os.path.exists(template_path):
            with open(template_path, 'r', encoding='utf-8') as f:
                return f.read().strip()
        else:
            # Default template if none found
            return """<instructions>
Vous êtes un assistant juridique spécialisé dans le droit québécois. Basez vos réponses sur le contexte fourni.
</instructions>

<context>
{context}
</context>

Question: {prompt}

Réponse:"""
    except Exception as e:
        logger.error(f"Error loading template: {e}")
        # Fallback template
        return """<context>{context}</context>
Question: {prompt}
Réponse:"""

def format_prompt(query: str, context: List[str] = None) -> str:
    """Format the prompt with context for the model."""
    template = get_template()
    
    if context:
        context_text = "\n\n".join(context)
    else:
        context_text = "Aucun contexte juridique spécifique disponible."
    
    return template.format(prompt=query, context=context_text)

async def stream_generator(prompt: str, max_tokens: int) -> Generator[str, None, None]:
    """Generate streaming response tokens."""
    if not engine:
        yield "Erreur: Le modèle n'est pas disponible. Veuillez réessayer plus tard."
        return
    
    try:
        # Stream tokens from the model
        for token in engine.stream(prompt, max_tokens=max_tokens):
            yield token
            # Small delay to avoid overwhelming the client
            await asyncio.sleep(0.01)
    except Exception as e:
        logger.error(f"Error streaming response: {e}")
        yield f"\nErreur pendant la génération: {str(e)}"

# -----------------------------------------------------------------------------
# API Routes
# -----------------------------------------------------------------------------

@app.post("/api/token")
async def create_token(request: TokenRequest) -> TokenResponse:
    """Create a new API token."""
    admin_key = os.getenv('ADMIN_API_KEY')
    
    # Verify admin key
    if not admin_key or request.admin_key != admin_key:
        raise HTTPException(status_code=401, detail="Invalid admin key")
    
    # Generate new token
    token = secrets.token_urlsafe(32)
    expires_at = int(time.time() + request.expires_in)
    
    # Store token with expiry
    api_tokens[token] = expires_at
    
    return TokenResponse(token=token, expires_at=expires_at)

@app.post("/api/chat")
async def chat(
    request: ChatRequest,
    token: str = Depends(check_rate_limit)
) -> StreamingResponse:
    """
    Chat endpoint with RAG support and streaming response.
    
    Args:
        request: Chat request with prompt and parameters
        token: API token (injected by dependency)
        
    Returns:
        Streaming response with generated text
    """
    # Check if model is available
    if not engine:
        raise HTTPException(status_code=503, detail="Model not available")
    
    # Log request
    logger.info(f"Received chat request: {request.prompt[:50]}...")
    
    try:
        # Retrieve relevant documents if RAG is enabled
        context = []
        if request.use_rag and ENABLE_RAG and retrieve:
            logger.info("Using RAG for retrieval")
            
            # Get RAG parameters from request if provided
            k = request.model_params.get("rag_k", 3) if request.model_params else 3
            threshold = request.model_params.get("rag_threshold", 0.6) if request.model_params else 0.6
            
            context = retrieve.top_k(
                request.prompt,
                k=k,
                threshold=threshold,
                index_path=INDEX_PATH
            )
            logger.info(f"Retrieved {len(context)} documents")
        elif request.use_rag and not ENABLE_RAG:
            # Graceful degradation when RAG is requested but disabled
            logger.warning("RAG requested but disabled on server")
            context = ["Note: La recherche contextuelle (RAG) a été demandée mais est désactivée sur le serveur."]
        
        # Format the prompt with context
        formatted_prompt = format_prompt(request.prompt, context)
        
        # Set max tokens
        max_tokens = request.max_tokens or MAX_TOKENS
        
        # Create streaming response
        return StreamingResponse(
            stream_generator(formatted_prompt, max_tokens),
            media_type="text/plain"
        )
        
    except Exception as e:
        logger.error(f"Error processing chat request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint."""
    return {
        "status": "ok" if engine else "unavailable",
        "model": MODEL_PATH,
        "rag_enabled": ENABLE_RAG,
        "timestamp": time.time()
    }

# Development token creation route - remove in production
if os.getenv('ENVIRONMENT', 'development') == 'development':
    @app.get("/dev/token")
    async def dev_token() -> TokenResponse:
        """Create a development token. Only available in development environment."""
        token = "dev_" + secrets.token_urlsafe(16)
        expires_at = int(time.time() + TOKEN_EXPIRY)
        api_tokens[token] = expires_at
        return TokenResponse(token=token, expires_at=expires_at)

# -----------------------------------------------------------------------------
# Startup and shutdown events
# -----------------------------------------------------------------------------

@app.on_event("startup")
async def startup_event():
    """Startup event handler."""
    logger.info("Starting Legal LLM API")
    
    # Add default API key to token store if provided
    if API_KEY != 'dev_key':
        api_tokens[API_KEY] = time.time() + TOKEN_EXPIRY
        logger.info("Added default API key from environment")
    
    # Log configuration
    logger.info(f"Model path: {MODEL_PATH}")
    logger.info(f"RAG enabled: {ENABLE_RAG}")
    logger.info(f"FAISS index: {INDEX_PATH}")
    logger.info(f"Rate limit: {RATE_LIMIT} requests per minute")

@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler."""
    logger.info("Shutting down Legal LLM API")
    # No cleanup needed for engine as it's managed by the EnginePool

# -----------------------------------------------------------------------------
# Main entrypoint
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment or use default
    port = int(os.getenv("PORT", "8080"))
    
    # Run server
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=port,
        log_level="info"
    ) 