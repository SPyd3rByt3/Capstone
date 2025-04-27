from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from notes.models import Note 
 #import your models


class StaticViewSitemap(Sitemap):
    priority = 0.5
    changefreq = 'weekly'

    def item(self):
        return ['home', 'about', 'projects', 'notes_list', 'notes_create', 'base', 'contact', 'navbar', 'content_projects_list' ]
    
    def location(self, item):
        return reverse(item)
    
class NotesSitemap(Sitemap):
    changefrq = 'daily'
    priority = 0.7

    def items(self):
        return Note.objects.all()
    
    def lastmod(self, obj):
        return obj.updated_at     # Assuming your model has this field
    
    # If your model has a get_absolute_url method, location is automatic
    # Otherwise, define it:
    # def location(self, obj):
    #     return reverse('note_detail', args=[obj.id])
