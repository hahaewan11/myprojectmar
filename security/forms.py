from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django_recaptcha.fields import ReCaptchaField
from django_recaptcha.widgets import ReCaptchaV2Checkbox
from django.core.exceptions import ValidationError
from .models import Report
import datetime


VIOLENCE_CHOICES = [
    ('Physical', 'Physical'),
    ('Emotional', 'Emotional'),
    ('Sexual', 'Sexual'),
    ('Economic', 'Economic'),
    ('Harassment', 'Harassment'),
]


class GBVReportForm(forms.Form):
    full_name = forms.CharField(
        label='Full Name',
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your full name'})
    )
    email = forms.EmailField(
        label='Email Address',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'you@example.com'})
    )
    contact_number = forms.CharField(
        label='Contact Number',
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+63 912 345 6789'})
    )
    title = forms.CharField(
        label='Report Title',
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Short title for the incident'})
    )
    description = forms.CharField(
        label='Incident Description',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Describe the incident in detail'})
    )
    date_of_incident = forms.DateField(
        label='Incident Date',
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    location = forms.CharField(
        label='Incident Location',
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City, Barangay, or address'})
    )
    type_of_violence = forms.ChoiceField(
        label='Type of Violence',
        choices=VIOLENCE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Create a password'})
    )
    confirm_password = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm your password'})
    )
    terms = forms.BooleanField(
        label='I agree to the Terms and Conditions',
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    def clean_contact_number(self):
        num = (self.cleaned_data.get('contact_number') or '').strip()
        if not num:
            raise ValidationError('Please provide a contact number.')
        # simple digits check
        digits = ''.join(ch for ch in num if ch.isdigit())
        if len(digits) < 7:
            raise ValidationError('Please enter a valid contact number.')
        return num

    def clean_date_of_incident(self):
        d = self.cleaned_data.get('date_of_incident')
        if d and d > datetime.date.today():
            raise ValidationError('Incident date cannot be in the future.')
        return d

    def clean_description(self):
        desc = (self.cleaned_data.get('description') or '').strip()
        if len(desc) < 20:
            raise ValidationError('Please provide a more detailed description (at least 20 characters).')
        return desc

    def clean(self):
        cleaned = super().clean()
        pw = cleaned.get('password')
        pw2 = cleaned.get('confirm_password')
        if pw and pw2:
            if pw != pw2:
                raise ValidationError({'confirm_password': 'Passwords do not match.'})
            if len(pw) < 8:
                raise ValidationError({'password': 'Password must be at least 8 characters long.'})
        return cleaned


class LoginForm(forms.Form):
    username = forms.CharField(
        label='Username',
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your username'
        })
    )
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password'
        })
    )
    captcha = ReCaptchaField(
        widget=ReCaptchaV2Checkbox(),
        label='Verify you are human'
    )


class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email'
        })
    )
    first_name = forms.CharField(
        label='First Name',
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your first name'
        })
    )
    last_name = forms.CharField(
        label='Last Name',
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your last name'
        })
    )

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'username', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super(RegisterForm, self).__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter your username'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter your password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm your password'
        })

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('This email is already registered.')
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('This username is already taken.')
        return username


class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = (
            'title',
            'case_type',
            'location',
            'date_of_incident',
            'time_of_incident',
            'description',
        )
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Short title for the incident'}),
            'case_type': forms.Select(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Example: Brgy. 2, City'}),
            'date_of_incident': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'time_of_incident': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Describe the full incident'}),
        }

    def clean_title(self):
        title = (self.cleaned_data.get('title') or '').strip()
        if not title:
            raise ValidationError('Title is required.')
        if len(title) > 200:
            raise ValidationError('Title must be 200 characters or fewer.')
        return title

    def clean_description(self):
        description = (self.cleaned_data.get('description') or '').strip()
        if not description:
            raise ValidationError('Description is required.')
        return description

    def clean_case_type(self):
        case_type = self.cleaned_data.get('case_type')
        if not case_type:
            raise ValidationError('Please select a case type.')
        return case_type

    def clean_date_of_incident(self):
        date_val = self.cleaned_data.get('date_of_incident')
        if date_val and date_val > datetime.date.today():
            raise ValidationError('Date of incident cannot be in the future.')
        return date_val
