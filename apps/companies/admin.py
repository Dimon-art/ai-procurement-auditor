from django.contrib import admin

from .models import Company


# Admin display labels only (no model Meta / no migrations).
Company._meta.verbose_name = "Компания"
Company._meta.verbose_name_plural = "Компании"

admin.site.register(Company)
