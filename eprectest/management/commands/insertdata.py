from django.core.management.base import BaseCommand
from ...models.for_query_test import insert_data, data
import pprint

class Command(BaseCommand):
    help = """some help"""

    def handle(self, *args, **options):
        self.stdout.write(f'data to be inserted:')
        p = pprint.PrettyPrinter()
        # p.pprint(data)
        insert_data(data)
