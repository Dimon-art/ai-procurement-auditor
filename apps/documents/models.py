from django.db import models
from apps.companies.models import Company


class Document(models.Model):
    title = models.CharField(max_length=255)

    def __str__(self):
        return self.title


