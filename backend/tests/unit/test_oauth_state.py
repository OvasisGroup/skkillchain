from apps.live_sessions import oauth_state


class TestOAuthState:
    def test_issue_and_resolve_roundtrip(self):
        token = oauth_state.issue_state("user-123", "zoom")

        data = oauth_state.resolve_state(token)

        assert data == {"user_id": "user-123", "provider": "zoom"}

    def test_resolve_rejects_tampered_token(self):
        token = oauth_state.issue_state("user-123", "zoom")

        assert oauth_state.resolve_state(token + "tampered") is None

    def test_resolve_rejects_garbage_input(self):
        assert oauth_state.resolve_state("not-a-real-token") is None

    def test_resolve_rejects_expired_token(self, monkeypatch):
        real_time = __import__("time").time
        token = oauth_state.issue_state("user-123", "zoom")

        # oauth_state._MAX_AGE_SECONDS is 600 — fast-forward past it by
        # patching django.core.signing's own `time.time`, the exact clock
        # TimestampSigner.unsign() checks against.
        monkeypatch.setattr(
            "django.core.signing.time.time", lambda: real_time() + oauth_state._MAX_AGE_SECONDS + 1
        )

        assert oauth_state.resolve_state(token) is None
