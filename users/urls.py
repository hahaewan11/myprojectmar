from django.urls import path
from . import views

urlpatterns = [
    path("profile/", views.user_profile_view, name="user_profile"),
    path("dashboard/intro/", views.dashboard_intro_view, name="dashboard_intro"),
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path("dashboard/submit/", views.dashboard_submit_view, name="dashboard_submit"),
    path("dashboard/my-reports/", views.my_reports_view, name="my_reports"),
    path("dashboard/report/<int:report_id>/", views.report_detail_user, name="report_detail"),
    path("chatbot/", views.chatbot_view, name="chatbot"),
    path("report/", views.report_anonymous_view, name="report_anonymous"),
]
