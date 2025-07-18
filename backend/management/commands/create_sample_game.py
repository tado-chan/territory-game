# management/commands/create_sample_game.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from your_app.models import Game, Player

class Command(BaseCommand):
    help = 'サンプルゲームを作成'

    def add_arguments(self, parser):
        parser.add_argument('--station', type=str, default='渋谷', help='中心駅名')
        parser.add_argument('--name', type=str, default='テストゲーム', help='ゲーム名')

    def handle(self, *args, **options):
        # サンプルユーザーを作成
        user1, created = User.objects.get_or_create(
            username='testuser1',
            defaults={'email': 'test1@example.com'}
        )
        if created:
            user1.set_password('password123')
            user1.save()

        user2, created = User.objects.get_or_create(
            username='testuser2',
            defaults={'email': 'test2@example.com'}
        )
        if created:
            user2.set_password('password123')
            user2.save()

        # ゲームを作成
        game = Game.objects.create(
            name=options['name'],
            center_station=options['station']
        )

        # プレイヤーを追加
        Player.objects.create(user=user1, game=game, team='team_a')
        Player.objects.create(user=user2, game=game, team='team_b')

        self.stdout.write(
            self.style.SUCCESS(
                f'ゲーム "{game.name}" (ID: {game.id}) を作成しました'
            )
        )
