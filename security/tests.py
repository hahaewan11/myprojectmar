from django.test import SimpleTestCase

from .forms import LoginForm


class LoginFormTests(SimpleTestCase):
    def test_login_form_contains_captcha_field(self):
        form = LoginForm()
        self.assertIn('captcha', form.fields)
        self.assertEqual(form.fields['captcha'].__class__.__name__, 'ReCaptchaField')
