from django.contrib import admin
from .models import Note

class NoteAdmin(admin.ModelAdmin):
    list_display = ('title', 'link_url', 'created_on')
    fields = ('title', 'content', 'image', 'link_url', 'slug')

admin.site.register(Note, NoteAdmin)
