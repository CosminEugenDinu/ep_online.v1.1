from django.core.management.base import BaseCommand
from ...models.for_query_test import get_client
import pprint

class Command(BaseCommand):
    help = """some help"""

    def add_arguments(self, parser):
        parser.add_argument('id', type=int)

    def handle(self, *args, **options):
        id = options['id']
        self.stdout.write(f'getting client id={id} ...')
        client = get_client(id)
        p = pprint.PrettyPrinter()
        p.pprint(client)
