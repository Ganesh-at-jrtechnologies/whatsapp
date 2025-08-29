from django.db import models

# Create your models here.

class PartyMaster(models.Model):
    party_master_code = models.CharField(max_length=50,primary_key=True)
    party_name = models.CharField(max_length=50)
    phone =  models.CharField(max_length=50)
    beat =  models.CharField(max_length=50)
    hul_code =  models.CharField(max_length=50)
    address =  models.CharField(max_length=250)
    
    