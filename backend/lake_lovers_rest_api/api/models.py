from django.db import models

class Data (models.Model):
    location = models.CharField(max_length=1000)
    coordinates = models.CharField(max_length=100)
    operator = models.CharField(max_length=500)
    date = models.CharField(max_length=100)
    level = models.IntegerField()
    txt = models.CharField(max_length=100)
    tracking = models.CharField(max_length=500)
    upkeep = models.CharField(max_length=500)
    description = models.TextField()

    def __str__(self):
        return self.name
