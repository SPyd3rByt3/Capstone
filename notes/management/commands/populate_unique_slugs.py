from django.core.management.base import BaseCommand
from notes.models import Note
from django.utils.text import slugify

class Command(BaseCommand):
    help = 'Populate unique slugs for existing notes'

    def handle(self, *args, **kwargs):
        notes = Note.objects.all()
        for note in notes:
            if not note.slug:
                base_slug = slugify(note.title)
                slug = base_slug
                counter = 1
                while Note.objects.filter(slug=slug).exclude(pk=note.pk).exists():
                    slug = f"{base_slug}-{counter}"
                    counter += 1
                note.slug = slug
                note.save()
                self.stdout.write(self.style.SUCCESS(f'Slug set for note "{note.title}": {note.slug}'))
            else:
                self.stdout.write(f'Slug already set for note "{note.title}": {note.slug}')
