from django.core.management.base import BaseCommand
from django.contrib.admin.models import LogEntry

class Command(BaseCommand):
    help = 'Clears all records from the Django admin action log (django_admin_log).'

    def handle(self, *args, **options):
        count = LogEntry.objects.count()
        if count == 0:
            self.stdout.write(self.style.SUCCESS('No admin log entries to delete.'))
            return

        LogEntry.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f'Successfully cleared {count} admin log entries.'))
