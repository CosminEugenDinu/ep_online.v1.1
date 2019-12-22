from django.db import models



class Translation(models.Model):
    ro_text = models.TextField()

    def __str__(self):
        return self.ro_text


class GenderCategory(models.Model):
    name = models.CharField(max_length=64)
    is_custom = models.BooleanField(default=True)
    translation = models.ForeignKey(Translation, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.name
    # def __str__(self):
    #     return self.translation

class AddressCategory(models.Model):
    # hier_type="leaf"
    name = models.CharField(max_length=32)
    is_custom = models.BooleanField(default=True)
    translation = models.ForeignKey(Translation, on_delete=models.SET_NULL, null=True, blank=True)
    def __str__(self):
        return self.name
    # def __str__(self):
    #     return self.translation

class ContactCategory(models.Model):
    name = models.CharField(max_length=32)
    is_custom = models.BooleanField(default=True)
    translation = models.ForeignKey(Translation, on_delete=models.SET_NULL, null=True, blank=True)
    def __str__(self):
        return self.name
    # def __str__(self):
    #     return self.translation

class PhoneCategory(models.Model):
    name = models.CharField(max_length=32)
    is_custom = models.BooleanField(default=True)
    translation = models.ForeignKey(Translation, on_delete=models.SET_NULL, null=True, blank=True)
    def __str__(self):
        return self.name
    # def __str__(self):
    #     return self.translation

class EmailCategory(models.Model):
    name = models.CharField(max_length=32)
    is_custom = models.BooleanField(default=True)
    translation = models.ForeignKey(Translation, on_delete=models.SET_NULL, null=True, blank=True)
    def __str__(self):
        return self.name
    # def __str__(self):
    #     return self.translation
    
class AddressType(models.Model):

    type_name = models.CharField(max_length=32) # e.g. county, city, sector, town, street, number_str, building, entrance, floor, apartment
    translation = models.ForeignKey(Translation, on_delete=models.SET_NULL, null=True, blank=True)
    def __str__(self):
        return self.type_name
    # def __str__(self):
    #     return self.translation