import sys
import os

from fastapi.testclient import TestClient

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from main import app

client = TestClient(app)


def test_health_check():
    response = client.get('/')
    assert response.status_code == 200
    assert response.json() == {'message': 'OK'}


def test_agent_response():
    params = {'input': 'Oi', 'session_id': '1'}
    response = client.post('/api/v1/agent/predict', params=params)
    assert response.status_code == 200
