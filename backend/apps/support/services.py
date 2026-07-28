from django.db import transaction

from .models import SupportTicket, SupportTicketMessage


def create_ticket(
    requester, *, category: str, priority: str, subject: str, body: str
) -> SupportTicket:
    with transaction.atomic():
        ticket = SupportTicket.objects.create(
            requester=requester, category=category, priority=priority, subject=subject
        )
        SupportTicketMessage.objects.create(ticket=ticket, sender=requester, body=body)
    return ticket


def add_ticket_message(ticket: SupportTicket, sender, body: str) -> SupportTicketMessage:
    message = SupportTicketMessage.objects.create(ticket=ticket, sender=sender, body=body)
    _notify_other_party(ticket, sender, message)
    if sender.id != ticket.requester_id and ticket.status == SupportTicket.STATUS_OPEN:
        # A reply from anyone other than the requester (i.e. an assigned
        # agent) is what actually moves a ticket off "open" — the
        # SLA-aware part of this workflow.
        ticket.status = SupportTicket.STATUS_IN_PROGRESS
        ticket.save(update_fields=["status"])
    return message


def _notify_other_party(ticket: SupportTicket, sender, message: SupportTicketMessage) -> None:
    from apps.notifications.services import notify

    recipient = ticket.assignee if sender.id == ticket.requester_id else ticket.requester
    if recipient is None or recipient.id == sender.id:
        return
    notify(
        recipient,
        type="support_ticket",
        channels=["in_app", "email"],
        title=f"New reply on: {ticket.subject}",
        body=message.body,
    )
