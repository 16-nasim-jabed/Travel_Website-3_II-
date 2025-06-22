# users/helpers.py

import secrets
from datetime import timedelta
import re

from django.utils import timezone
from django.shortcuts import redirect
from functools import wraps

from .models import User, Session, LoginLog

SESSION_DURATION_MINUTES = 60
PERSISTENT_SESSION_DURATION_DAYS = 7


# ─────────────────────────────────────────────────────────────
#  Sessions
# ─────────────────────────────────────────────────────────────
def create_session(user_id: int, persistent: bool = False) -> str:
    """
    Create a new Session row and return its token.
    """
    token = secrets.token_urlsafe(32)
    expires_at = (
        timezone.now() + timedelta(days=PERSISTENT_SESSION_DURATION_DAYS)
        if persistent
        else timezone.now() + timedelta(minutes=SESSION_DURATION_MINUTES)
    )
    Session.objects.create(
        user_id=user_id,
        session_token=token,
        expires_at=expires_at,
        is_persistent=persistent,
    )
    return token


def get_authenticated_user(request):
    """
    Return a dict of user info if a valid session_token cookie is present,
    otherwise return None.
    """
    token = request.COOKIES.get("session_token")
    if not token:
        return None

    try:
        sess = Session.objects.select_related("user").get(session_token=token)
    except Session.DoesNotExist:
        return None

    # Expiration check
    if timezone.now() > sess.expires_at:
        sess.delete()
        return None

    user = sess.user
    return {
        "id":             user.id,
        "username":       user.username,
        "email":          user.email,
        "is_admin":       user.is_admin,
        "is_persistent":  sess.is_persistent,
    }


# ─────────────────────────────────────────────────────────────
#  Password validation helper
# ─────────────────────────────────────────────────────────────
def is_valid_password(password: str):
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r"[A-Za-z]", password):
        return False, "Password must contain at least one letter."
    if not re.search(r"\d", password):
        return False, "Password must contain at least one digit."
    return True, ""


# ─────────────────────────────────────────────────────────────
#  Login / logout event log
# ─────────────────────────────────────────────────────────────
def log_auth_event(user_id: int, event_type: str, ip_address: str = None):
    """
    Record a login or logout event.
    """
    LoginLog.objects.create(
        user_id=user_id,
        event_type=event_type,
        ip_address=ip_address,
    )


# ─────────────────────────────────────────────────────────────
#  Admin-required decorator
# ─────────────────────────────────────────────────────────────
def admin_required(view_func):
    """
    Decorator to allow access only to admin users.
    """
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        user = get_authenticated_user(request)
        if not user or not user.get("is_admin"):
            return redirect("login")
        return view_func(request, *args, **kwargs)

    return _wrapped
