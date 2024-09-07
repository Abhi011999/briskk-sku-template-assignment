import os
import sys
import pytest
from fastapi.testclient import TestClient

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.main import app

@pytest.fixture(scope="module")
def test_app():
    client = TestClient(app)
    return client

def test_ingest_endpoint(test_app):
    with open("tests/Briskk-Sku-Template-Assignment.xlsx", "rb") as f:
        response = test_app.post("/ingest", files={"file": ("Briskk-Sku-Template-Assignment.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
    
    assert response.status_code == 200
    assert "ingested_count" in response.json()
    assert response.json()["ingested_count"] > 0

def test_products_endpoint(test_app):
    response = test_app.get("/products")
    
    assert response.status_code == 200
    assert "products" in response.json()
    assert len(response.json()["products"]) > 0
    
    first_product = response.json()["products"][0]
    assert "product_id" in first_product
    assert "product_name" in first_product
    assert "brand" in first_product
    assert "skus" in first_product
    assert len(first_product["skus"]) > 0
