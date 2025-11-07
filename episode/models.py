from django.db import models
from season.models import Season

# Create your models here.
class Episode(models.Model):
    season = models.ForeignKey( Season, on_delete=models.CASCADE, related_name="episodes",)
    episode_number = models.PositiveIntegerField()
    episode_title = models.CharField(max_length=255)
    content = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ("season", "episode_number")
        ordering = ["season", "episode_number"]

    def __str__(self):
        return f"{self.season.series.title} S{self.season.season_number}E{self.episode_number}"