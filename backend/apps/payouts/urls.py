from django.urls import path

from . import views

urlpatterns = [
    path("instructor/wallet/", views.InstructorWalletView.as_view(), name="instructor-wallet"),
    path(
        "instructor/payouts/",
        views.InstructorPayoutListView.as_view(),
        name="instructor-payout-list",
    ),
    path(
        "instructor/payout-requests/",
        views.InstructorPayoutRequestView.as_view(),
        name="instructor-payout-request",
    ),
]
