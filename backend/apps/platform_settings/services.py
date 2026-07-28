from .models import Setting


def upsert_setting(*, scope_type: str, scope_id, key: str, value_json) -> Setting:
    setting, _created = Setting.objects.update_or_create(
        scope_type=scope_type, scope_id=scope_id, key=key, defaults={"value_json": value_json}
    )
    return setting
