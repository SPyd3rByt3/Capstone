from django.db import models

# Create your models here.

class Note(models.Model):
    title = models.CharField(max_length=50)
    content = models.TextField()

    image = models.ImageField(upload_to='notes/', blank=True, null=True)

    created_on = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return self.title
