from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.core.management.base import BaseCommand
from django.utils import timezone

from registration.views import _destroy_anonymous_account


class Command(BaseCommand):
    help = ("Deletes temporary (anonymous) accounts older than ANONYMOUS_ACCOUNT_TTL "
            "and clears expired sessions. Run it periodically, e.g. hourly via Heroku Scheduler.")

    def handle(self, *args, **options):
        cutoff = timezone.now() - timedelta(seconds=settings.ANONYMOUS_ACCOUNT_TTL)
        stale = User.objects.filter(user_type__type="Anonymous", date_joined__lt=cutoff)
        count = 0
        for user in stale.iterator():
            _destroy_anonymous_account(user)
            count += 1
        Session.objects.filter(expire_date__lt=timezone.now()).delete()
        self.stdout.write(self.style.SUCCESS(f"Deleted {count} expired anonymous account(s)."))
