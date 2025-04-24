from django.contrib.sitemaps import Sitemap
from django.urls import reverse

class StaticViewSitemap(Sitemap):
    priority = 0.5
    changefreq = 'weekly'

    def item(self):
        return ['home', 'about', 'projects', 'notes_list', 'notes_create', 'base', 'contact', 'navbar', 'content_projects_list' ]
    