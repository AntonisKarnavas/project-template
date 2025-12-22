import pytest
import asyncio
import time
from fastapi import FastAPI
from starlette.testclient import TestClient
from middlewares.timeout import TimeoutMiddleware
from config import settings, TimeoutRule

# Setup App
app = FastAPI()
app.add_middleware(TimeoutMiddleware)

@app.get("/fast")
async def fast_endpoint():
    return {"message": "fast"}

@app.get("/slow")
async def slow_endpoint():
    await asyncio.sleep(2)
    return {"message": "slow"}

@app.get("/custom_timeout")
async def custom_timeout_endpoint():
    await asyncio.sleep(0.5)
    return {"message": "custom"}

@app.get("/slow_allowed")
async def slow_allowed():
    await asyncio.sleep(2)
    return {"message": "slow_allowed"}


client = TestClient(app)

def test_default_timeout_success():
    settings.REQUEST_TIMEOUT = 1
    
    response = client.get("/fast")
    assert response.status_code == 200

def test_default_timeout_failure():
    settings.REQUEST_TIMEOUT = 1
    
    start = time.time()
    response = client.get("/slow")
    duration = time.time() - start
    
    # It might take slightly more than 1s due to processing, but should be < 2s (endpoint duration)
    # The middleware cuts it off at 1s.
    assert response.status_code == 504
    assert response.text == "Request timed out"

def test_custom_timeout_rule():
    settings.REQUEST_TIMEOUT = 1
    # Allow 3s for /slow_allowed
    settings.TIMEOUT_RULES = [
        TimeoutRule(path_pattern="^/slow_allowed", timeout=3)
    ]
    
    # Endpoint takes 2s, rule allows 3s. Should pass.
    response = client.get("/slow_allowed")
    assert response.status_code == 200
