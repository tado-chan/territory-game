# routing.py
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/game/(?P<game_id>\w+)/, consumers.GameConsumer.as_asgi()),
]

# tasks.py (Celery タスク)
from celery import shared_task
import time
from .models import Game

@shared_task
def game_timer_task(game_id):
    """ゲームタイマーを管理するCeleryタスク"""
    try:
        game = Game.objects.get(id=game_id)
        
        while game.status == 'active' and game.remaining_time > 0:
            time.sleep(1)  # 1秒待機
            game.refresh_from_db()
            
            if not game.time_tick():
                break
                
    except Game.DoesNotExist:
        pass

# serializers.py
from rest_framework import serializers
from .models import Game, Spot, Player, GeofenceEntry, YAMANOTE_STATIONS

class SpotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Spot
        fields = ['id', 'name', 'latitude', 'longitude', 'radius', 
                 'required_stay_time', 'owner_team', 'captured_at']

class PlayerSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = Player
        fields = ['id', 'username', 'team', 'current_latitude', 
                 'current_longitude', 'is_online', 'last_seen']

class GameSerializer(serializers.ModelSerializer):
    spots = SpotSerializer(many=True, read_only=True)
    players = PlayerSerializer(many=True, read_only=True)
    
    class Meta:
        model = Game
        fields = ['id', 'name', 'status', 'team_a_score', 'team_b_score', 
                 'winner', 'created_at', 'started_at', 'finished_at',
                 'max_players', 'time_limit', 'remaining_time', 
                 'center_station', 'spots', 'players']

class GameCreateSerializer(serializers.ModelSerializer):
    center_station = serializers.ChoiceField(choices=list(YAMANOTE_STATIONS.keys()))
    
    class Meta:
        model = Game
        fields = ['name', 'center_station']

class GeofenceEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = GeofenceEntry
        fields = ['id', 'spot_id', 'player_id', 'entered_at', 
                 'stay_duration', 'is_captured']