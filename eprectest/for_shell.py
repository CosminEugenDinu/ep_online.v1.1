from django.apps import apps
from .db_procedures.schema_models import sch_models
print(sch_models)

# models = [model for model in apps.get_app_config('eprectest').get_models()]

# for r in dir(models[0]._meta):
#     print(r)

# print(models[0]._meta.model_name)
# print(models)

# closure test
def closure():
    on_off = 0
    def magic():
        nonlocal on_off
        on_off = 1 if on_off == 0 else 0
        return on_off
    return magic

# generator test
def gen():
    num = 0
    while num < 10:
        yield num
        num += 1


# for n in gen():
#     print(n)

global_a = 'global_a_val'

def printglobals():
    print(globals())