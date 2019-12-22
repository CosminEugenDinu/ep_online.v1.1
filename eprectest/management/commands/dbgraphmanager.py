
from django.core.management.base import BaseCommand
from ...db_procedures.db_graph_manager import DbGraphManager
import pprint as _pprint
import re

def pprint(*args):
    t = (*args,)
    p = _pprint.PrettyPrinter()
    p.pprint(t)

dgm = DbGraphManager()

class Command(BaseCommand):
    help = """some help"""

    def add_arguments(self, parser):
        parser.add_argument('args_str', type=str)


    def handle(self, *args, **options):
        args_str = options['args_str'] or ''
        p = r'''\s*(\w+)\s*'''
        m = re.findall(p, args_str)
        print(m)
        print('------------')
        args = m
        pprint(dgm.give_me(*args, kw='keyword'))