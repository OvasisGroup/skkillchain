from django.db import connection
from django.http import JsonResponse


def liveness(request):
    """Process is up. Never touches the network — used for k8s liveness probes."""
    return JsonResponse({"status": "ok"})


def readiness(request):
    """Process can actually serve traffic — used for k8s readiness probes."""
    checks = {}
    healthy = True

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        checks["database"] = "ok"
    except Exception as exc:  # noqa: BLE001 — any DB failure means "not ready"
        checks["database"] = f"error: {exc}"
        healthy = False

    status = "ok" if healthy else "error"
    return JsonResponse({"status": status, "checks": checks}, status=200 if healthy else 503)
