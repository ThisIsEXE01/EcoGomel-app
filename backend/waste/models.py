from django.db import models

# Create your models here.
class WasteItem(models.Model):
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=200)
    code = models.CharField(max_length=200)
    recyclable = models.BooleanField()
    preparation = models.TextField()
    
    def __str__(self):
        return self.name
