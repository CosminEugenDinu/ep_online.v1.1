from django.core.management.commands.migrate import Command as RCommand
from ...db_procedures.schema import TrunkProcedures2 as TrunkProcedures
from ...db_procedures.schema import Schema
from django.db.utils import ProgrammingError
import re

ep_schema = Schema('eprectest')
tr_proc = TrunkProcedures('eprectest', 'Trunk')

class Command(RCommand):
    def handle(self, *args, **options):
        super().handle(*args, **options)



        try:
            branches = [br.model_name for br in ep_schema.trunk_branches]
        except ProgrammingError as pe:
            self.stderr.write(re.sub(r'[^\S\n]+', ' ',f"\
                Schema('app_label').branches getter returned ProgrammingError:\n\
                {str(pe)}\n\
                Probably meaning that Trunk model was not migrated.\n\
                Maybe you should run `makemigrations` first!\n"
                ))
        else:
            if not ep_schema.last_schema_filename and len(branches) > 0:
                self.stdout.write(re.sub(r'[^\S\n]+', ' ', f"\
                    It seems that Trunk contains Branches data and\
                    no schema.json is present!\n\
                    Branches from Trunk: {branches}\n\
                    If you choose refresh Trunk with no schema.json,\
                    Trunk will be rewriten with data\
                    only from models statically typed in django.\n\
                    Please choose:\n\n\
                    1  to refresh Trunk anyway\n\
                    2  to dump schema.json from Trunk and abort refreshing Trunk\n\
                    "))
                chosen = int(input())
                if chosen == 1:
                    # TrunkProcedures('eprectest', 'Trunk').refresh()
                    tr_proc.refresh()
                elif chosen == 2:
                    ep_schema.dumpschema()
                    self.stdout.write(ep_schema.dumpschema.message)
                    self.stdout.write(re.sub(r'[^\S\n]+', ' ', f"\
                        To apply last schema.json run `makemigrations`!\n\
                        "))
            else:
                # this code is run if schema.json and Trunk table exists.
                try:
                    # TrunkProcedures('eprectest', 'Trunk').refresh()
                    tr_proc.refresh()
                    self.stdout.write(tr_proc.refresh.message)
                    if ep_schema.schema_graph_changes:
                        ep_schema.update_bunches_db()
                        self.stdout.write(ep_schema.update_bunches_db.message)
                        ep_schema.dumpschema()
                        self.stdout.write(ep_schema.dumpschema.message)
                except ProgrammingError as pe:
                    self.stderr.write(re.sub(r'[^\S\n]+', ' ', f"\
                        TrunkProcedures('eprectest', 'Trunk').refresh() \
                        raised ProgrammingError:\n\
                        {str(pe)}\n\
                        Maybe you should run `makemigrations` first!\n\
                        "))
