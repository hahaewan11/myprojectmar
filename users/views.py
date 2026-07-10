from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from firebase_config import db
from django.core.mail import send_mail
from django.contrib.auth.models import User
from security.forms import ReportForm
from security.models import Report, Notification


@login_required(login_url='login')
def report_detail_user(request, report_id):
    report = get_object_or_404(Report, id=report_id, reporter=request.user)
    return render(request, "report_detail_user.html", {"report": report})


@login_required(login_url='login')
def user_profile_view(request):
    user = request.user
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

            Notification.objects.create(
                user=user,
                report=report,
                message=f"New report submitted: {report.reference_number}",
                notification_type=Notification.NOTIFICATION_REPORT,
            )

            for staff_user in User.objects.filter(is_staff=True, is_active=True):
                Notification.objects.create(
                    user=staff_user,
                    report=report,
                    message=f"New report submitted by {user.get_full_name() or user.username}: {report.reference_number}",
                    notification_type=Notification.NOTIFICATION_REPORT,
                )

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
        except Exception as e:
            print("Firebase Error:", e)

        messages.success(request, "Your anonymous report has been submitted. Thank you.")
        return redirect("login")

    return render(request, "report_anonymous.html")
