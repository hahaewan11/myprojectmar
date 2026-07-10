from django.urls import path
from django.contrib.auth import views as auth_views
from . import views as security_views

urlpatterns = [
    path("", security_views.login_view, name="login"),
    path("register/", security_views.register_view, name="register"),
    path("logout/", security_views.logout_view, name="logout"),
    path("admin/analytics/", security_views.admin_analytics_view, name="admin_analytics"),
    path("admin/notifications/", security_views.admin_notifications_view, name="admin_notifications"),
    path("admin/report/<str:report_id>/", security_views.admin_report_detail, name="admin_report_detail"),
    path("verify-email/<uuid:token>/", security_views.verify_email, name="verify_email"),
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