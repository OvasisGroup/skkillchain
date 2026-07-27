import pytest
from django.test import RequestFactory

from apps.audit.models import AuditLog
from apps.audit.services import record_event

pytestmark = pytest.mark.django_db


def test_audit_log_cannot_be_modified():
    entry = AuditLog.objects.create(action="test.action")
    entry.action = "changed"

    with pytest.raises(ValueError):
        entry.save()


def test_audit_log_cannot_be_deleted():
    entry = AuditLog.objects.create(action="test.action")

    with pytest.raises(ValueError):
        entry.delete()


def test_record_event_captures_request_metadata():
    request = RequestFactory().post(
        "/x/", REMOTE_ADDR="203.0.113.5", HTTP_USER_AGENT="pytest-agent"
    )

    entry = record_event(actor=None, action="test.event", request=request)

    assert entry.ip_address == "203.0.113.5"
    assert entry.user_agent == "pytest-agent"


def test_record_event_prefers_x_forwarded_for():
    request = RequestFactory().post(
        "/x/", REMOTE_ADDR="10.0.0.1", HTTP_X_FORWARDED_FOR="203.0.113.9, 10.0.0.1"
    )

    entry = record_event(actor=None, action="test.event", request=request)

    assert entry.ip_address == "203.0.113.9"


def test_record_event_without_request_still_works():
    entry = record_event(actor=None, action="test.event")

    assert entry.ip_address is None
    assert entry.user_agent == ""
