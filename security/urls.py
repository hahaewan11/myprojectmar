from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path("", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("logout/", views.logout_view, name="logout"),
    path("report/", views.report_anonymous_view, name="report_anonymous"),
    path("profile/", views.user_profile_view, name="user_profile"),
    path("dashboard/intro/", views.dashboard_intro_view, name="dashboard_intro"),
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path("dashboard/submit/", views.dashboard_submit_view, name="dashboard_submit"),
    path("dashboard/my-reports/", views.my_reports_view, name="my_reports"),
    path("dashboard/report/<int:report_id>/", views.report_detail_user, name="report_detail"),
    path("admin/analytics/", views.admin_analytics_view, name="admin_analytics"),
    path("admin/notifications/", views.admin_notifications_view, name="admin_notifications"),
    path("admin/report/<str:report_id>/", views.admin_report_detail, name="admin_report_detail"),
    path("chatbot/", views.chatbot_view, name="chatbot"),
    path("verify-email/<uuid:token>/", views.verify_email, name="verify_email"),
        path(
        "password-reset/",
        auth_views.PasswordResetView.as_view(
            template_name="password_reset.html"
        ),
        name="password_reset",
    ),

    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="password_reset_done.html"
        ),
        name="password_reset_done",
    ),

    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="password_reset_confirm.html"
        ),
        name="password_reset_confirm",
    ),

    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),
]