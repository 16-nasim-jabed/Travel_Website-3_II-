# users/views.py
from datetime import timedelta
import secrets
import bcrypt

from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect, Http404
from django.core.mail import send_mail
from django.utils import timezone
from django.db import IntegrityError
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect
from destinations.models import Destination        # ← import your model


from .models import User

from .helpers import (
    get_authenticated_user,
    create_session,
    SESSION_DURATION_MINUTES,
    PERSISTENT_SESSION_DURATION_DAYS,
    is_valid_password,
    log_auth_event,
)

# ─────────────────────────────────────────────────────────────
#  Registration
# ─────────────────────────────────────────────────────────────
def register_view(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        confirm = request.POST.get("confirm_password", "")

        # Basic validation
        if not all([username, email, password, confirm]):
            return render(request, "register.html", {"error": "All fields are required"})
        if password != confirm:
            return render(request, "register.html", {"error": "Passwords do not match"})

        valid, msg = is_valid_password(password)
        if not valid:
            return render(request, "register.html", {"error": msg})

        email_token = secrets.token_urlsafe(24)
        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

        try:
            User.objects.create(
                username=username,
                email=email,
                password_hash=password_hash,
                email_verification_token=email_token,
                password_changed_at=timezone.now(),
            )
        except IntegrityError:
            return render(
                request,
                "register.html",
                {"error": "Username or email already taken"},
            )

        verification_link = f"http://{request.get_host()}/verify-email?token={email_token}"
        send_mail(
            subject="Please verify your email address",
            message=f"Hi {username},\n\nVerify here:\n{verification_link}",
            from_email=None,
            recipient_list=[email],
            fail_silently=False,
        )
        return render(
            request,
            "register.html",
            {"success": "✅ User registered! Check your email to verify."},
        )

    return render(request, "register.html")


# ─────────────────────────────────────────────────────────────
#  Email Verification
# ─────────────────────────────────────────────────────────────
def verify_email_view(request):
    token = request.GET.get("token")
    if not token:
        return render(request, "verify_email.html", {"error": "Missing token."})

    try:
        user = User.objects.get(email_verification_token=token)
    except User.DoesNotExist:
        return render(request, "verify_email.html", {"error": "Invalid token."})

    if user.email_verified:
        return render(
            request, "verify_email.html", {"message": "Email already verified."}
        )

    user.email_verified = True
    user.email_verification_token = None
    user.save(update_fields=["email_verified", "email_verification_token"])

    return render(
        request,
        "verify_email.html",
        {"message": "Your email has been verified successfully!"},
    )


# ─────────────────────────────────────────────────────────────
#  Login + Logout
# ─────────────────────────────────────────────────────────────
def login_view(request):
    if get_authenticated_user(request):
        return redirect("/home/")

    if request.method == "POST":
        identifier = request.POST.get("identifier", "").strip()
        password = request.POST.get("password", "")
        remember_me = request.POST.get("remember_me") == "on"

        if not identifier or not password:
            return render(request, "login.html", {"error": "All fields are required"})

        try:
            user = User.objects.get(username=identifier)
        except User.DoesNotExist:
            try:
                user = User.objects.get(email=identifier)
            except User.DoesNotExist:
                return render(request, "login.html", {"error": "User not found"})

        if not bcrypt.checkpw(password.encode(), user.password_hash.encode()):
            return render(request, "login.html", {"error": "Incorrect password"})

        token = create_session(user.id, persistent=remember_me)
        log_auth_event(user.id, "login", request.META.get("REMOTE_ADDR", "unknown"))

        max_age = (
            PERSISTENT_SESSION_DURATION_DAYS * 24 * 60 * 60
            if remember_me
            else SESSION_DURATION_MINUTES * 60
        )
        resp = redirect("/home/")
        resp.set_cookie(
            "session_token",
            token,
            httponly=True,
            secure=True,
            samesite="Lax",
            max_age=max_age,
        )
        return resp

    return render(request, "login.html")


def logout_view(request):
    token = request.COOKIES.get("session_token")
    resp = HttpResponseRedirect("/login/")

    user = get_authenticated_user(request)
    if user:
        log_auth_event(user["id"], "logout", request.META.get("REMOTE_ADDR", "unknown"))

    if token:
        from .models import Session

        Session.objects.filter(session_token=token).delete()
        resp.delete_cookie("session_token")

    return resp


# ─────────────────────────────────────────────────────────────
#  Home (requires auth)
# ─────────────────────────────────────────────────────────────

def home_view(request):
    user = get_authenticated_user(request)
    if not user:
        return redirect("/login/")

    # fetch all regions
    destinations = Destination.objects.all()

    return render(request, "home.html", {
        "user": user,
        "destinations": destinations,           # ← pass into context
    })

# ─────────────────────────────────────────────────────────────
#  Forgot Password
# ─────────────────────────────────────────────────────────────
def forgot_password_view(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        if not email:
            return render(request, "forgot_password.html", {"error": "Email is required."})

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return render(
                request, "forgot_password.html", {"error": "No account with that email."}
            )

        if not user.email_verified:
            return render(
                request,
                "forgot_password.html",
                {"error": "Please verify your email first."},
            )

        reset_token = secrets.token_urlsafe(32)
        expiry_time = timezone.now() + timedelta(minutes=30)

        user.reset_token = reset_token
        user.reset_token_expiry = expiry_time
        user.save(update_fields=["reset_token", "reset_token_expiry"])

        reset_link = f"http://{request.get_host()}/reset-password?token={reset_token}"
        send_mail(
            "Password Reset - TravelSite",
            f"Hi {user.username},\n\nReset here (30 min):\n{reset_link}",
            None,
            [email],
        )

        return render(
            request,
            "forgot_password.html",
            {"success": "📩 Reset link sent to your email."},
        )

    return render(request, "forgot_password.html")


# ─────────────────────────────────────────────────────────────
#  Reset Password
# ─────────────────────────────────────────────────────────────
def reset_password_view(request):
    token = request.GET.get("token") or request.POST.get("token")
    if not token:
        return render(request, "reset_password.html", {"error": "Missing reset token."})

    try:
        user = User.objects.get(reset_token=token)
    except User.DoesNotExist:
        return render(request, "reset_password.html", {"error": "Invalid or expired token."})

    if timezone.now() > user.reset_token_expiry:
        return render(
            request,
            "reset_password.html",
            {"error": "Token has expired. Please request a new one."},
        )

    if request.method == "POST":
        password = request.POST.get("password", "")
        confirm = request.POST.get("confirm_password", "")
        if password != confirm:
            return render(
                request,
                "reset_password.html",
                {"error": "Passwords do not match.", "token": token},
            )

        valid, msg = is_valid_password(password)
        if not valid:
            return render(
                request,
                "reset_password.html",
                {"error": msg, "token": token},
            )

        pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        user.password_hash = pw_hash
        user.password_changed_at = timezone.now()
        user.reset_token = None
        user.reset_token_expiry = None
        user.save(
            update_fields=[
                "password_hash",
                "password_changed_at",
                "reset_token",
                "reset_token_expiry",
            ]
        )

        return render(
            request,
            "reset_password.html",
            {"success": "✅ Your password has been reset successfully."},
        )

    # GET request—show form
    return render(request, "reset_password.html", {"token": token})


# ─────────────────────────────────────────────────────────────
#  Resend Verification
# ─────────────────────────────────────────────────────────────
@csrf_exempt
def resend_verification_view(request):
    context = {}
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        if not email:
            context["error"] = "Please enter your email."
        else:
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                context["error"] = "No account found with that email."
            else:
                if user.email_verified:
                    context["message"] = "Your email is already verified."
                else:
                    new_token = secrets.token_urlsafe(24)
                    user.email_verification_token = new_token
                    user.save(update_fields=["email_verification_token"])

                    link = f"http://{request.get_host()}/verify-email?token={new_token}"
                    send_mail(
                        "Your verification link",
                        f"Hi {user.username},\n\nClick to verify:\n{link}",
                        None,
                        [email],
                    )
                    context["message"] = "✅ Verification email resent—check your inbox."

    return render(request, "resend_verification.html", context)
