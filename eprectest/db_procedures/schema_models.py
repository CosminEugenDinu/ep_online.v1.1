from .schema import Trunk, Schema

ep_schema = Schema('eprectest')

# sch_models = [model for model in ep_schema.create_branches_bunches()]

# bind dinamically created models classes names to global variables with the same name
for class_model in ep_schema.create_branches_bunches():
    globals()[class_model.__name__] = class_model