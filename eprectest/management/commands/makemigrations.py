
from django.core.management.commands.makemigrations import Command as RCommand
from django.contrib import admin
from ...db_procedures.schema import Schema 
import re

ep_schema = Schema('eprectest')

class Command(RCommand):
    def handle(self, *args, **options):
        if ep_schema.last_schema_filename:
            # if schemafile exists True
            # run django makemigrations command
            super().handle(*args, **options)

            if ep_schema.trunk_is_migrated:
                schemafile_leaf_names = set(ep_schema.last_schema_dict['leaves'])
                model_leaf_names = set(ep_schema.model_leaf_names)
                trunk_leaf_names = set(ep_schema.trunk_leaf_names)
                leaves_differences = model_leaf_names != trunk_leaf_names
                only_models = model_leaf_names - trunk_leaf_names
                only_in_trunk = trunk_leaf_names - model_leaf_names
                schemafile_leaves_differences = schemafile_leaf_names != model_leaf_names
                if schemafile_leaves_differences:
                    only_models and self.stderr.write(re.sub(r"[^\S\n]+", ' ',
                        f"'leaves': {model_leaf_names - trunk_leaf_names} \
                        are not in Trunk\nRun `manage.py migrate` to migrate \
                        them and trigger TrunkProcedures.refresh()"))
                    only_in_trunk and self.stderr.write(re.sub(r'[^\S\n]+', ' ', f"\
                        'leaves' : {trunk_leaf_names - model_leaf_names}\ are only \
                        in Trunk and not in models.\nRun `manage.py migrate` to \
                        trigger TrunkProcedures.refresh() => sync Trunk with models.\
                        "))
                    ep_schema.dumpschemafile_leaves_updated()
                    self.stdout.write(ep_schema.dumpschemafile_leaves_updated.message)
            else:
                self.stderr.write(re.sub("[^\S\n]+", ' ',f"\
                        Trunk is not migrated?\nIf so, \
                        run `manage.py migrate` !"))

        elif not ep_schema.last_schema_filename:
            # if there is no schemafile in schames directory
            # in order to save some previous data: check if Trunk is migrated
            # and try to get branches => dump schemafile, because schemafile is the
            # only code source for dynamically created Branches and Bunches classes (models)
            # After having a schemafile, can run `manage.py dumpschema` in order to
            # retreive from db bunches items.

            # if trunk is not migrated run `makemigrations` command 
            if not ep_schema.trunk_is_migrated:
                super().handle(*args, **options)
                ep_schema.dumpschema()
                self.stdout.write(ep_schema.dumpschema.message)
                self.stderr.write(re.sub(r"[^\S\n]+", ' ', f'\
                    Trunk model is not migrated.\n\
                    Run `manage.py migrate`.\nand run `manage.py makemigrations` \
                    again in order to retreive data from Trunk in initial schemafile.'))
            else:
                ep_schema.dumpschema()
                self.stdout.write(ep_schema.dumpschema.message)

