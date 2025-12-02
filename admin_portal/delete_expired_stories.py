from django.core.management.base import BaseCommand
from django.utils import timezone
from admin_portal.models import SuccessStory

class Command(BaseCommand):
    help = 'Deletes success stories that have expired (older than one year)'

    def handle(self, *args, **kwargs):
        expired_stories = SuccessStory.objects.filter(expires_at__lte=timezone.now())
        count = expired_stories.count()
        expired_stories.delete()
        self.stdout.write(self.style.SUCCESS(f'Successfully deleted {count} expired success stories'))