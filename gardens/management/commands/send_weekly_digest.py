"""
Management command to send weekly garden digest emails to users.

This command should be run once per week (e.g., via cron job on Sunday mornings).
It sends a comprehensive weekly summary of all upcoming garden tasks.

Usage:
    python manage.py send_weekly_digest
    python manage.py send_weekly_digest --dry-run
    python manage.py send_weekly_digest --user=username
    python manage.py send_weekly_digest --preview
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from datetime import datetime, date
import zoneinfo

from gardens.notifications import calculate_all_notifications

User = get_user_model()


class Command(BaseCommand):
    help = 'Send weekly garden digest emails to users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be sent without actually sending emails',
        )
        parser.add_argument(
            '--user',
            type=str,
            help='Send to specific user only (username)',
        )
        parser.add_argument(
            '--preview',
            action='store_true',
            help='Print email content to console for preview',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        specific_user = options['user']
        preview = options['preview']

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No emails will be sent\n'))

        if preview:
            self.stdout.write(self.style.WARNING('PREVIEW MODE - Emails will be printed to console\n'))

        # Get users who have weekly tips enabled
        if specific_user:
            users = User.objects.filter(username=specific_user, is_active=True)
            if not users.exists():
                self.stdout.write(self.style.ERROR(f'User "{specific_user}" not found'))
                return
        else:
            users = User.objects.filter(
                is_active=True,
                profile__weekly_tips=True
            ).select_related('profile')

        total_users = users.count()
        self.stdout.write(f'Found {total_users} user(s) with weekly digest enabled\n')

        emails_sent = 0
        emails_skipped = 0

        for user in users:
            # Get user's timezone
            try:
                user_tz = zoneinfo.ZoneInfo(user.profile.notification_timezone)
            except:
                user_tz = zoneinfo.ZoneInfo('America/Chicago')  # Default fallback

            # Get current time in user's timezone
            user_now = timezone.now().astimezone(user_tz)

            # Calculate all notifications for this user
            notifications = calculate_all_notifications(user)

            # For weekly digest, we always send (even if no tasks) to provide weekly tips
            # Skip only if user has no gardens at all
            if not user.gardens.exists() and not preview and not specific_user:
                emails_skipped += 1
                self.stdout.write(
                    self.style.WARNING(f'  ⊘ Skipped {user.username} (no gardens)')
                )
                continue

            # Prepare email context
            context = {
                'user': user,
                'notification_date': date.today(),
                'gardens': notifications['gardens'],
                'total_overdue': notifications['total_overdue'],
                'total_due_today': notifications['total_due_today'],
                'total_coming_up': notifications['total_coming_up'],
                'has_notifications': notifications['has_notifications'],
                'site_url': f"{settings.SITE_URL or 'http://127.0.0.1:8000'}/gardens/",
                'profile_url': f"{settings.SITE_URL or 'http://127.0.0.1:8000'}/accounts/profile/edit/",
            }

            # Render email templates
            subject = f"🌱 Your Weekly Garden Digest"
            if notifications['total_overdue'] > 0 or notifications['total_due_today'] > 0:
                subject += f" - {notifications['total_overdue'] + notifications['total_due_today']} task"
                if (notifications['total_overdue'] + notifications['total_due_today']) > 1:
                    subject += "s"
                subject += " need attention"

            text_content = render_to_string('gardens/emails/weekly_digest.txt', context)
            html_content = render_to_string('gardens/emails/weekly_digest.html', context)

            if preview:
                self.stdout.write(self.style.SUCCESS(f'\n{"="*60}'))
                self.stdout.write(self.style.SUCCESS(f'EMAIL PREVIEW for {user.username} ({user.email})'))
                self.stdout.write(self.style.SUCCESS(f'{"="*60}'))
                self.stdout.write(f'Subject: {subject}\n')
                self.stdout.write(f'To: {user.email}')
                self.stdout.write(f'Timezone: {user_tz}')
                self.stdout.write(f'Notifications: {notifications["total_overdue"]} overdue, '
                                f'{notifications["total_due_today"]} due today, '
                                f'{notifications["total_coming_up"]} coming up\n')
                self.stdout.write('─' * 60)
                self.stdout.write(text_content)
                self.stdout.write('─' * 60 + '\n')
                continue

            if dry_run:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'  ✓ Would send to {user.username} ({user.email}) - '
                        f'{notifications["total_overdue"]} overdue, '
                        f'{notifications["total_due_today"]} due today, '
                        f'{notifications["total_coming_up"]} coming up'
                    )
                )
                emails_sent += 1
                continue

            # Send email
            try:
                email = EmailMultiAlternatives(
                    subject=subject,
                    body=text_content,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[user.email]
                )
                email.attach_alternative(html_content, "text/html")
                email.send()

                self.stdout.write(
                    self.style.SUCCESS(
                        f'  ✓ Sent to {user.username} ({user.email}) - '
                        f'{notifications["total_overdue"]} overdue, '
                        f'{notifications["total_due_today"]} due today, '
                        f'{notifications["total_coming_up"]} coming up'
                    )
                )
                emails_sent += 1

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'  ✗ Failed to send to {user.username}: {str(e)}')
                )

        # Summary
        self.stdout.write('\n' + '─' * 60)
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f'DRY RUN COMPLETE: Would have sent {emails_sent} email(s), '
                    f'skipped {emails_skipped} user(s) with no gardens'
                )
            )
        elif preview:
            self.stdout.write(
                self.style.SUCCESS(f'PREVIEW COMPLETE: Showed {emails_sent} email(s)')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'COMPLETE: Sent {emails_sent} email(s), '
                    f'skipped {emails_skipped} user(s) with no gardens'
                )
            )
