from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site

class Command(BaseCommand):
    help = 'Add default site to the sites framework'

    def handle(self, *args, **options):
        site_domain = 'localhost:8000'
        site_name = 'localhost'
        if not Site.objects.filter(domain=site_domain).exists():
            Site.objects.create(domain=site_domain, name=site_name)
            self.stdout.write(self.style.SUCCESS(f'Successfully created site {site_domain}'))
        else:
            self.stdout.write(self.style.WARNING(f'Site {site_domain} already exists'))
