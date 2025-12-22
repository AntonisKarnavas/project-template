import pytest
from fastapi import FastAPI, Request
from starlette.testclient import TestClient
from middlewares.size_limit import RequestSizeLimitMiddleware
from config import settings, SizeLimitRule

# Setup App (Module Scope or Global)
app = FastAPI()
app.add_middleware(RequestSizeLimitMiddleware)

@app.post("/upload")
async def upload_endpoint(request: Request):
    body = await request.body()
    return {"message": "received", "size": len(body)}

@app.post("/upload/heavy")
async def heavy_upload_endpoint(request: Request):
    body = await request.body()
    return {"message": "received heavy", "size": len(body)}

client = TestClient(app)

@pytest.fixture(autouse=True)
def restore_settings():
    original_limit = settings.MAX_UPLOAD_SIZE
    original_rules = settings.SIZE_LIMIT_RULES.copy()
    yield
    settings.MAX_UPLOAD_SIZE = original_limit
    settings.SIZE_LIMIT_RULES = original_rules

def test_default_limit_success():
    # Configure Settings
    settings.MAX_UPLOAD_SIZE = 100
    
    # 50 bytes < 100 bytes
    response = client.post(
        "/upload", content=b"a" * 50, headers={"Content-Length": "50"}
    )
    assert response.status_code == 200

def test_default_limit_failure():
    settings.MAX_UPLOAD_SIZE = 100
    
    # 150 bytes > 100 bytes
    response = client.post(
        "/upload", content=b"a" * 150, headers={"Content-Length": "150"}
    )
    assert response.status_code == 413
    assert response.text == "Request entity too large"
    assert "X-Request-ID" in response.headers
    assert response.headers["X-Max-Content-Length"] == "100"

def test_custom_limit_success():
    # Configure Custom Rule
    settings.MAX_UPLOAD_SIZE = 100
    settings.SIZE_LIMIT_RULES = [
        SizeLimitRule(path_pattern="^/upload/heavy", limit=1000)
    ]
    
    # 500 bytes < 1000 bytes (but > 100 bytes default)
    response = client.post(
        "/upload/heavy", content=b"a" * 500, headers={"Content-Length": "500"}
    )
    assert response.status_code == 200

def test_custom_limit_failure():
    settings.MAX_UPLOAD_SIZE = 100
    settings.SIZE_LIMIT_RULES = [
        SizeLimitRule(path_pattern="^/upload/heavy", limit=1000)
    ]
    
    # 1500 bytes > 1000 bytes
    response = client.post(
        "/upload/heavy", content=b"a" * 1500, headers={"Content-Length": "1500"}
    )
    assert response.status_code == 413
    assert response.headers["X-Max-Content-Length"] == "1000"

def test_invalid_content_length():
    # Should warn log but pass through
    response = client.post(
        "/upload", content=b"a" * 50, headers={"Content-Length": "invalid"}
    )
    assert response.status_code == 200
