from rest_framework import serializers
from .models import Season

class SeasonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Season
        fields = ['id', 'series', 'season_number']
        read_only_fields = ['id']