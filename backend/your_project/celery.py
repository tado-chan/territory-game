# celery.py
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'your_project.settings')

app = Celery('your_project')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# __init__.py (プロジェクトルート)
from .celery import app as celery_app

__all__ = ('celery_app',)

# admin.py
from django.contrib import admin
from .models import Game, Spot, Player, GeofenceEntry

@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ['name', 'status', 'team_a_score', 'team_b_score', 
                   'center_station', 'created_at', 'started_at']
    list_filter = ['status', 'center_station', 'created_at']
    search_fields = ['name']
    readonly_fields = ['created_at', 'started_at', 'finished_at']

@admin.register(Spot)
class SpotAdmin(admin.ModelAdmin):
    list_display = ['name', 'game', 'owner_team', 'latitude', 'longitude', 'captured_at']
    list_filter = ['owner_team', 'game__status']
    search_fields = ['name', 'game__name']

@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ['user', 'game', 'team', 'is_online', 'joined_at', 'last_seen']
    list_filter = ['team', 'is_online', 'game__status']
    search_fields = ['user__username', 'game__name']

@admin.register(GeofenceEntry)
class GeofenceEntryAdmin(admin.ModelAdmin):
    list_display = ['player', 'spot', 'stay_duration', 'is_captured', 'entered_at']
    list_filter = ['is_captured', 'spot__owner_team']
    search_fields = ['player__user__username', 'spot__name']