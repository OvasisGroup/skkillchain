from django.urls import path

from . import views

urlpatterns = [
    path("plans/", views.PlanListView.as_view(), name="plan-list"),
    path("subscriptions/", views.SubscriptionListView.as_view(), name="subscription-list"),
    path(
        "subscriptions/<uuid:id>/cancel/",
        views.SubscriptionCancelView.as_view(),
        name="subscription-cancel",
    ),
]
