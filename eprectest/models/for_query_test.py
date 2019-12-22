from django.db import models
from django.apps import apps


app = apps.get_app_config('eprectest')

# class q_Client_branch(models.Model):
#     table_name = models.CharField(max_length=100)
#     leaf_row_id = models.IntegerField(db_index=True)
#     # index used to count the children. unique_together('index_as_child, 'parent_id') assures unique child row
#     index_as_child = models.IntegerField(db_index=True)
#     parent = models.ForeignKey('self', on_delete=models.CASCADE)

#     class Meta:
#         # abstract = True
#         unique_together = ('index_as_child', 'parent')

# class q_Names_leaf(models.Model):
#     name = models.CharField(max_length=100)
#     # model_id = 300

# class q_Phones_leaf(models.Model):
#     number = models.CharField(max_length=10)
# #     model_id = 600
# class Another_duplicate(models.Model):
#     dup = models.CharField(max_length=100)
#     model_id = 77777777

# class Another_dup_2(models.Model):
#     dup2 = models.CharField(max_length=100)
#     model_id = 33

# class New_model_32_test(models.Model):
#     name = models.CharField(max_length=100)
#     model_id = 35

# class A_definetely_new_test_mode(models.Model):
#     name = models.CharField(max_length=100)
#     model_id = 49 

# class New_model_11_test(models.Model):
#     name = models.CharField(max_length=100)
#     model_id = 52 # like old Dummy_test

# class q_Addresses_leaf(models.Model):
#     address = models.CharField(max_length=100)

# class Dummy_test(models.Model):
#     dummy_text = models.CharField(max_length=100)
#     dummy_text2 = models.CharField(max_length=100)

#     class Meta:
#         unique_together = ('dummy_text', 'dummy_text2')

# class Test_without_unique(models.Model):
#     text1 = models.CharField(max_length=20)
#     text2 = models.CharField(max_length=20)


# class Dummy_test_2(models.Model):
#     some_field = models.CharField(max_length=100)

# class PlsDeleteMe_renamed2(models.Model):
#     del_pls = models.CharField(max_length=100)

data = {
    'names': [
        'name_0', 
        'name_1', 
        'name_2',
        'name_3',
        'name_4',
        'name_5',
        'name_6',
        'name_7',
        'name_8',
        'name_9',
    ],
    'phones': [
        '0000000000',
        '1111111111',
        '2222222222',
        '3333333333',
        '4444444444',
        '5555555555',
        '6666666666',
        '7777777777',
        '8888888888',
        '9999999999',
    ],
    'addresses': [
        'address 0',
        'address 1',
        'address 2',
        'address 3',
        'address 4',
        'address 5',
        'address 6',
        'address 7',
        'address 8',
        'address 9',
    ],
    'leaves': (
        ('eprectest_q_names_leaf', 'names'),
        ('eprectest_q_phones_leaf', 'phones'),
        ('eprectest_q_addresses_leaf', 'addresses'),
    ),
    'clients': [
        (1, 'eprectest_q_names_leaf', 1, 0, 1),
        (2, 'eprectest_q_phones_leaf', 1, 1, 1), # '0000000000'
        (3, 'eprectest_q_phones_leaf', 2, 2, 1), # '11111111111'
        (4, 'eprectest_q_addresses_leaf', 1, 3, 1), # 'address 0'
        (5, 'eprectest_q_addresses_leaf', 2, 4, 1), # 'address 1'
        (6, 'eprectest_q_addresses_leaf', 3, 5, 1), # 'address 2'
    ]
}

def insert_client():
    for client_tuple in data['clients']:
        client = q_Client_branch(*client_tuple)
        client.save()

def insert_data(data):
    
    insert_client()

    for entity in data:
        for leaf in data['leaves']:
            if entity in leaf:
                for model in app.get_models():
                    if model._meta.db_table == leaf[0]:
                        for i, e in enumerate(data[entity]):
                            id = i+1
                            print(f'inserting/updating "{e}" in "{model._meta.db_table}"')
                            model(id, e).save()
                        
def get_client(id):
    client_qs = q_Client_branch.objects.filter(parent=id)
    client_leaves_names = [c.table_name for c in client_qs]
    client = {k:[] for k in client_leaves_names}
    for client_attr in client_qs:
        leaf_table_name = client_attr.table_name
        leaf_table_model = [m for m in app.get_models()
            if m._meta.db_table == leaf_table_name][0]
        q_obj = leaf_table_model.objects.get(id=client_attr.leaf_row_id)
        q_obj_fields_names = [f.name for f in q_obj._meta.get_fields()]
        q_obj_vals = tuple(q_obj.__getattribute__(n) for n in q_obj_fields_names)
        if client[leaf_table_name]:
            client[leaf_table_name] += [q_obj_vals]
        else:
            client[leaf_table_name] = [q_obj_vals]
    return client