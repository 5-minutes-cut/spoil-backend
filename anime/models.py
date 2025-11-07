from django.db import models


class Anime(models.Model):
	title = models.CharField(max_length=255)

	class Meta:
		db_table = 'anime'

	def __str__(self):
		return self.title
