from django.db import models
from django.contrib.auth.models import User
import uuid


class Report(models.Model):
    STATUS_SUBMITTED = 'Submitted'
    STATUS_UNDER_REVIEW = 'Under Review'
    STATUS_IN_PROGRESS = 'In Progress'
    STATUS_RESOLVED = 'Resolved'

    STATUS_CHOICES = [
        (STATUS_SUBMITTED, 'Submitted'),
        (STATUS_UNDER_REVIEW, 'Under Review'),
        (STATUS_IN_PROGRESS, 'In Progress'),
        (STATUS_RESOLVED, 'Resolved'),
    ]

    CASE_TYPE_CHOICES = [
        ('Physical', 'Physical'),
        ('Emotional', 'Emotional'),
        ('Sexual', 'Sexual'),
        ('Economic', 'Economic'),
        ('Harassment', 'Harassment'),
    ]

    reporter = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='reports'
    )
    reference_number = models.CharField(max_length=50, unique=True, blank=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    case_type = models.CharField(max_length=50, choices=CASE_TYPE_CHOICES, blank=True)
    location = models.CharField(max_length=200, blank=True)
    date_of_incident = models.DateField(null=True, blank=True)
    time_of_incident = models.TimeField(null=True, blank=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default=STATUS_SUBMITTED)
    is_anonymous = models.BooleanField(default=False)
    email = models.EmailField(blank=True)
    admin_response = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.reference_number:
            self.reference_number = f"GBV-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    @property
    def reporter_name(self):
        if self.is_anonymous or not self.reporter:
            return 'Anonymous'
        return self.reporter.get_full_name() or self.reporter.username

    @property
    def status_class(self):
        return {
            self.STATUS_SUBMITTED: 'status-submitted',
            self.STATUS_UNDER_REVIEW: 'status-review',
            self.STATUS_IN_PROGRESS: 'status-progress',
            self.STATUS_RESOLVED: 'status-resolved',
        }.get(self.status, 'status-submitted')

    def __str__(self):
        return self.reference_number or self.title


class Notification(models.Model):
    NOTIFICATION_REPORT = 'report'
    NOTIFICATION_ANNOUNCEMENT = 'announcement'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    report = models.ForeignKey(Report, null=True, blank=True, on_delete=models.CASCADE, related_name='notifications')
    message = models.CharField(max_length=255)
    notification_type = models.CharField(max_length=32, choices=[(NOTIFICATION_REPORT, 'Report'), (NOTIFICATION_ANNOUNCEMENT, 'Announcement')], default=NOTIFICATION_ANNOUNCEMENT)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.message

    @property
    def url(self):
        if self.report:
            return f"{self.report.id}"
        return '#'
    
    
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    email_verified = models.BooleanField(default=False)
    verification_token = models.UUIDField(default=uuid.uuid4, unique=True)

    def __str__(self):
        return self.user.username