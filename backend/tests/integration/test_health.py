import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_liveness_returns_ok(client):
    response = client.get(reverse("health-live"))
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.django_db
def test_readiness_reports_database_ok(client):
    response = client.get(reverse("health-ready"))
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["checks"]["database"] == "ok"
