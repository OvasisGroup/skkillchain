import pytest
from django.core.cache import cache
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture(autouse=True)
def _clear_cache():
    # The RBAC permission cache and DRF's throttle counters both live in the
    # shared Redis cache — without this, one test's throttle hits or role
    # cache entries bleed into the next test.
    cache.clear()
    yield
    cache.clear()
