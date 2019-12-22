from django.conf import settings
import inspect
import json
import importlib
import os
import re
import types
from django.db import models
from django.db.models import Model as DjangoModel
from django.db.models import Count
from django.db.migrations.loader import MigrationLoader
from django.db.migrations.recorder import MigrationRecorder
from django.db.migrations import RenameModel
from django.apps import apps
from django.db.utils import ProgrammingError
import pprint as _pprint
import math

def pprint(*args):
    t = (*args,)
    p = _pprint.PrettyPrinter()
    p.pprint(t)


# Trunk model contains all app_modeltables from database
class Trunk(models.Model):
    model_id = models.IntegerField()
    table_name = models.CharField(max_length=64, unique=True)
    # hier_types: leaf, bunch, branch, hschema, trunk
    hier_type = models.CharField(max_length=10)
    keyword = models.CharField(max_length=64, unique=True) 
    model_name = models.CharField(max_length=64, unique=True)
    app_label = models.CharField(max_length=64)
    table_descr = models.TextField()
    admin_display = ('id','model_id', 'table_name', 'hier_type', 'keyword', 'model_name', 'app_label', 'table_descr')

    def __str__(self):
        return self.model_name

# Branch model. All Branch models inherit from this.
class Branch(models.Model):
    hier_type = "branch"
    table_descr = "Description from Branch"
    # bunch_id field is added by BranchesCreator and dinamically references coresponding Bunch table
    leaf_row_id = models.IntegerField(db_index=True)
    # index used to count the children. unique_together('index_as_child, 'parent') assures unique child row
    index_as_child = models.IntegerField(db_index=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE)

    # bunch will store a reference to associated Bunch model
    model_bunch = None

    class Meta:
        abstract = True
        # important! to test unique_together! Because a misstype ('parent_id' instead of 'parent') passed silenced!...
        unique_together = [('index_as_child', 'parent')]
    
    def __str__(self):
        return str(self.id)

# Bunch model. All Bunch models inherit from this.
class Bunch(models.Model):
    hier_type = "bunch"
    table_descr = "Description from Bunch"
    tablename = models.OneToOneField(Trunk, primary_key=True ,on_delete=models.CASCADE)
    admin_display = ('tablename',)
    class Meta:
        abstract = True
    
    def __str__(self):
        return str(self.tablename)

# ==============================================================================
class TrunkProcedures2():
    """
    Refreshes app_trunk table after runnig `migrate`.

    Trunk model (app_trunk table) is meant to store all app models tables names and related info.
    """
    def __init__(self, app_label, trunk_model_name):
        self.app_label = app_label
        self.trunk_model_name = trunk_model_name
        self.app = apps.get_app_config(app_label)
        self.trunk_model = self.app.get_model(trunk_model_name)
        self.models = [m for m in self.app.get_models() if m is not Trunk]

    def refresh(self):

        message = ''
        # get info about existing models
        models_table_names = []
        models_names = []
        models_ids = []
        for m in self.app.get_models():
            if m is not Trunk:
                models_table_names.append(m._meta.db_table)
                models_names.append(m._meta.object_name)
                models_ids.append((lambda m: getattr(m, 'model_id', 0))(m))
        # raise if there are more models with same model_id
        duplicate_model_ids = []
        for model_id in set(models_ids):
            if model_id > 0:
                if models_ids.count(model_id) > 1:
                    duplicate_model_ids.append({ 
                        model_id: [models_names[i] for i, m_n in enumerate(models_names)
                        if models_ids[i] == model_id]
                        })
        if duplicate_model_ids:
            raise Exception(f'Duplicate model_id attr found in: {duplicate_model_ids} models!')

        trunk_model_names_ids = {
            row.model_name: row.id
            for row in self.trunk_model.objects.all() 
        }
        
        # delete dirty data from Trunk; i.e Trunk records that are not models anymore
        for t_n in trunk_model_names_ids:
            # print(t_n)
            if t_n not in models_names:
                for_del = self.trunk_model.objects.get(id=trunk_model_names_ids[t_n])
                for_del.delete()
                message += f' >>> ({trunk_model_names_ids[t_n]}, {for_del.model_id}, "{for_del.model_name}") deleted from Trunk.\n'
        
        # should raise if a new model with model_id == model_id of deleted model from Trunk
        # is not yet migrated

        # get first missing id from sorted sequence of ids
        def missingFromSeq(sorted_seq, min=0, max=None ):
            max = max or len(sorted_seq)
            # stop rec
            if min >= max:
                return min + 1
            pivot = math.floor((min + max)/2)
            if (sorted_seq[pivot] == pivot + 1):
                return missingFromSeq(sorted_seq, pivot+1, max)
            else:
                return missingFromSeq(sorted_seq, min, pivot)
        trunk_ids = [tr_ob.id for tr_ob in self.trunk_model.objects.all()]
        trunk_ids_sorted = sorted(trunk_ids)
        id = missingFromSeq(trunk_ids_sorted)
        for model in self.models:
            trunk_fields = dict(
            id=getattr(model, 'model_id', id),
            model_id=getattr(model, 'model_id', 0),
            hier_type=getattr(model, 'hier_type', 'leaf'),
            table_name=model._meta.db_table,
            keyword=getattr(model, 'keyword', model._meta.model_name),
            model_name=model._meta.object_name,
            app_label=model._meta.app_label,
            table_descr=getattr(model, 'table_descr', 'no description')
            )
            # pprint(trunk_fields['id'], trunk_fields['model_id'], trunk_fields['model_name'])
            this_model_in_trunk = self.trunk_model.objects.filter(**{k:trunk_fields[k]for k in trunk_fields if k != 'id' and k != 'model_id'})
            if not this_model_in_trunk.exists():
                message += f''' >>> Model ({trunk_fields['id']}, {trunk_fields['model_id']}, "{trunk_fields['model_name']}")\
                    don't exists in Trunk -- query on all fields except 'id' and 'model_id'\n'''
                # check if wanted id is not in use already in Trunk.
                try:
                    this_id = self.trunk_model.objects.get(id = trunk_fields['id'])
                    exception_message = re.sub(r"[^\S\n]+", ' ', f'''\
                        ({trunk_fields['id']}, {trunk_fields['model_id']}, "{trunk_fields['model_name']}") could not be saved in Trunk. \
                        id={trunk_fields['id']} already in trunk: ({this_id.id}, {this_id.model_id}, "{this_id.model_name}") !''')
                    # raise Exception(exception_message)
                    raise Exception(exception_message)
                # if the model is not in Trunk then insert it
                except self.trunk_model.DoesNotExist:
                    trunk_instance = self.trunk_model(**trunk_fields)
                    trunk_instance.save()
                    message += f'\
                        >>> ({trunk_instance.id}, {trunk_instance.model_id}, "{trunk_instance.model_name}")\
                        inserted in trunk.\n'        

            # if model exists in Trunk (check all fields except id and model_id) than it might have different model_id in model class
            else:
                # get model from Trunk based on all attr except id and model_id
                this_model_exists = self.trunk_model.objects.get(**{k:trunk_fields[k]for k in trunk_fields if k != 'id' and k != 'model_id'})
                # if the model get from Trunk have different model_id than delete if from Trunk and insert with corresponding id and model_id from model_class
                if this_model_exists.model_id != trunk_fields['model_id']:
                    this_model_exists_id = this_model_exists.id
                    this_model_exists.delete()
                    message += f' >>> ({this_model_exists_id}, {this_model_exists.model_id} "{this_model_exists.model_name}")\
                         deleted from Trunk.\n'
                    this_model_exists.model_id = trunk_fields['model_id']
                    
                    # check if new id is not already in use
                    try:
                        this_id = self.trunk_model.objects.get(id=trunk_fields['id'])
                        raise Exception(re.sub(r"\s+", ' ', f"The id {trunk_fields['id']} wanted for model_name {trunk_fields['model_name']}\
                            is already used by '{this_id.model_name}'"))
                    except self.trunk_model.DoesNotExist:
                        this_model_exists.id = trunk_fields['id']
                        this_model_exists.save()
                        message += f''' >>>({this_model_exists.id}, {this_model_exists.model_id}, "{this_model_exists.model_name}")\
                            inserted in Trunk.\n'''
            
            trunk_ids_sorted = sorted([tr_ob.id for tr_ob in self.trunk_model.objects.all()])
            id = missingFromSeq(trunk_ids_sorted)

        intro = f'>>> {type(self).__name__}.{inspect.stack()[0][3]}.message  said: >>>\n'
        message = intro + message if message else ''
        message = re.sub(r"[^\S\n]+", ' ', message)
        TrunkProcedures2.refresh.message = message 

def create_dj_model(app_label, model_name, inherit=(models.Model,) ,to_string=None, **fields):
    
    class Meta:
        nonlocal app_label
        app_label = app_label

    def to_str_default(self):
        return "This is __str__ from django model metaclass." 

    dj_required_fields = {
        # "Meta": Meta,
        "__module__": app_label,
        "__str__": to_string if callable(to_string) else to_str_default,
        "__unicode__": to_string if callable(to_string) else to_str_default
    }

    return type(model_name, inherit, {**dj_required_fields, **fields})

class Schema:
    """Schema"""

    def __init__(self, app_label='eprectest'):
        self.app_label = app_label
        self.app = apps.get_app_config(app_label)
        app_root = os.path.join(settings.BASE_DIR, app_label)
        schemas_path = os.path.join(app_root, 'schemas')
        if not os.path.isdir(schemas_path):
            os.mkdir(schemas_path)
            print('"schemas" directory created...')
        self.schemas_path = schemas_path
        self.trunk_q = Trunk.objects.all()
        # add 'message' property to all function objects methods of this class
        self.__class__.add_message_to_methods()

    @property 
    def trunk_is_migrated(self):
        try:
            tr_q_all = self.trunk_q_all
            if tr_q_all:
                return True
        except ProgrammingError as pe:
            p = r'''\s*(relation)\s+('|")([\w_]+)_(trunk)\2\s+(.*\S+)+\s*'''
            m = re.match(p, pe.args[0], flags=re.I)
            relation, _, app_label, trunk, message = m.groups()
            if ( 
                re.match(r'\s*relation\s*', relation, flags=re.I)
                and re.match(rf'{self.app_label}', self.app_label, flags=re.I)
                and re.match(r'\s*trunk\s*', trunk, flags=re.I)
                and re.match(r'\s*does\s+not\s+exist\s*', message, flags=re.I)
                ):
                return False
            else:
                raise pe
        except Exception as e:
            raise e


    @property
    def trunk_q_all(self):
        return [tr_ob for tr_ob in Trunk.objects.all()]

    @property
    def trunk_leaves(self):
        return Trunk.objects.filter(hier_type='leaf')
    
    @property
    def trunk_leaf_names(self):
        return [tr_l.model_name for tr_l in self.trunk_leaves]
    
    @property
    def model_leaves(self):
        ml = [
            model for model in self.app.get_models() 
                if not (
                hasattr(model, 'hier_type')
                or (hasattr(model, 'hier_type') and model.hier_type == 'leaf')
                or model is Trunk
                )
        ]
        return ml 

    @property
    def model_leaf_names(self):
        '''Return names of model classes type leaf
        A leaf is a standard Django model
        '''
        return [ml._meta.object_name for ml in self.model_leaves]

    @property
    def model_bunches(self):
        m_bu = [ model for model in self.app.get_models()
            if issubclass(model, Bunch) and Bunch.hier_type == 'bunch'
        ]
        return m_bu
    @property
    def model_branches(self):
        m_br = [ model for model in self.app.get_models()
            if issubclass(model, Branch) and Branch.hier_type == 'branch'
        ]
        return m_br
    @property
    def model_branch_names(self):
        return [m_br._meta.object_name for m_br in self.model_branches]
    @property
    def trunk_branches(self):
        return Trunk.objects.filter(hier_type='branch')
    
    @property
    def trunk_branch_names(self):
        return [tr_br.model_name for tr_br in self.trunk_branches]
         
    @property
    def trunk_bunches(self):
        return Trunk.objects.filter(hier_type='bunch')

    @property
    def last_schema_filename(self):
        if self.schema_files:
            return sorted(
                self.schema_files, key=lambda x: int(x.split('_')[0]),
                reverse=True
                )[0] 
             
    @property
    def last_schema_filepath(self):
        if self.last_schema_filename:
            return os.path.join(self.schemas_path, self.last_schema_filename)
    
    @property
    def last_schema_dict(self):
        if self.last_schema_filename:
            with open(self.last_schema_filepath, 'r') as json_schema:
                schema = json.load(json_schema)
            return schema

    @property
    def last_schema_graph_ids(self):
        """takes "schema_graph" from last_schema.json and
        converts adjacent bunches items (names) to ids from Trunk in place
        """
        schema_graph = self.last_schema_dict['schema_graph']
        # change adjacent model_names in schema_graph with ids from Trunk in place
        for t_info in self.trunk_q:
            for branch_name in schema_graph:
                for i, adjacent in enumerate(schema_graph[branch_name]):
                    if t_info.model_name == adjacent:
                        schema_graph[branch_name][i] = t_info.id
        return schema_graph

    @property
    def schema_graph_from_db_ids(self):
        """get schema_graph from db with adjacent items of bunches as ids from bunches_tables;
        get branches and coresponding bunches from models and bunches content from db
        """
        return {
        m_br._meta.object_name:[bu_record.tablename_id
            for bu_record in m_br.model_bunch.objects.all()]
        for m_br in self.model_branches
        }
    @property
    def schema_graph_from_db_ids(self):
        """
        Returns dict schema_graph from Trunk and Bunches tables
        """
        return {
            m_br._meta.object_name: [
                bu_record.tablename_id
                for bu_record in m_br.model_bunch.objects.all()
            ]
            for m_br in [
                self.app.get_model(tr_br.model_name)
                for tr_br in self.trunk_branches
                ]
        }
    @property
    def schema_files(self):
        """Return a list with schemafiles.json found in schemas directory
        """
        return [
                sch_file
                for root, directory, files in os.walk(self.schemas_path)
                for sch_file in files
                if re.compile(r"^\d{1,4}_\w*\.json$").match(sch_file)
                ]
    
    @property
    def trunk_leaves_changes(self):
        """ return True if were created or deleted leaf-tables """
        with open(self.last_schema_filepath, 'r') as json_schema:
            schema = json.load(json_schema)
            schema_leaves = schema['leaves']
        trunk_leaves = (leaf.model_name for leaf in self.leaves)
        return not set(schema_leaves) == set(trunk_leaves)
    
    @property
    def model_leaves_changes(self):
        """ return True if were created or deleted leaf-models 
        (leaves from schema.json are not the same as leaves model_leaves)
        Whenever you create or delete a model class (considered leaf)
        """
        with open(self.last_schema_filepath, 'r') as json_schema:
            schema = json.load(json_schema)
            schema_leaves = schema['leaves']
        model_leaves_names = [m._meta.object_name for m in self.model_leaves]
        return not (set(schema_leaves) == set(model_leaves_names))
    
    @property
    def schema_graph_changes(self):
        """ return True content of "bunches" (adjacent items) from "schema_graph"
        from last schemafile.json
        is different than schema_graph from db (trunk and bunches)
        """
        if self.last_schema_graph_ids != self.schema_graph_from_db_ids:
            return True
        else:
            return False


    def create_branches_bunches(self):
        """Dinamically creates Branches and associated Bunches models,
        having as source "schema_graph" from last schemafile.json
        """

        if issubclass(Branch, DjangoModel) and Branch.hier_type == 'branch':
            branch_meta_model = Branch
        else:
            raise Exception("Branch model does not inherit from django.db.model.Model or Branch.hier_type is not 'Branch'  ")
        if issubclass(Bunch, DjangoModel) and Bunch.hier_type == 'bunch':
            bunch_meta_model = Bunch
        else:
            raise Exception("Bunch model does not inherit from django.db.model.Model or Bunch.hier_type is not 'bunch' ")

        # print('Creating Branches from ', self.last_schema_filename)
        if self.last_schema_filename is None: 
            return
        with open(self.last_schema_filepath, 'r') as json_schema:
            schema = json.load(json_schema)
        # get branches names from schemafile_schema_graph
        branches_names = [branch_name for branch_name in schema['schema_graph']]
        bunches_names = [f'Bunch_{branch_name}' for branch_name in branches_names]
        branch_inherit = (branch_meta_model,)
        bunch_inherit = (bunch_meta_model,)
        bunch_extra_fields = dict()
        branches_models = [
            create_dj_model(
                self.app_label, branch_name,
                inherit=branch_inherit,
                to_string=branch_meta_model.__str__,
                **{
                    f"bunch_{branch_name.lower()}": models.ForeignKey(
                                                    f'Bunch_{branch_name}',
                                                    on_delete=models.CASCADE)
                }
            )
            for branch_name in branches_names
        ]
        bunches_models = [
            create_dj_model(
                self.app_label, bunch_name,
                inherit=bunch_inherit,
                to_string=bunch_meta_model.__str__,
                **bunch_extra_fields
            )
            for bunch_name in bunches_names
        ]
        # asign a ref to Bunch model to bunch_model property of Branch model
        for br, bu in zip(branches_models, bunches_models):
            br.model_bunch = bu
        # a list with [X, Bunch_X, Y, Bunch_Y, Z, Bunch_Z]
        br_bu_models = [ br_bu
            for pair in zip(branches_models, bunches_models)
            for br_bu in pair
            ]
        for br_bu in br_bu_models:
            yield br_bu

    def dumpschema(self):
        """
        Dump a schema.json based on actual status of trunk table,
        ...
        """
        message = ''
        # getting leaves, branches, bunches from Trunk and return if exception occured in _query_trunk()
        schema_snap = {}
        # schema_snap['leaves'] = [leaf._meta.object_name for leaf in self.model_leaves]
        schema_snap['leaves'] = self.model_leaf_names 
        schema_snap['branches'] = []
        schema_snap['schema_graph'] = {}

        if  self.last_schema_filename and self.trunk_is_migrated:
            next_schema_num = int(self.last_schema_filename.split('_')[0]) + 1
            next_schema_name = f'{next_schema_num}_schema.json'
            trunk_q = Trunk.objects.all()
            # get branches names from Trunk
            schema_snap['branches'] = [br.model_name for br in trunk_q if br.hier_type == 'branch']
            message += ' >>> "branches" retreived from Trunk ...\n'
            # get schema graph from models and db with adjacent items as ids
            schema_graph_db_ids = self.schema_graph_from_db_ids
            message += ' >>> "schema_graph_from_db_ids" received from Trunk and Bunches.\n'
            # replace adjacent ids with names from Trunk
            # change adjacent ids in schema_graph_db_ids with names from Trunk in place
            schema_graph = schema_graph_db_ids
            for t_info in trunk_q:
                # print((t_info.model_name, t_info.model_id))
                for branch_name in schema_graph_db_ids:
                    for i, adjacent in enumerate(schema_graph[branch_name]):
                        if t_info.id == adjacent:
                            schema_graph[branch_name][i] = t_info.model_name
            schema_snap['schema_graph'] = schema_graph

        elif (not self.last_schema_filename) and (not self.trunk_is_migrated):
            next_schema_name = '0_initial_schema.json'
        
        elif (not self.last_schema_filename) and self.trunk_is_migrated:
            next_schema_name = '0_trunk_recovered_schema.json'
            schema_snap['branches'] = self.trunk_branch_names
            message += f" >>> 'branches' names recovered from Trunk.\n"
            message += '\n'
            message += ' >>> In order to recover bunches items from db\n\
                run `manage.py dumpschema` !\n\n'
        


        next_schema_path = os.path.join(self.schemas_path, next_schema_name)
        
        try:
            with open(next_schema_path, 'w') as schema_file:
                json.dump(schema_snap, schema_file, indent=4)
        except Exception as e:
            raise e
        else:
            message += f' >>> Schema "{next_schema_name}" was created in {self.schemas_path} !'
            self.add_message_to_myself(message)
            return True
    
    def dumpschemafile_leaves_updated(self):
        """Dump schema.json if are changes between model_leaves and trunk_leaves
        and previous schemafile exists
        'branches' and 'schema_graph' are copied from prev. schemafile
        """
        message = ''
        if self.last_schema_filename:
            next_schema_num = int(self.last_schema_filename.split('_')[0]) + 1
            next_schema_name = f'{next_schema_num}_schema_leaves_updated.json'
            next_schema_path = os.path.join(self.schemas_path, next_schema_name)
        else:
            raise Exception("No previous schemafile!")
        with open(self.last_schema_filepath, 'r') as last_schema:
            last_schema_dict = json.load(last_schema)
        schema_snap = {
            'leaves': self.model_leaf_names,
            # 'branches': last_schema_dict['branches'],
            'branches': self.model_branch_names,
            'schema_graph': last_schema_dict['schema_graph']
        }
        with open(next_schema_path, 'w') as next_schemafile:
            json.dump(schema_snap, next_schemafile, indent=4)
        message += f' >>> Schemafile "{next_schema_name}" \
                was created in {self.schemas_path} !\n'
        self.add_message_to_myself(message)
        return True
        
    def dumpschema_from_db(self):
        """
        Dump schema.json from Trunk (query Trunk for Branches) and Bunches tables
        """
        print('hi from dumpschema_from_db') 

    # def dumpschema_from_migrated_models(self):
    #     """Dump schema.json from django models and db. All models must be migrated."""
    #     pass
    
    def update_bunches_db(self):
        """Update/insert/delete data in bunches in sync with schema_graph.

        This function should be run at `migrate` command.

        Every Branch table has an associated Bunch table 
        (i.e appLabel_BranchTableName has appLabel_Bunch_BranchTableName).
        Every Branch table has a bunch_branchModelName_id field 
        with foreign key to appLabel_Bunch_BranchTableName id.
        A Bunch table for a Branch table contains tablename_id with
        ids of table_names from Trunk.
        These ids limit the data that can be inserted in a Branch table.
        """
        message = ''
        # message += f' >>> self.schema_graph_changes returned: {self.schema_graph_changes} \n'

        schema_graph = self.last_schema_graph_ids
        
    
        
        for model_branch in self.model_branches:
            # delete bunches items from bunches tables that are not anymore
            # in last schemafile_graph
            model_name = model_branch._meta.object_name
            bunch = model_branch.model_bunch
            bunch_name = bunch._meta.object_name
            # inserts ids of tables in bunches for every branch
            for tablename_id in schema_graph[model_name]:
                message += f' >>> Insert/Update (tablename_id={tablename_id}, \
                    model_name="{Trunk.objects.get(id=tablename_id).model_name}") \
                    in "{bunch_name}"\n'
                bunch(tablename_id=tablename_id).save()
            # delete from db bunches if not in last schemafile_graph
            db_bunch_items = [bu_it.tablename_id for bu_it in bunch.objects.all()]
            message += f' >>> Bunch "{bunch_name}" contain {db_bunch_items}\n'
            for i in db_bunch_items:
                if i not in schema_graph[model_name]:
                    message += f' >>> {i} is in Bunch {bunch_name} and not in schema_graph["{model_name}"]\n'
                    bunch.objects.get(tablename_id=i).delete()
                    message += f' >>> "{Trunk.objects.get(id=i).model_name}" deleted from Bunch "{bunch_name}"\n'
                
            
            
        message += '\n'
        # message += f' >>> {schema_graph == self.schema_graph_from_db_ids}'
        self.add_message_to_myself(message)

        return None 

    @classmethod
    def add_message_to_methods(cls):
        """When is called in __init__ with the statement: 
        'self.__class__.add_message_to_methods()'
        this class method adds the property 'message' to all
        methods of that class (methods are function objects and can have props)
        except `magic` methods.
        """
        method_names = [
            met_name
            for met_name in cls.__dict__
            if type(cls.__dict__[met_name]) == types.FunctionType
            and re.match(r'[^_]{2}\S*?[^_]{2}', met_name)
            and met_name != cls.add_message_to_methods.__name__
        ]
        for m_n in method_names:
            cls.__dict__[m_n].message = f'>>> {cls.__name__}.{m_n}.message said: >>>\n'

    def add_message_to_myself(self, message):
        """When this method is run inside a method of this class from on instance call,
        gets the name of the caling method and appent message variable defined
        inside that methon to the property 'message' of that method
        (the method is a function object and can have also added static properties,
        like this 'message' property)
        """
        # replace multiple white spaces from message with single whitespace
        message = re.sub(r"[^\S\n]+", ' ', message)
        import sys
        # get the name of the method (function) where add_message_to_myself(mes) was called
        who_called_me = sys._getframe(1).f_code.co_name
        # append str from variable message of that function to property message of that function
        type(self).__dict__[who_called_me].message += message

        