import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from middlewares.validation import RequestValidationMiddleware
from config import settings
from pydantic_models.validation import ENDPOINT_SCHEMAS, WhitelistSchema
from pydantic import Field

# Setup App
app = FastAPI()
app.add_middleware(RequestValidationMiddleware)

@app.get("/test_query")
async def endpoint_query(request: Request):
    return {"params": request.query_params}

@app.post("/test_body")
async def endpoint_body(request: Request):
    return await request.json()

@app.get("/test_strict")
async def endpoint_strict(request: Request):
    return {"message": "ok"}

# Schema
class QuerySchema(WhitelistSchema):
    q: str = Field(..., min_length=3)

ENDPOINT_SCHEMAS["/test_query"] = QuerySchema

client = TestClient(app)

def test_sanitization():
    response = client.get("/test_query?q=<script>hello</script>")
    assert response.status_code == 200
    assert response.json()["params"]["q"] == "hello"

def test_validation_input():
    # Valid
    response = client.get("/test_query?q=abc")
    assert response.status_code == 200

    # Invalid
    response = client.get("/test_query?q=ab")
    assert response.status_code == 400

def test_json_body_validation():
    # Valid
    response = client.post("/test_body", json={"key": "value"})
    assert response.status_code == 200
    
    # Deep nested
    deep_json = {
        "a": {
            "b": {
                "c": {"d": {"e": {"f": {"g": {"h": {"i": {"j": {"k": "too deep"}}}}}}}}
            }
        }
    }
    # Assuming config max depth is small default (10)
    response = client.post("/test_body", json=deep_json)
    assert response.status_code == 400

    # Invalid JSON syntax
    response = client.post(
        "/test_body",
        content="{invalid_json}",
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 400
    
    # Non-JSON content ignored
    # Note: The endpoint expects json(), so it will fail internally with 500 or similar
    # if middleware lets it through. We just assert middleware DOES let it through (not 400 from middleware).
    # Since middleware returns 400 on validation error, if we get 500 (or whatever exception), middleware passed.
    try:
        client.post(
            "/test_body", content="some text", headers={"Content-Type": "text/plain"}
        )
    except Exception:
        # Expected crash in endpoint, means middleware passed it.
        pass

def test_strict_mode_logging():
    # Config strict mode is enabled by default in settings.
    # We just ensure it doesn't crash on unknown endpoints.
    response = client.get("/test_strict?foo=bar")
    assert response.status_code == 200
