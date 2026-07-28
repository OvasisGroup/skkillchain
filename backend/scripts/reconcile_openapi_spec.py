#!/usr/bin/env python
"""
Diffs the live, generated OpenAPI schema against the hand-authored
docs/03-api/02-openapi.yaml, reporting any (path, method) operation present
in one but not the other. Path parameter names are normalized away before
comparing (`{course_id}` and `{id}` for the same route shouldn't count as a
mismatch) so the diff surfaces genuinely missing/extra routes, not naming
noise.

Usage:
    python scripts/reconcile_openapi_spec.py [--fix-docs]

Exit code is non-zero if any discrepancy remains — wired into CI
(.github/workflows/backend-ci.yml) as a real merge gate, replacing the
former `--file /dev/null` placeholder that only checked the live schema
generates without warnings.

--fix-docs is intentionally NOT implemented: reconciling a real discrepancy
means a human decides whether a route was forgotten in the docs or never
actually built, not a mechanical rewrite.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SPEC_PATH = REPO_ROOT / "docs" / "03-api" / "02-openapi.yaml"

_PARAM_RE = re.compile(r"\{[^}]+\}")
# docs/03-api/02-openapi.yaml's `servers:` entry already ends in `/api/v1`,
# so its paths are written relative to that (e.g. `/auth/register`). The
# live schema's paths include the full `/api/v1/...` prefix — strip it so
# the two are comparable.
_LIVE_PREFIX = "/api/v1"


def _normalize(path: str) -> str:
    if path.startswith(_LIVE_PREFIX):
        path = path[len(_LIVE_PREFIX) :]
    return _PARAM_RE.sub("{param}", path).rstrip("/")


def _live_operations() -> set[tuple[str, str]]:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
    os.environ.setdefault("SECRET_KEY", "reconcile-openapi-only")
    os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

    sys.path.insert(0, str(REPO_ROOT / "backend"))
    import django

    django.setup()

    from drf_spectacular.generators import SchemaGenerator

    generator = SchemaGenerator()
    schema = generator.get_schema(request=None, public=True)
    operations = set()
    for path, methods in schema.get("paths", {}).items():
        for method in methods:
            if method.lower() in {"get", "post", "put", "patch", "delete"}:
                operations.add((_normalize(path), method.lower()))
    return operations


def _documented_operations() -> set[tuple[str, str]]:
    with SPEC_PATH.open() as fh:
        spec = yaml.safe_load(fh)
    operations = set()
    for path, methods in spec.get("paths", {}).items():
        for method in methods:
            if method.lower() in {"get", "post", "put", "patch", "delete"}:
                operations.add((_normalize(path), method.lower()))
    return operations


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()

    live = _live_operations()
    documented = _documented_operations()

    missing_from_docs = sorted(live - documented)
    extra_in_docs = sorted(documented - live)

    if not missing_from_docs and not extra_in_docs:
        print(f"OK: {len(live)} live operations all accounted for in {SPEC_PATH}.")
        return 0

    if missing_from_docs:
        print(f"Live routes missing from {SPEC_PATH} ({len(missing_from_docs)}):")
        for path, method in missing_from_docs:
            print(f"  {method.upper():6} {path}")

    if extra_in_docs:
        print(f"Documented routes with no live match ({len(extra_in_docs)}):")
        for path, method in extra_in_docs:
            print(f"  {method.upper():6} {path}")

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
