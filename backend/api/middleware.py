"""Security and utility middleware."""

from __future__ import annotations
import re
import uuid
import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from backend.core.logging import get_logger

logger = get_logger(__name__)

def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal and limit length."""
    filename = filename.replace("\\", "/").split("/")[-1]
    filename = re.sub(r'[^a-zA-Z0-9_\-\.]', '', filename)
    return filename[:255]

def validate_upload_size(content_length: int, max_size: int = 100 * 1024 * 1024) -> bool:
    """Validate upload size against maximum allowed size."""
    return content_length <= max_size

def check_path_traversal(path: str) -> bool:
    """Check for path traversal patterns."""
    return ".." not in path

def generate_request_id() -> str:
    """Generate a unique request ID."""
    return str(uuid.uuid4())

class SecurityMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for security checks and request tracking."""
    
    async def dispatch(self, request: Request, call_next) -> Response:
        req_id = generate_request_id()
        request.state.request_id = req_id
        
        if not check_path_traversal(str(request.url)):
            return Response(content="Invalid path", status_code=400)
            
        cl = request.headers.get("content-length")
        if cl and not validate_upload_size(int(cl)):
            return Response(content="Payload too large", status_code=413)

        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        
        response.headers["X-Request-ID"] = req_id
        response.headers["X-Process-Time"] = str(process_time)
        
        return response
