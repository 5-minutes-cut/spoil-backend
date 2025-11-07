from django.db import models
from genre.models import Genre

# Create your models here.
class Series(models.Model):
    title = models.CharField(max_length=255)  # NOT NULL
    photo = models.ImageField(
        upload_to="series_photos/",
        blank=True,
        null=True,
    )
    description = models.TextField(blank=True, null=True)
    genres = models.ManyToManyField( Genre, blank=True, related_name="series")

    def __str__(self):
        return self.title