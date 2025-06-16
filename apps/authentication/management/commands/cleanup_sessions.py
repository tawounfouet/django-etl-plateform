from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from apps.authentication.models import UserSession


class Command(BaseCommand):
    help = 'Clean up expired user sessions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Clean sessions older than N days (default: 30)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting'
        )

    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']
        
        cutoff_date = timezone.now() - timedelta(days=days)
        
        expired_sessions = UserSession.objects.filter(
            last_activity__lt=cutoff_date
        )
        
        count = expired_sessions.count()
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'DRY RUN: Would delete {count} sessions older than {days} days'
                )
            )
            for session in expired_sessions[:10]:  # Show first 10
                self.stdout.write(f'  - {session.user.email}: {session.last_activity}')
            if count > 10:
                self.stdout.write(f'  ... and {count - 10} more')
        else:
            deleted_count, _ = expired_sessions.delete()
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully deleted {deleted_count} expired sessions'
                )
            )
