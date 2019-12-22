from django.db import models
from django.contrib.auth.models import User

class ClientDescr(models.Model):
    name = models.CharField(max_length=64)
    date_become_client = models.DateTimeField(auto_now_add=True)
    other_details = models.TextField()

class Person(models.Model):
    firstname = models.CharField(max_length=64)
    lastname = models.CharField(max_length=64)
    born = models.DateField()
    # model_id = 105
    gender = models.ForeignKey('GenderCategory', on_delete=models.SET_NULL, null=True, blank=False)

    def __str__(self):
        return self.firstname

class LegalEntity(models.Model):
    name = models.CharField("name", max_length=64)
    company_name = models.CharField("company_name", max_length=64)
    identifier = models.CharField(max_length=32)
    vat_code = models.CharField(max_length=32)

    def __str__(self):
        return self.name

class EpUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    admin_display = ('user',)
    # def __str__(self):
    #     return self.user

# class Client(Branch):
#     pass

class Email(models.Model):
    admin_display = ('email', 'category_id')
    email = models.EmailField()

    def _get_id_(*args):
        return 1
    category_id = models.ForeignKey('EmailCategory', on_delete=models.SET_DEFAULT, default=_get_id_())
    def __str__(self):
        return self.email

class Phone(models.Model):
    phone = models.CharField(max_length=20)
    # date_added = 
    
    admin_display = ('phone', 'category')
    def _get_id_(*args):
        return 1
    category = models.ForeignKey('EmailCategory', on_delete=models.SET_DEFAULT, default=_get_id_())
    
# date_last_changed = 
# modified_by = key to user