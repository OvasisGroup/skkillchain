from django.conf import settings
from django.core.mail import send_mail

from ..models import EmailTemplate
from .base import NotificationProvider


class EmailProvider(NotificationProvider):
    code = "email"

    def send(self, notification, *, title: str, body: str) -> None:
        html_body = None
        if notification.template_code:
            email_template = (
                EmailTemplate.objects.filter(code=notification.template_code, is_active=True)
                .order_by("locale")
                .first()
            )
            if email_template is not None:
                html_body = email_template.html_body or None

        send_mail(
            subject=title,
            message=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[notification.user.email],
            html_message=html_body,
        )
