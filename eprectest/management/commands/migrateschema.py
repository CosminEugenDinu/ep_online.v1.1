from django.core.management.base import BaseCommand, CommandError
from ...db_procedures.schema import Schema

class Command(BaseCommand):
    help = Schema.__doc__
    
    def handle(self, *args, **options):
        s = Schema('eprectest')
        # s.migrateschema()
        print(s.trunk_is_migrated)

