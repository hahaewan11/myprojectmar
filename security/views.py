from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import csrf_protect
from django.utils import timezone
from firebase_config import db
from django.core.mail import send_mail
from django.urls import reverse
from .forms import LoginForm, RegisterForm, ReportForm, GBVReportForm
from .models import Report, Notification, UserProfile
from django.http import HttpResponse

import datetime
import json


@login_required(login_url='login')
def report_detail_user(request, report_id):
    """Allow a logged-in user to view details of their own report only."""
    report = get_object_or_404(Report, id=report_id, reporter=request.user)
    return render(request, "report_detail_user.html", {"report": report})


def login_view(request):
    form = LoginForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")

            user = authenticate(request, username=username, password=password)

            if user is not None:

                # Skip email verification for admin
                if not user.is_staff:
                    profile, created = UserProfile.objects.get_or_create(user=user)

                    if not profile.email_verified:
                        messages.error(
                            request,
                            "Please verify your email first before logging in."
                        )
                        return redirect("login")

                login(request, user)

                if user.is_staff:
                    return redirect("admin_dashboard")

                return redirect("dashboard_intro")

            else:
                messages.error(request, "Invalid username or password")

        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")

    return render(request, "login.html", {"form": form})

def register_view(request):
    form = RegisterForm(request.POST or None)

    success_message = None
    show_login_button = False

    if request.method == "POST":
        if form.is_valid():

            user = form.save()

            # Create User Profile
            profile = UserProfile.objects.create(user=user)

            # Verification Link
            verification_link = request.build_absolute_uri(
                reverse("verify_email", args=[str(profile.verification_token)])
            )

            # Send Verification Email
            send_mail(
                subject="Verify Your Email - GBV Support System",
                message=f"""
Hello {user.username},

Thank you for registering.

Please verify your email by clicking the link below:

{verification_link}

If you did not create this account, you may ignore this email.
""",
                from_email=None,
                recipient_list=[user.email],
                fail_silently=False,
            )

            # Save user to Firebase
            db.collection("users").document(str(user.id)).set({
                "user_id": user.id,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "date_joined": str(user.date_joined),
                "is_staff": user.is_staff
            })

            messages.success(
            request,
             "Registration successful! Please check your email and verify your account before logging in."
            )

            return redirect("login")

        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")

    return render(
        request,
        "register.html",
        {
            "form": form,
            "success_message": success_message,
            "show_login_button": show_login_button,
        },
    )

@login_required(login_url='login')
def user_profile_view(request):
    user = request.user
    # Hide the Profile nav button on the profile page itself because the user is already there.
    hide_profile_button = True

    context = {
        'user': user,
        'hide_profile_button': hide_profile_button,
    }
    return render(request, "user_profile.html", context)


@login_required(login_url='login')
def dashboard_intro_view(request):
    user = request.user
    return render(request, "dashboard_intro.html", {'user': user})


@login_required(login_url='login')
def dashboard_view(request):
    user = request.user
    reports = Report.objects.filter(reporter=user).order_by('-created_at')
    notification_qs = Notification.objects.filter(user=user).order_by('-created_at')
    notifications = notification_qs[:5]
    unread_count = notification_qs.filter(is_read=False).count()
    my_reports_count = reports.count()
    pending_reports_count = reports.filter(status__in=[Report.STATUS_SUBMITTED, Report.STATUS_UNDER_REVIEW, Report.STATUS_IN_PROGRESS]).count()
    under_review_count = reports.filter(status=Report.STATUS_UNDER_REVIEW).count()
    resolved_reports_count = reports.filter(status=Report.STATUS_RESOLVED).count()

    context = {
        'user': user,
        'reports': reports,
        'notifications': notifications,
        'unread_count': unread_count,
        'my_reports_count': my_reports_count,
        'pending_reports_count': pending_reports_count,
        'under_review_count': under_review_count,
        'resolved_reports_count': resolved_reports_count,
    }
    return render(request, "dashboard_user.html", context)


@login_required(login_url='login')
def dashboard_submit_view(request):
    user = request.user
    form = ReportForm(request.POST or None)

    if request.method == "POST":
        form = ReportForm(request.POST)

        if form.is_valid():
            report = form.save(commit=False)
            report.reporter = user
            report.email = user.email or ""
            report.is_anonymous = False
            report.status = Report.STATUS_SUBMITTED
            report.save()

            # Notification para sa user
            Notification.objects.create(
                user=user,
                report=report,
                message=f"New report submitted: {report.reference_number}",
                notification_type=Notification.NOTIFICATION_REPORT,
            )

            # Notification at email para sa lahat ng admin
            for staff_user in User.objects.filter(is_staff=True, is_active=True):

                # Dashboard notification
                Notification.objects.create(
                    user=staff_user,
                    report=report,
                    message=f"New report submitted by {user.get_full_name() or user.username}: {report.reference_number}",
                    notification_type=Notification.NOTIFICATION_REPORT,
                )

                # Email notification
                if staff_user.email:
                    try:
                        send_mail(
                            subject="🚨 New GBV Report Submitted",
                            message=f"""
Hello {staff_user.get_full_name() or staff_user.username},

A new GBV report has been submitted.

Reference Number:
{report.reference_number}

Reporter:
{user.get_full_name() or user.username}

Email:
{user.email}

Title:
{report.title}

Status:
{report.status}

Please log in to the Admin Dashboard to review this report.

Thank you,
GBV Support System
                            """,
                            from_email=None,
                            recipient_list=[staff_user.email],
                            fail_silently=False,
                        )
                    except Exception as e:
                        print("Admin Email Error:", e)

            # Save sa Firebase
            db.collection("reports").add({
                "reference_number": report.reference_number,
                "reporter": user.username,
                "email": user.email,
                "title": report.title,
                "description": report.description,
                "status": report.status,
                "created_at": str(report.created_at)
            })

            messages.success(
                request,
                "Report submitted successfully. Your report is now in the system."
            )
            return redirect('my_reports')

        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")

    return render(
        request,
        "dashboard_submit.html",
        {
            'user': user,
            'form': form
        }
    )


@login_required(login_url='login')
def my_reports_view(request):
    user = request.user
    reports = Report.objects.filter(reporter=user).order_by('-created_at')
    total_reports = reports.count()
    submitted_count = reports.filter(status=Report.STATUS_SUBMITTED).count()
    under_review_count = reports.filter(status=Report.STATUS_UNDER_REVIEW).count()
    in_progress_count = reports.filter(status=Report.STATUS_IN_PROGRESS).count()
    resolved_count = reports.filter(status=Report.STATUS_RESOLVED).count()

    context = {
        'user': user,
        'reports': reports,
        'total_reports': total_reports,
        'submitted_count': submitted_count,
        'under_review_count': under_review_count,
        'in_progress_count': in_progress_count,
        'resolved_count': resolved_count,
    }
    return render(request, "my_reports.html", context)


@staff_member_required
def admin_dashboard_view(request):
    """Dashboard view exposed for admin/staff users at /admin/dashboard/."""
    reports = Report.objects.all().order_by('-created_at')[:15]
    notification_qs = Notification.objects.filter(user=request.user).order_by('-created_at')
    notifications = notification_qs[:5]
    unread_notifications_count = notification_qs.filter(is_read=False).count()

    context = {
        'hide_dashboard_button': True,
        'reports': reports,
        'total_reports': Report.objects.count(),
        'new_reports': Report.objects.filter(status=Report.STATUS_SUBMITTED).count(),
        'in_progress': Report.objects.filter(status=Report.STATUS_IN_PROGRESS).count(),
        'resolved_reports': Report.objects.filter(status=Report.STATUS_RESOLVED).count(),
        'urgent_cases': Report.objects.filter(status=Report.STATUS_UNDER_REVIEW).count(),
        'anonymous_reports': Report.objects.filter(is_anonymous=True).count(),
        'named_reports': Report.objects.filter(is_anonymous=False).count(),
        'notifications': notifications,
        'unread_notifications_count': unread_notifications_count,
    }
    return render(request, "dashboard.html", context)


@staff_member_required
def admin_analytics_view(request):
    reports = Report.objects.all().order_by('-created_at')
    filter_start = request.GET.get('start_date')
    filter_end = request.GET.get('end_date')
    selected_status = request.GET.get('status', 'all')
    selected_case_type = request.GET.get('case_type', 'all')

    if filter_start:
        try:
            reports = reports.filter(created_at__date__gte=datetime.date.fromisoformat(filter_start))
        except ValueError:
            filter_start = None

    if filter_end:
        try:
            reports = reports.filter(created_at__date__lte=datetime.date.fromisoformat(filter_end))
        except ValueError:
            filter_end = None

    if selected_status and selected_status != 'all':
        reports = reports.filter(status=selected_status)

    if selected_case_type and selected_case_type != 'all':
        reports = reports.filter(case_type=selected_case_type)

    total_reports = reports.count()
    resolved_reports = reports.filter(status=Report.STATUS_RESOLVED).count()
    pending_reports = reports.filter(status__in=[Report.STATUS_SUBMITTED, Report.STATUS_UNDER_REVIEW, Report.STATUS_IN_PROGRESS]).count()
    anonymous_reports = reports.filter(is_anonymous=True).count()
    named_reports = reports.filter(is_anonymous=False).count()

    status_labels = [choice[0] for choice in Report.STATUS_CHOICES]
    status_counts = [reports.filter(status=status).count() for status in status_labels]
    case_type_labels = [choice[0] for choice in Report.CASE_TYPE_CHOICES]
    case_type_counts = [reports.filter(case_type=value).count() for value in case_type_labels]

    today = timezone.now().date()
    monthly_labels = []
    monthly_counts = []
    first_of_month = today.replace(day=1)
    for months_ago in range(5, -1, -1):
        month_offset = first_of_month.month - months_ago
        year = first_of_month.year
        while month_offset <= 0:
            month_offset += 12
            year -= 1
        monthly_date = datetime.date(year, month_offset, 1)
        monthly_labels.append(monthly_date.strftime('%b %Y'))
        monthly_counts.append(reports.filter(created_at__year=year, created_at__month=month_offset).count())

    notification_qs = Notification.objects.filter(user=request.user).order_by('-created_at')
    notifications = notification_qs[:5]
    unread_notifications_count = notification_qs.filter(is_read=False).count()

    context = {
        'reports': reports[:12],
        'total_reports': total_reports,
        'resolved_reports': resolved_reports,
        'pending_reports': pending_reports,
        'anonymous_reports': anonymous_reports,
        'named_reports': named_reports,
        'status_labels': status_labels,
        'status_counts': status_counts,
        'case_type_labels': case_type_labels,
        'case_type_counts': case_type_counts,
        'monthly_labels': monthly_labels,
        'monthly_counts': monthly_counts,
        'status_labels_json': json.dumps(status_labels),
        'status_counts_json': json.dumps(status_counts),
        'case_type_labels_json': json.dumps(case_type_labels),
        'case_type_counts_json': json.dumps(case_type_counts),
        'monthly_labels_json': json.dumps(monthly_labels),
        'monthly_counts_json': json.dumps(monthly_counts),
        'anonymous_counts_json': json.dumps([anonymous_reports, named_reports]),
        'selected_status': selected_status,
        'selected_case_type': selected_case_type,
        'filter_start': filter_start,
        'filter_end': filter_end,
        'statuses': status_labels,
        'case_types': case_type_labels,
        'notifications': notifications,
        'unread_notifications_count': unread_notifications_count,
    }
    return render(request, "analytics.html", context)


@staff_member_required
def admin_report_detail(request, report_id):
    report = get_object_or_404(Report, reference_number=report_id)

    if request.method == 'POST':
        selected_status = request.POST.get('status')
        admin_response = request.POST.get('admin_response', '').strip()

        if selected_status in dict(Report.STATUS_CHOICES):
            report.status = selected_status

        report.admin_response = admin_response
        report.save()

        # Create notification
        if report.reporter:
            Notification.objects.create(
                user=report.reporter,
                report=report,
                message=f"Your report {report.reference_number} status was updated to {report.status}",
                notification_type=Notification.NOTIFICATION_REPORT,
            )

        # Send email to reporter
        if report.reporter and report.reporter.email:
            try:
                send_mail(
                    subject=f"GBV Report Update - {report.reference_number}",
                    message=f"""
Hello {report.reporter.get_full_name() or report.reporter.username},

Your GBV report has been updated.

Reference Number:
{report.reference_number}

Status:
{report.status}

Admin Response:
{report.admin_response}

Thank you for using the GBV Support System.
                    """,
                    from_email=None,
                    recipient_list=[report.reporter.email],
                    fail_silently=False,
                )
            except Exception as e:
                print("Email Error:", e)

        # Update Firebase
        docs = db.collection("reports").where(
            "reference_number", "==", report.reference_number
        ).stream()

        for doc in docs:
            doc.reference.update({
                "status": report.status,
                "admin_response": report.admin_response,
                "updated_at": str(report.updated_at)
            })

        messages.success(request, "Report updated successfully.")
        return redirect("admin_report_detail", report_id=report.reference_number)

    return render(request, "report_detail.html", {"report": report})

@staff_member_required
def admin_notifications_view(request):
    notification_qs = Notification.objects.filter(user=request.user).order_by('-created_at')
    notifications = notification_qs
    unread_notifications_count = notification_qs.filter(is_read=False).count()

    context = {
        'notifications': notifications,
        'unread_notifications_count': unread_notifications_count,
    }
    return render(request, "admin_notifications.html", context)


def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect("login")


def chatbot_view(request):
    return render(request, "chatbot.html")


def report_anonymous_view(request):

    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        description = request.POST.get("description", "").strip()

        if not description:
            messages.error(request, "Please provide a description for the anonymous report.")
            return render(request, "report_anonymous.html")

        report = Report.objects.create(
            title=title or "(No title)",
            description=description,
            is_anonymous=True,
            status=Report.STATUS_SUBMITTED,
            email="",
        )
        for staff_user in User.objects.filter(is_staff=True, is_active=True):
            Notification.objects.create(
                user=staff_user,
                report=report,
                message=f"Anonymous report submitted: {report.reference_number}",
                notification_type=Notification.NOTIFICATION_REPORT,
            )

        try:
            db.collection("reports").add({
                "reference_number": report.reference_number,
                "reporter": "Anonymous",
                "email": "",
                "title": report.title,
                "description": report.description,
                "status": report.status,
                "created_at": str(report.created_at),
                "is_anonymous": True
            })
            print("Anonymous report saved to Firebase!")
        except Exception as e:
            print("Firebase Error:", e)

        messages.success(request, "Your anonymous report has been submitted. Thank you.")
        return redirect("login")

    return render(request, "report_anonymous.html")

def gbv_report_demo_view(request):
    """Demo page that shows the GBV report form with validation errors by binding invalid data."""
    # Intentionally invalid / blank values to demonstrate validation messages
    invalid_data = {
        'full_name': '',
        'email': 'invalid-email',
        'contact_number': '12',
        'title': '',
        'description': 'Too short',
        'date_of_incident': '2099-01-01',
        'location': '',
        'type_of_violence': '',
        'password': '123',
        'confirm_password': '456',
        # 'terms' omitted to trigger required error
    }

    form = GBVReportForm(data=invalid_data)
    # Force validation to populate errors
    form.is_valid()

    return render(request, 'gbv_report_form.html', {'form': form})

def verify_email(request, token):
    try:
        profile = UserProfile.objects.get(verification_token=token)

        if not profile.email_verified:
            profile.email_verified = True
            profile.save()

        messages.success(request, "Email verified successfully. You can now log in.")
        return redirect("login")

    except UserProfile.DoesNotExist:
        return HttpResponse("""
            <h2>❌ Invalid Verification Link</h2>
        """)