from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Game
from .serializers import GameSerializer

class GameViewSet(viewsets.ModelViewSet):
    queryset = Game.objects.all()
    serializer_class = GameSerializer
    
    def create(self, request):
        name = request.data.get('name')
        center_station = request.data.get('center_station')
        
        if not name or not center_station:
            return Response(
                {'error': 'name and center_station are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        game = Game.objects.create(
            name=name,
            center_station=center_station
        )
        
        serializer = GameSerializer(game)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def available(self, request):
        games = Game.objects.filter(status='waiting')
        serializer = GameSerializer(games, many=True)
        return Response(serializer.data)
