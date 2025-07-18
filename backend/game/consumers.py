# consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from .models import Game, Player, Spot, GeofenceEntry

class GameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.game_id = self.scope['url_route']['kwargs']['game_id']
        self.game_group_name = f'game_{self.game_id}'
        
        # グループに参加
        await self.channel_layer.group_add(
            self.game_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # ゲーム情報を送信
        game_data = await self.get_game_data()
        await self.send(text_data=json.dumps({
            'type': 'game_update',
            'data': game_data
        }))

    async def disconnect(self, close_code):
        # グループから退出
        await self.channel_layer.group_discard(
            self.game_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        """クライアントからのメッセージを受信"""
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type')
            
            if message_type == 'player_position':
                await self.handle_player_position(text_data_json)
            elif message_type == 'geofence_check':
                await self.handle_geofence_check(text_data_json)
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON'
            }))

    async def handle_player_position(self, data):
        """プレイヤー位置更新処理"""
        try:
            latitude = data.get('latitude')
            longitude = data.get('longitude')
            user_id = self.scope['user'].id
            
            await self.update_player_position(user_id, latitude, longitude)
            
            # グループ内の他のプレイヤーに位置更新を通知
            await self.channel_layer.group_send(
                self.game_group_name,
                {
                    'type': 'player_position_update',
                    'user_id': user_id,
                    'latitude': latitude,
                    'longitude': longitude
                }
            )
            
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e)
            }))

    async def handle_geofence_check(self, data):
        """ジオフェンスチェック処理"""
        try:
            spot_id = data.get('spot_id')
            user_id = self.scope['user'].id
            
            result = await self.check_geofence(user_id, spot_id)
            
            await self.send(text_data=json.dumps({
                'type': 'geofence_result',
                'data': result
            }))
            
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e)
            }))

    # WebSocketイベントハンドラー
    async def game_update(self, event):
        """ゲーム状態更新"""
        await self.send(text_data=json.dumps({
            'type': 'game_update',
            'data': event['data']
        }))

    async def player_joined(self, event):
        """プレイヤー参加通知"""
        await self.send(text_data=json.dumps({
            'type': 'player_joined',
            'data': event['player_data']
        }))

    async def player_left(self, event):
        """プレイヤー退出通知"""
        await self.send(text_data=json.dumps({
            'type': 'player_left',
            'data': {'player_id': event['player_id']}
        }))

    async def spot_captured(self, event):
        """スポット取得通知"""
        await self.send(text_data=json.dumps({
            'type': 'spot_captured',
            'data': {
                'spot_id': event['spot_id'],
                'team': event['team'],
                'player': event['player'],
                'captured_at': event['captured_at'],
                'team_a_score': event['team_a_score'],
                'team_b_score': event['team_b_score']
            }
        }))

    async def game_timer(self, event):
        """ゲームタイマー更新"""
        await self.send(text_data=json.dumps({
            'type': 'game_timer',
            'data': {'remaining_time': event['remaining_time']}
        }))

    async def game_finished(self, event):
        """ゲーム終了通知"""
        await self.send(text_data=json.dumps({
            'type': 'game_finished',
            'data': {
                'winner': event['winner'],
                'finished_at': event['finished_at']
            }
        }))

    async def player_position_update(self, event):
        """プレイヤー位置更新通知"""
        await self.send(text_data=json.dumps({
            'type': 'player_position_update',
            'data': {
                'user_id': event['user_id'],
                'latitude': event['latitude'],
                'longitude': event['longitude']
            }
        }))

    # データベース操作（同期→非同期変換）
    @database_sync_to_async
    def get_game_data(self):
        try:
            game = Game.objects.get(id=self.game_id)
            return {
                'id': game.id,
                'name': game.name,
                'status': game.status,
                'team_a_score': game.team_a_score,
                'team_b_score': game.team_b_score,
                'remaining_time': game.remaining_time,
                'center_station': game.center_station,
                'spots': [
                    {
                        'id': spot.id,
                        'name': spot.name,
                        'latitude': spot.latitude,
                        'longitude': spot.longitude,
                        'radius': spot.radius,
                        'required_stay_time': spot.required_stay_time,
                        'owner_team': spot.owner_team,
                        'captured_at': spot.captured_at.isoformat() if spot.captured_at else None
                    }
                    for spot in game.spots.all()
                ],
                'players': [
                    {
                        'id': player.id,
                        'username': player.user.username,
                        'team': player.team,
                        'current_latitude': player.current_latitude,
                        'current_longitude': player.current_longitude,
                        'is_online': player.is_online,
                        'last_seen': player.last_seen.isoformat()
                    }
                    for player in game.players.all()
                ]
            }
        except Game.DoesNotExist:
            return None

    @database_sync_to_async
    def update_player_position(self, user_id, latitude, longitude):
        try:
            player = Player.objects.get(user_id=user_id, game_id=self.game_id)
            player.current_latitude = latitude
            player.current_longitude = longitude
            player.save()
            return True
        except Player.DoesNotExist:
            return False

    @database_sync_to_async
    def check_geofence(self, user_id, spot_id):
        try:
            player = Player.objects.get(user_id=user_id, game_id=self.game_id)
            spot = Spot.objects.get(id=spot_id, game_id=self.game_id)
            
            if not player.current_latitude or not player.current_longitude:
                return None
                
            # 距離をチェック
            if spot.is_within_radius(player.current_latitude, player.current_longitude):
                # ジオフェンスエントリーを作成または更新
                entry, created = GeofenceEntry.objects.get_or_create(
                    player=player,
                    spot=spot,
                    defaults={'stay_duration': 0}
                )
                
                if not created:
                    # 既存エントリーの滞在時間を更新
                    entry.update_stay_duration()
                    
                # キャプチャ条件をチェック
                entry.check_capture()
                
                return {
                    'id': entry.id,
                    'spot_id': spot.id,
                    'player_id': player.id,
                    'entered_at': entry.entered_at.isoformat(),
                    'stay_duration': entry.stay_duration,
                    'is_captured': entry.is_captured,
                    'required_time': spot.required_stay_time
                }
            else:
                # スポット外の場合、エントリーを削除
                GeofenceEntry.objects.filter(player=player, spot=spot).delete()
                return None
                
        except (Player.DoesNotExist, Spot.DoesNotExist):
            return None
