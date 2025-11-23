from django.db import models

class Data(models.Model):
    location = models.CharField(max_length=1000, default="")
    operator = models.CharField(max_length=500, default="")
    date = models.DateField()
    level = models.IntegerField(default=0)
    txt = models.CharField(max_length=100, default="")
    tracking = models.CharField(max_length=500, default="")
    upkeep = models.CharField(max_length=500, default="")
    description = models.TextField(default="")
    latitude = models.FloatField(default=0)
    longitude = models.FloatField(default=0)

    def __str__(self):
        return self.name

class ProvinceRequest(models.Model):
    province = models.IntegerField()
    date = models.DateField()

    def __str__(self):
        return self.name
    
class Predict(models.Model):
    date = models.CharField(max_length=255)
    lat = models.FloatField()
    lon = models.FloatField()
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name