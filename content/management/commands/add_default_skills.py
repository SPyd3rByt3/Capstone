from django.core.management.base import BaseCommand
from content.models import Skill

class Command(BaseCommand):
    help = 'Add default skills to the database'

    def handle(self, *args, **kwargs):
        default_skills = ['Python', 'Django', 'JavaScript', 'React', 'CSS', 'HTML']
        for skill_name in default_skills:
            skill, created = Skill.objects.get_or_create(name=skill_name)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Skill "{skill_name}" created.'))
            else:
                self.stdout.write(f'Skill "{skill_name}" already exists.')
