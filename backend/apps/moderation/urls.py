from django.urls import path

from . import views

urlpatterns = [
    path("instructor/apply/", views.InstructorApplyView.as_view(), name="instructor-apply"),
    path(
        "admin/instructors/", views.AdminInstructorListView.as_view(), name="admin-instructor-list"
    ),
    path(
        "admin/instructors/<uuid:user_id>/approve/",
        views.AdminInstructorApproveView.as_view(),
        name="admin-instructor-approve",
    ),
]
