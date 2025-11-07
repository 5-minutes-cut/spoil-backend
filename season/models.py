from django.db import models
from series.models import Series

# Create your models here.
class Season(models.Model):
    series = models.ForeignKey(
        Series,
        on_delete=models.CASCADE,
        related_name="seasons",
    )
    season_number = models.PositiveIntegerField()

    class Meta:
        unique_together = ("series", "season_number")
        ordering = ["series", "season_number"]

    def __str__(self):
        return f"{self.series.title} - Season {self.season_number}"