from .models import AuditLog


def record_event(*, actor, action, entity_type="", entity_id="", request=None, payload=None):
    ip_address = None
    user_agent = ""
    if request is not None:
        ip_address = _client_ip(request)
        user_agent = request.META.get("HTTP_USER_AGENT", "")[:512]

    return AuditLog.objects.create(
        actor=actor,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id != "" else "",
        ip_address=ip_address,
        user_agent=user_agent,
        payload=payload or {},
    )


def _client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")
