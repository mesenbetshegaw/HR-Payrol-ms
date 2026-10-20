"""
Professional email notification service with HTML templates.
Sends real emails via Gmail SMTP when configured, falls back to console.
"""
from __future__ import annotations
import logging
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)

# ── HTML email template ───────────────────────────────────────────────────────

def _wrap_html(title: str, body: str, color: str = "#2563eb") -> str:
    """Wrap email body in a professional HTML template."""
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
</head>
<body style="margin:0;padding:0;background:#f3f4f6;font-family:'Segoe UI',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f3f4f6;padding:32px 0;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0" style="background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.08);">
        <!-- Header -->
        <tr><td style="background:{color};padding:28px 40px;">
          <h1 style="margin:0;color:#fff;font-size:22px;font-weight:700;">HR &amp; Payroll System</h1>
          <p style="margin:4px 0 0;color:rgba(255,255,255,0.85);font-size:13px;">Ethiopian Human Resource Management</p>
        </td></tr>
        <!-- Body -->
        <tr><td style="padding:36px 40px;">
          {body}
        </td></tr>
        <!-- Footer -->
        <tr><td style="background:#f9fafb;padding:20px 40px;border-top:1px solid #e5e7eb;">
          <p style="margin:0;color:#9ca3af;font-size:12px;text-align:center;">
            This email was sent by the HR &amp; Payroll Management System.<br>
            Please do not reply to this email.
          </p>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""


def _send(to: str | list[str], subject: str, html_body: str) -> bool:
    """Send an HTML email. Returns True on success."""
    if not to:
        return False
    recipients = [to] if isinstance(to, str) else to
    recipients = [r for r in recipients if r and "@" in r]
    if not recipients:
        return False
    try:
        text_body = strip_tags(html_body)
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=recipients,
        )
        msg.attach_alternative(html_body, "text/html")
        msg.send(fail_silently=False)
        logger.info("Email sent to %s: %s", recipients, subject)
        return True
    except Exception as e:
        logger.error("Failed to send email to %s: %s", recipients, e)
        return False


# ── Public email functions ────────────────────────────────────────────────────

def send_registration_submitted(email: str, first_name: str, request_id: int) -> bool:
    """Notify applicant that their registration was received."""
    body = f"""
    <h2 style="color:#1f2937;margin:0 0 16px;">Hello, {first_name}! 👋</h2>
    <p style="color:#4b5563;line-height:1.7;margin:0 0 16px;">
      Thank you for submitting your registration request to the 
      <strong>HR &amp; Payroll Management System</strong>.
    </p>
    <div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:8px;padding:16px 20px;margin:0 0 20px;">
      <p style="margin:0;color:#1d4ed8;font-weight:600;">📋 Request ID: #{request_id}</p>
    </div>
    <p style="color:#4b5563;line-height:1.7;margin:0 0 16px;">
      An administrator will review your request and you will receive an email 
      notification once a decision has been made.
    </p>
    <p style="color:#4b5563;margin:0;">
      <strong>What happens next:</strong><br>
      ✅ An Admin or HR Officer reviews your information<br>
      ✅ You receive an approval or rejection email<br>
      ✅ Upon approval, you can log in immediately
    </p>
    """
    html = _wrap_html("Registration Received", body)
    return _send(email, "Registration Request Received — HR Payroll System", html)


def send_registration_approved(email: str, first_name: str, role: str) -> bool:
    """Notify applicant that their registration was approved."""
    body = f"""
    <h2 style="color:#1f2937;margin:0 0 16px;">Congratulations, {first_name}! 🎉</h2>
    <div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:8px;padding:16px 20px;margin:0 0 20px;">
      <p style="margin:0;color:#15803d;font-size:16px;font-weight:700;">✅ Your registration has been approved!</p>
    </div>
    <p style="color:#4b5563;line-height:1.7;margin:0 0 16px;">
      Your account has been created with the role of <strong>{role.replace('_',' ').title()}</strong>.
    </p>
    <div style="background:#f9fafb;border-radius:8px;padding:16px 20px;margin:0 0 20px;">
      <p style="margin:0 0 8px;color:#6b7280;font-size:13px;">Your login credentials:</p>
      <p style="margin:0;color:#1f2937;"><strong>Email:</strong> {email}</p>
      <p style="margin:4px 0 0;color:#1f2937;"><strong>Password:</strong> The password you set during registration</p>
    </div>
    <p style="color:#4b5563;line-height:1.7;margin:0 0 20px;">
      ⚠️ You will be prompted to change your password on first login for security.
    </p>
    <div style="text-align:center;margin:24px 0;">
      <a href="http://localhost:5173/login" 
         style="background:#2563eb;color:#fff;padding:12px 32px;border-radius:8px;text-decoration:none;font-weight:600;display:inline-block;">
        Login to the System →
      </a>
    </div>
    """
    html = _wrap_html("Registration Approved", body, "#16a34a")
    return _send(email, "✅ Your Registration is Approved — HR Payroll System", html)


def send_registration_rejected(email: str, first_name: str, reason: str) -> bool:
    """Notify applicant that their registration was rejected."""
    body = f"""
    <h2 style="color:#1f2937;margin:0 0 16px;">Hello, {first_name}</h2>
    <div style="background:#fef2f2;border:1px solid #fecaca;border-radius:8px;padding:16px 20px;margin:0 0 20px;">
      <p style="margin:0;color:#b91c1c;font-weight:600;">❌ Your registration request has not been approved.</p>
    </div>
    <div style="background:#f9fafb;border-radius:8px;padding:16px 20px;margin:0 0 20px;">
      <p style="margin:0 0 6px;color:#6b7280;font-size:13px;">Reason:</p>
      <p style="margin:0;color:#1f2937;">{reason}</p>
    </div>
    <p style="color:#4b5563;line-height:1.7;margin:0;">
      If you believe this is an error or would like to re-apply, please contact 
      the HR department directly.
    </p>
    """
    html = _wrap_html("Registration Update", body, "#dc2626")
    return _send(email, "Registration Request Update — HR Payroll System", html)


def send_password_reset(email: str, first_name: str, reset_url: str) -> bool:
    """Send password reset email."""
    body = f"""
    <h2 style="color:#1f2937;margin:0 0 16px;">Password Reset Request</h2>
    <p style="color:#4b5563;line-height:1.7;margin:0 0 16px;">
      Hello {first_name}, we received a request to reset your password.
    </p>
    <div style="text-align:center;margin:24px 0;">
      <a href="{reset_url}" 
         style="background:#2563eb;color:#fff;padding:12px 32px;border-radius:8px;text-decoration:none;font-weight:600;display:inline-block;">
        Reset My Password →
      </a>
    </div>
    <p style="color:#9ca3af;font-size:13px;margin:0;">
      This link expires in 2 hours. If you did not request this, ignore this email.
    </p>
    """
    html = _wrap_html("Password Reset", body)
    return _send(email, "Password Reset Request — HR Payroll System", html)


def send_payslip_ready(email: str, first_name: str, period: str, net_pay: float) -> bool:
    """Notify employee that their payslip is ready."""
    body = f"""
    <h2 style="color:#1f2937;margin:0 0 16px;">Your Payslip is Ready 💰</h2>
    <p style="color:#4b5563;line-height:1.7;margin:0 0 16px;">
      Hello {first_name}, your payslip for <strong>{period}</strong> is now available.
    </p>
    <div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:8px;padding:16px 20px;margin:0 0 20px;text-align:center;">
      <p style="margin:0;color:#6b7280;font-size:13px;">Net Pay</p>
      <p style="margin:4px 0 0;color:#15803d;font-size:28px;font-weight:700;">ETB {net_pay:,.2f}</p>
    </div>
    <div style="text-align:center;margin:24px 0;">
      <a href="http://localhost:5173/my-payslips" 
         style="background:#2563eb;color:#fff;padding:12px 32px;border-radius:8px;text-decoration:none;font-weight:600;display:inline-block;">
        View &amp; Download Payslip →
      </a>
    </div>
    """
    html = _wrap_html("Payslip Ready", body, "#16a34a")
    return _send(email, f"Payslip Ready for {period} — HR Payroll System", html)


def notify_admins_new_registration(admin_emails: list[str], applicant_name: str,
                                    applicant_email: str, role: str, request_id: int) -> bool:
    """Notify all admins of a new registration request."""
    body = f"""
    <h2 style="color:#1f2937;margin:0 0 16px;">New Registration Request 📋</h2>
    <p style="color:#4b5563;line-height:1.7;margin:0 0 16px;">
      A new registration request requires your review.
    </p>
    <div style="background:#f9fafb;border-radius:8px;padding:16px 20px;margin:0 0 20px;">
      <table style="width:100%;border-collapse:collapse;">
        <tr><td style="padding:6px 0;color:#6b7280;font-size:13px;width:120px;">Name:</td>
            <td style="padding:6px 0;color:#1f2937;font-weight:600;">{applicant_name}</td></tr>
        <tr><td style="padding:6px 0;color:#6b7280;font-size:13px;">Email:</td>
            <td style="padding:6px 0;color:#1f2937;">{applicant_email}</td></tr>
        <tr><td style="padding:6px 0;color:#6b7280;font-size:13px;">Requested Role:</td>
            <td style="padding:6px 0;color:#1f2937;">{role.replace('_',' ').title()}</td></tr>
        <tr><td style="padding:6px 0;color:#6b7280;font-size:13px;">Request ID:</td>
            <td style="padding:6px 0;color:#1f2937;">#{request_id}</td></tr>
      </table>
    </div>
    <div style="text-align:center;margin:24px 0;">
      <a href="http://localhost:5173/registrations" 
         style="background:#2563eb;color:#fff;padding:12px 32px;border-radius:8px;text-decoration:none;font-weight:600;display:inline-block;">
        Review Request →
      </a>
    </div>
    """
    html = _wrap_html("New Registration", body)
    return _send(admin_emails, f"New Registration Request from {applicant_name} — HR Payroll System", html)
