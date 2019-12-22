
from django.core.management.commands.makemigrations import Command as RCommand
from django.contrib import admin
from ...db_procedures.schema import Schema 

ep_schema = Schema('eprectest')

class Command(RCommand):
    def handle(self, *args, **options):
        if ep_schema.last_schema_filename:
            # if ep_schema.model_leaves_changes or ep_schema.schema_graph_changes:
            if ep_schema.model_leaves_changes or ep_schema.schema_graph_changes:
            # if ep_schema.model_leaves_changes:
                self.stderr.write("Changes detected in leaves or schema_graph!")
                # ep_schema.dumpschema()
                # self.stdout.write(ep_schema.dumpschema.message)
                # self.stderr.write('Run again `makemigrations` to apply last dumped schema.json!')
            else:
                # super().handle(*args, **options)
                pass
                
        elif ep_schema.dumpschema():
            self.stdout.write(ep_schema.dumpschema.message)
            ep_schema.dumpschema()
            self.stdout.write(ep_schema.dumpschema.message)
            self.stderr.write('Was no schema.json found in schemas directory!\nRun again `makemigrations` to apply last dumped schema.json!')
            return
            