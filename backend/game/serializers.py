from rest_framework import serializers
from .models import Game

class GameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Game
        fields = ['id', 'name', 'center_station', 'status', 'team_a_score', 'team_b_score', 'created_at']
