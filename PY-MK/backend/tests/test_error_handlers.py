from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel, model_validator

from app.core.error_handlers import register_exception_handlers
from app.core.exceptions import AppError


def test_app_error_with_custom_status():
    """Test that AppError with custom status code returns correct response."""
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/test")
    def test_endpoint():
        raise AppError("Ya existe", status_code=409)

    client = TestClient(app)
    response = client.get("/test")
    
    assert response.status_code == 409
    assert response.json() == {"message": "Ya existe", "type": "app_error"}


def test_app_error_default_status():
    """Test that AppError without status code defaults to 400."""
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/test")
    def test_endpoint():
        raise AppError("x")

    client = TestClient(app)
    response = client.get("/test")
    
    assert response.status_code == 400
    assert response.json() == {"message": "x", "type": "app_error"}


def test_validation_error_with_model_validator():
    """Test that validation errors from model validators don't cause 500."""
    app = FastAPI()
    register_exception_handlers(app)

    class TestModel(BaseModel):
        name: str

        @model_validator(mode="after")
        def validate_dates(self):
            raise ValueError("fechas al revés")
    
    @app.post("/test")
    def test_endpoint(model: TestModel):
        return {"message": "success"}

    client = TestClient(app)
    response = client.post("/test", json={"name": "test"})
    
    assert response.status_code == 422
    assert response.json()["type"] == "validation_error"
    assert response.json()["message"] == "Payload validation failed"
    assert len(response.json()["details"]) > 0
    # Verify no "ctx" key in details
    for detail in response.json()["details"]:
        assert "ctx" not in detail


def test_validation_error_with_missing_field():
    """Test that missing required fields cause 422 with validation error."""
    app = FastAPI()
    register_exception_handlers(app)

    class TestModel(BaseModel):
        name: str
    
    @app.post("/test")
    def test_endpoint(model: TestModel):
        return {"message": "success"}

    client = TestClient(app)
    response = client.post("/test", json={})
    
    assert response.status_code == 422
    assert response.json()["type"] == "validation_error"
