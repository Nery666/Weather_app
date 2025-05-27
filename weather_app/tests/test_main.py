from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_home():
    response = client.get("/")
    assert response.status_code == 200

def test_weather():
    response = client.get("/weather?city=Moscow")
    assert response.status_code == 200

def test_stats():
    response = client.get("/api/stats")
    assert response.status_code == 200