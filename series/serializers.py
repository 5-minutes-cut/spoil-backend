from rest_framework import serializers
from .models import Series
from genre.models import Genre

class SeriesSerializer(serializers.ModelSerializer):
    genres = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Genre.objects.all(),
        required=False
    )

    class Meta:
        model = Series
        fields = ['id', 'title', 'photo', 'description', 'genres']