from django.db import models

class Game(models.Model):
    name = models.CharField(max_length=200)
    center_station = models.CharField(max_length=50)
    status = models.CharField(max_length=20, default='waiting')
    team_a_score = models.IntegerField(default=0)
    team_b_score = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
