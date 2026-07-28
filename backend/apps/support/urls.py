from django.urls import path

from . import views

urlpatterns = [
    path(
        "support-tickets/",
        views.SupportTicketListCreateView.as_view(),
        name="support-ticket-list-create",
    ),
    path(
        "support-tickets/<uuid:ticket_id>/messages/",
        views.SupportTicketMessageListCreateView.as_view(),
        name="support-ticket-message-list-create",
    ),
]
