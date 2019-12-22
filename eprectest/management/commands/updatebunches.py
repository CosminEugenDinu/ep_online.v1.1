from django.core.management.base import BaseCommand
from ...db_procedures.schema import Schema
import pprint

s = Schema('eprectest')

class Command(BaseCommand):
    help = """some help"""

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        self.stdout.write(f'Running update_bunches() ...')
        s.update_bunches_db()
        self.stdout.write(s.update_bunches_db.message)