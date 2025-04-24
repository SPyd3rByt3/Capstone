from django.db import models

class Skill(models.Model):
    name = models.CharField(max_length=50)

# Create your models here.
class Project(models.Model):
    name = models.CharField(max_length=150)
    description = models.TextField()
    year = models.IntegerField()
    image = models.ImageField(upload_to='static/')
    repository = models.URLField() 
    skills = models.ManyToManyField(Skill)
    
    def __str__(self):
        return f"{self.name} - ({self.year})"