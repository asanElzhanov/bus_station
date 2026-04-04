"""
Демо-данные для разработки.
python manage.py seed_demo

Включает пример:
  - маршрут с ограниченной остановкой (нет посадки/высадки)
  - маршрут с остановкой только для высадки (транзитная)
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from users.models import User
from transport.models import Transport
from routes.models import Route, Stop


class Command(BaseCommand):
    help = 'Seed demo data'

    def handle(self, *args, **options):
        with transaction.atomic():
            self._users()
            self._transport()
            self._routes()
        self.stdout.write(self.style.SUCCESS('\n✅ Demo data seeded!\n'))
        self.stdout.write('Логины:')
        self.stdout.write('  admin@demo.com   / admin123  (Администратор)')
        self.stdout.write('  manager@demo.com / admin123  (Менеджер)')
        self.stdout.write('  user@demo.com    / admin123  (Пользователь)\n')

    def _users(self):
        specs = [
            dict(email='admin@demo.com',   full_name='Администратор', role=User.Role.ADMIN,   is_staff=True, is_superuser=True),
            dict(email='manager@demo.com', full_name='Менеджер Асель', role=User.Role.MANAGER),
            dict(email='user@demo.com',    full_name='Тест Юзер',     role=User.Role.USER),
        ]
        for s in specs:
            if not User.objects.filter(email=s['email']).exists():
                u = User(**s)
                u.set_password('admin123')
                u.save()
                self.stdout.write(f'  + User {s["email"]}')

    def _transport(self):
        mgr = User.objects.filter(role=User.Role.MANAGER).first()
        t1, c = Transport.objects.get_or_create(
            name='Автобус МАЗ-206',
            defaults={'total_seats': 32, 'layout': Transport.default_layout(8, 4), 'created_by': mgr}
        )
        if c:
            t1.generate_seats()
            self.stdout.write(f'  + Transport {t1.name}')

        t2, c = Transport.objects.get_or_create(
            name='Маршрутка Газель',
            defaults={'total_seats': 13, 'layout': Transport.default_layout(4, 4)[:13], 'created_by': mgr}
        )
        if c:
            t2.generate_seats()
            self.stdout.write(f'  + Transport {t2.name}')

    def _routes(self):
        mgr = User.objects.filter(role=User.Role.MANAGER).first()
        t1  = Transport.objects.filter(name__icontains='МАЗ').first()
        t2  = Transport.objects.filter(name__icontains='Газель').first()
        if not t1:
            self.stdout.write(self.style.WARNING('  Skipping routes — transport not found'))
            return

        # ── Маршрут 1: Астана → Алматы ──────────────────────────────────────
        # Петропавловск — только транзит (нет посадки И нет высадки)
        r1, c = Route.objects.get_or_create(
            name='Астана — Алматы',
            defaults={'transport': t1, 'departure_time': '08:00',
                      'is_approved': True, 'created_by': mgr}
        )
        if c:
            Stop.objects.bulk_create([
                Stop(route=r1, city='Астана',
                     order=0, price_from_start=0,    arrival_offset_minutes=0,
                     is_boarding_allowed=True,  is_alighting_allowed=False),   # нельзя выйти в начале
                Stop(route=r1, city='Кокшетау',
                     order=1, price_from_start=1500, arrival_offset_minutes=120,
                     is_boarding_allowed=True,  is_alighting_allowed=True),
                Stop(route=r1, city='Петропавловск',
                     order=2, price_from_start=2800, arrival_offset_minutes=240,
                     is_boarding_allowed=False, is_alighting_allowed=False),   # транзит, без билетов
                Stop(route=r1, city='Алматы',
                     order=3, price_from_start=4200, arrival_offset_minutes=480,
                     is_boarding_allowed=False, is_alighting_allowed=True),    # нельзя сесть в конце
            ])
            self.stdout.write(f'  + Route {r1.name} (с ограничениями остановок)')

        # ── Маршрут 2: Алматы → Шымкент ─────────────────────────────────────
        # Тараз — только для выхода (нет посадки)
        r2, c = Route.objects.get_or_create(
            name='Алматы — Шымкент',
            defaults={'transport': t2, 'departure_time': '10:00',
                      'is_approved': True, 'created_by': mgr}
        )
        if c:
            Stop.objects.bulk_create([
                Stop(route=r2, city='Алматы',
                     order=0, price_from_start=0,    arrival_offset_minutes=0,
                     is_boarding_allowed=True,  is_alighting_allowed=False),
                Stop(route=r2, city='Тараз',
                     order=1, price_from_start=1800, arrival_offset_minutes=150,
                     is_boarding_allowed=False, is_alighting_allowed=True),    # только выход
                Stop(route=r2, city='Шымкент',
                     order=2, price_from_start=2800, arrival_offset_minutes=300,
                     is_boarding_allowed=False, is_alighting_allowed=True),
            ])
            self.stdout.write(f'  + Route {r2.name} (Тараз — только высадка)')

        # ── Маршрут 3: Астана → Шымкент (ожидает подтверждения) ─────────────
        r3, c = Route.objects.get_or_create(
            name='Астана — Шымкент',
            defaults={'transport': t1, 'departure_time': '07:30',
                      'is_approved': False, 'created_by': mgr}
        )
        if c:
            Stop.objects.bulk_create([
                Stop(route=r3, city='Астана',   order=0, price_from_start=0,
                     is_boarding_allowed=True,  is_alighting_allowed=False),
                Stop(route=r3, city='Балхаш',   order=1, price_from_start=2200, arrival_offset_minutes=200,
                     is_boarding_allowed=True,  is_alighting_allowed=True),
                Stop(route=r3, city='Шымкент',  order=2, price_from_start=5000, arrival_offset_minutes=480,
                     is_boarding_allowed=False, is_alighting_allowed=True),
            ])
            self.stdout.write(f'  + Route {r3.name} (pending)')
