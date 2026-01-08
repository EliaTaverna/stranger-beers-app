"""Tests for the ingestion API."""

import pytest
from fastapi.testclient import TestClient

from apps.ingestion_api.src.main import app


@pytest.fixture
def client():
    """Create test client for the ingestion API."""
    return TestClient(app)


class TestHealthEndpoint:
    """Tests for the health check endpoint."""

    def test_health_returns_200(self, client):
        """Health endpoint returns 200 OK."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_response_structure(self, client):
        """Health response has correct structure."""
        response = client.get("/health")
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "ingestion-api"


class TestRootEndpoint:
    """Tests for the root endpoint."""

    def test_root_returns_service_info(self, client):
        """Root endpoint returns service information."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "Stranger Beers Ingestion API"
        assert "version" in data


class TestTallyWebhook:
    """Tests for the Tally webhook endpoint."""

    def test_webhook_accepts_valid_payload(self, client):
        """Webhook accepts valid Tally payload."""
        payload = {
            "event_id": "test-123",
            "event_type": "form.submitted",
            "created_at": "2024-01-01T00:00:00Z",
            "data": {"fields": []},
        }
        response = client.post("/webhooks/tally", json=payload)
        assert response.status_code == 201
        assert response.json()["status"] == "received"

    def test_webhook_returns_event_id(self, client):
        """Webhook response includes event_id."""
        payload = {
            "event_id": "abc-456",
            "event_type": "form.submitted",
            "created_at": "2024-01-01T00:00:00Z",
            "data": {},
        }
        response = client.post("/webhooks/tally", json=payload)
        assert response.json()["event_id"] == "abc-456"
