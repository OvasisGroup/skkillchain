from django.urls import path

from . import views

urlpatterns = [
    path("affiliate/register/", views.AffiliateRegisterView.as_view(), name="affiliate-register"),
    path("affiliate/me/", views.AffiliateMeView.as_view(), name="affiliate-me"),
    path(
        "affiliate/referrals/",
        views.AffiliateReferralListView.as_view(),
        name="affiliate-referral-list",
    ),
    path(
        "affiliate/commissions/",
        views.AffiliateCommissionListView.as_view(),
        name="affiliate-commission-list",
    ),
    path("affiliate/wallet/", views.AffiliateWalletView.as_view(), name="affiliate-wallet"),
    path(
        "affiliate/payout-requests/",
        views.AffiliatePayoutRequestView.as_view(),
        name="affiliate-payout-request",
    ),
]
