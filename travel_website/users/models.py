# users/models.py
from django.db import models
from django.utils import timezone


class User(models.Model):
    """
    Custom user table (simplified) – we’ll keep the hashed password
    instead of using Django’s authentication framework.
    """
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    password_hash = models.CharField(max_length=128)

    # flags & timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    password_changed_at = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)

    # email verification + reset
    email_verification_token = models.TextField(null=True, blank=True)
    email_verified = models.BooleanField(default=False)
    reset_token = models.TextField(null=True, blank=True)
    reset_token_expiry = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.username


class Session(models.Model):
    """
    Manual session store.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sessions")
    session_token = models.TextField(unique=True)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_persistent = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} | {self.session_token[:12]}…"


class LoginLog(models.Model):
    """
    Tracks login/logout events for auditing.
    """
    LOGIN = "login"
    LOGOUT = "logout"
    EVENT_CHOICES = [(LOGIN, "Login"), (LOGOUT, "Logout")]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="login_logs")
    event_type = models.CharField(max_length=6, choices=EVENT_CHOICES)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} | {self.event_type} | {self.timestamp:%Y-%m-%d %H:%M}"
