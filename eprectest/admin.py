from django.contrib import admin
from django.apps import apps

app = apps.get_app_config('eprectest')
# admin.site.register(app.get_models())

for model in app.get_models():

    # these names will become class names; i.e XModel will have class XModelAdmin(admin.ModelAdmin)
    md_admin_cls_name = f'{model._meta.object_name}Admin'
    if hasattr(model, 'admin_display'):
        md_admin_display = model.admin_display
    else:
        md_admin_display = None

    md_admin_cls_attr = {}
    # if a model has attr 'admin_display' then this attribute will become attr 'list_display' in XModelClass
    if md_admin_display:
        md_admin_cls_attr['list_display'] = md_admin_display

    # dinamically creates XModelAdmin classes
    ModelAdminClass = type(md_admin_cls_name, (admin.ModelAdmin,), md_admin_cls_attr)

    # binding md_admin_cls_names to this module
    globals()[ModelAdminClass.__name__] = ModelAdminClass

    # registering both Model and associated XModelAdmin classes
    admin.site.register(model, ModelAdminClass)