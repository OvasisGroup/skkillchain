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
    path(
        "admin/support-tickets/",
        views.AdminSupportTicketListView.as_view(),
        name="admin-support-ticket-list",
    ),
    path(
        "admin/support-tickets/<uuid:pk>/",
        views.AdminSupportTicketUpdateView.as_view(),
        name="admin-support-ticket-update",
    ),
]
