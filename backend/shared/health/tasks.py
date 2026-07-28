from celery import shared_task


@shared_task(name="shared.health.ping")
def ping() -> str:
    """Proves a worker is actually consuming from the broker — see
    Makefile `celery-ping` / the M4 live_sessions commit notes for how
    this got verified against real RabbitMQ before anything was built on
    top of it."""
    return "pong"
