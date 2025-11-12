# Password Reset Flow

Custom password reset templates have been created matching the Chicago Garden Planner design.

## Flow Overview

1. **Request Reset** (`/accounts/password/reset/`)
   - User enters their email address
   - Green card with "Reset Password" header
   - Bootstrap Icons: `bi-key`
   - Link back to login page

2. **Confirmation** (`/accounts/password/reset/done/`)
   - Success message that email was sent
   - Large envelope icon (`bi-envelope-check`)
   - Alert about checking spam folder
   - Link back to login

3. **Set New Password** (`/accounts/password/reset/<uidb64>/<token>/`)
   - Form to enter new password twice
   - Password requirements displayed
   - Handles invalid/expired links gracefully
   - Bootstrap Icons: `bi-shield-lock`

4. **Complete** (`/accounts/password/reset/complete/`)
   - Success confirmation
   - Large checkmark icon (`bi-check-circle-fill`)
   - Security tip reminder
   - Links to login and home page

## Email Template

Plain text email (`password_reset_email.html`) includes:
- Personalized greeting with username
- Clear reset link
- 24-hour expiration notice
- Instructions for ignoring if not requested
- Branded footer

## Design Consistency

All templates match the existing site style:
- Bootstrap 5 with green theme (`bg-success`)
- Card-based layout with shadows
- Centered single-column design (col-md-6 col-lg-5)
- Bootstrap Icons throughout
- Crispy Forms for form rendering
- Responsive and mobile-friendly

## URLs

The password reset URLs are already configured in `accounts/urls.py`:
- `accounts:password_reset` - Request form
- `accounts:password_reset_done` - Email sent confirmation
- `accounts:password_reset_confirm` - Set new password
- `accounts:password_reset_complete` - Success page

## Testing

In development, emails are sent to the console (see `settings.py` EMAIL_BACKEND).

For production, configure your email backend in `settings_production.py`:
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.example.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@example.com'
EMAIL_HOST_PASSWORD = 'your-password'
DEFAULT_FROM_EMAIL = 'Chicago Garden Planner <noreply@yourdomain.com>'
```

## Access

Users can access password reset from:
- Login page "Forgot your password?" link
- Direct URL: `/accounts/password/reset/`
