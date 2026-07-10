from django.test import SimpleTestCase
from users import views as users_views


class UsersViewsTests(SimpleTestCase):
    def test_user_views_are_available_from_users_app(self):
        self.assertTrue(hasattr(users_views, "dashboard_intro_view"))
        self.assertTrue(hasattr(users_views, "dashboard_view"))
        self.assertTrue(hasattr(users_views, "dashboard_submit_view"))
        self.assertTrue(hasattr(users_views, "my_reports_view"))
        self.assertTrue(hasattr(users_views, "user_profile_view"))
        self.assertTrue(hasattr(users_views, "chatbot_view"))
        self.assertTrue(hasattr(users_views, "report_anonymous_view"))
