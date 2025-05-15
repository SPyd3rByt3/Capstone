from django.db import models
from django.contrib.auth.models import User

# Create your models here.

from django.utils.text import slugify

class Note(models.Model):
    title = models.CharField(max_length=50)
    content = models.TextField()

    image = models.ImageField(upload_to='notes/', blank=True, null=True)

    link_url = models.URLField(blank=True, null=True)

    slug = models.SlugField(max_length=60, unique=False, blank=True)

    created_on = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while Note.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

class NoteComment(models.Model):
    note = models.ForeignKey(Note, on_delete=models.CASCADE)
    content = models.TextField()
    created_on = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.note.title + " - " + self.content[0:50] + "..."