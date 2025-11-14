# Email Configuration

This document explains how to configure email for password reset and other email features.

## Development Mode (Default)

By default, emails are **printed to the console** where you run `python manage.py runserver`. This is perfect for development and testing.

**To see password reset emails:**
1. Run the dev server: `python manage.py runserver`
2. Request a password reset
3. Check your terminal - the email will be printed there!

Example console output:
```
Content-Type: text/plain; charset="utf-8"
MIME-Version: 1.0
Content-Transfer-Encoding: 7bit
Subject: Password reset on Chicago Garden Planner
From: noreply@chicagogarden.com
To: user@example.com
Date: Mon, 12 Nov 2025 10:30:00 -0000
Message-ID: <...>

Hello demo_gardener,

You're receiving this email because you requested a password reset...
[Full email content here]
```

## Sending Real Emails (Development)

If you want to send actual emails during development for testing, you can configure SMTP.

### Option 1: Gmail (Easiest)

1. **Enable 2-Factor Authentication** on your Google account
   - Go to: https://myaccount.google.com/security

2. **Generate an App Password**
   - Go to: https://myaccount.google.com/apppasswords
   - App: "Mail"
   - Device: "Other" → "Django Dev"
   - Copy the 16-character password

3. **Create/Update your `.env` file:**
   ```bash
   # Add these lines to your .env file (NOT .env.example)
   EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
   EMAIL_HOST=smtp.gmail.com
   EMAIL_PORT=587
   EMAIL_USE_TLS=True
   EMAIL_HOST_USER=your-email@gmail.com
   EMAIL_HOST_PASSWORD=your-16-character-app-password
   DEFAULT_FROM_EMAIL=Chicago Garden Planner <your-email@gmail.com>
   ```

4. **Restart the dev server**

**Important:** Never commit your `.env` file with real credentials! The `.env` file is in `.gitignore`.

### Option 2: Other Email Providers

**SendGrid:**
```bash
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=your-sendgrid-api-key
```

**Mailgun:**
```bash
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.mailgun.org
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=postmaster@your-domain.mailgun.org
EMAIL_HOST_PASSWORD=your-mailgun-smtp-password
```

**AWS SES:**
```bash
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=email-smtp.us-east-1.amazonaws.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-ses-smtp-username
EMAIL_HOST_PASSWORD=your-ses-smtp-password
```

### Option 3: File Backend (Save to Files)

Useful if you want to see emails without sending them:

```bash
EMAIL_BACKEND=django.core.mail.backends.filebased.EmailBackend
# Emails will be saved to tmp/emails/
```

Then check `tmp/emails/` for saved email files.

## Production Configuration

For production (via Docker/environment variables), configure these in your `.env` file on the server:

```bash
# Production email via SMTP
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.your-provider.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=noreply@yourdomain.com
EMAIL_HOST_PASSWORD=your-secure-password
DEFAULT_FROM_EMAIL=Chicago Garden Planner <noreply@yourdomain.com>
```

**Best Practices for Production:**
- Use a dedicated email service (SendGrid, Mailgun, AWS SES)
- Use environment-specific credentials
- Set up SPF and DKIM records for your domain
- Monitor email sending quotas and bounce rates

## Testing Email Configuration

To test if your email configuration works:

```bash
python manage.py shell
```

Then run:
```python
from django.core.mail import send_mail

send_mail(
    'Test Email',
    'This is a test email from Chicago Garden Planner.',
    'noreply@chicagogarden.com',
    ['your-email@example.com'],
    fail_silently=False,
)
```

**Console Backend:** Email will print to terminal
**SMTP Backend:** Email will be sent to your inbox
**File Backend:** Check `tmp/emails/` for the file

## Troubleshooting

### "Connection refused" error
- Check EMAIL_HOST and EMAIL_PORT are correct
- Ensure your firewall allows outbound connections on port 587/465

### Gmail "Username and Password not accepted"
- Make sure you're using an App Password, not your regular password
- Verify 2-factor authentication is enabled
- Try re-generating a new App Password

### Emails not appearing in inbox
- Check spam/junk folder
- Verify EMAIL_HOST_USER and DEFAULT_FROM_EMAIL are valid
- Check email service logs/dashboard for delivery status

### "SMTPAuthenticationError"
- Double-check EMAIL_HOST_USER and EMAIL_HOST_PASSWORD
- Ensure EMAIL_USE_TLS is set correctly
- Some providers require EMAIL_USE_SSL instead

## Email Templates

Password reset emails use these templates:
- `accounts/templates/registration/password_reset_email.html` - The email content
- `accounts/templates/registration/password_reset_subject.txt` - Email subject (optional)

To customize the email:
1. Edit `password_reset_email.html`
2. Available context variables:
   - `{{ user.username }}` - Username
   - `{{ protocol }}` - http or https
   - `{{ domain }}` - Your domain
   - `{{ uid }}` - User ID (base64)
   - `{{ token }}` - Reset token

## Related Documentation

- Django Email Documentation: https://docs.djangoproject.com/en/4.2/topics/email/
- Gmail App Passwords: https://support.google.com/accounts/answer/185833
- SendGrid Django Guide: https://docs.sendgrid.com/for-developers/sending-email/django
