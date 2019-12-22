from django.core.management.commands.migrate import Command as RCommand
from ...db_procedures.schema import TrunkProcedures2 as TrunkProcedures
from ...db_procedures.schema import Schema
from django.db.utils import ProgrammingError

ep_schema = Schema('eprectest')
tr_proc = TrunkProcedures('eprectest', 'Trunk')

class Command(RCommand):
    def handle(self, *args, **options):
        super().handle(*args, **options)



        try:
            branches = [br.model_name for br in ep_schema.trunk_branches]
        except ProgrammingError as pe:
            self.stderr.write(f"""
Schema('app_label').branches getter returned ProgrammingError: 
{str(pe)}
Probably meaning that Trunk model was not migrated.
Maybe you should run `makemigrations` first!
                """)
        else:
            if not ep_schema.last_schema_filename and len(branches) > 0:
                self.stdout.write(f"""
It seems that Trunk contains Branches data and no schema.json is present!
Branches from Trunk: {branches}
If you choose refresh Trunk with no schema.json, Trunk will be rewriten with data
only from models statically typed in django.
Please choose:

1  to refresh Trunk anyway
2  to dump schema.json from Trunk and abort refreshing Trunk
                    """)
                chosen = int(input())
                if chosen == 1:
                    # TrunkProcedures('eprectest', 'Trunk').refresh()
                    tr_proc.refresh()
                elif chosen == 2:
                    ep_schema.dumpschema()
                    self.stdout.write(ep_schema.dumpschema.message)
                    self.stdout.write(f"""
To apply last schema.json run `makemigrations`!
                    """)
            else:
                # this code is run if schema.json and Trunk table exists.
                try:
                    # TrunkProcedures('eprectest', 'Trunk').refresh()
                    tr_proc.refresh()
                    self.stdout.write(tr_proc.refresh.message)
                except ProgrammingError as pe:
                    self.stderr.write(f"""
TrunkProcedures('eprectest', 'Trunk').refresh() raised ProgrammingError:
{str(pe)}
Maybe you should run `makemigrations` first!
                    """)
                # try:
                #     ep_schema.update_bunches()
                # except Exception as e:
                #     self.stderr.write(f"""
                #    Error from Schema.update_bunches(): {e}
                #     """)
