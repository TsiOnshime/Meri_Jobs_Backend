from django.core.management.base import BaseCommand

from prep.consumers.match_found_consumer import run


class Command(BaseCommand):
    help = (
        "Long-running consumer for the match.found Kafka topic -- "
        "pre-generates and caches mock interview questions for matched "
        "jobs. Run as its own process/container, separate from the web "
        "server and the Celery worker."
    )

    def handle(self, *args, **options):
        run()