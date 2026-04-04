# 🚌 АвтоВокзал — Django Bus Station Management System

Production-ready система управления автовокзалом на Django.

---

## 📦 Структура проекта

```
bus_station/
├── config/                  # Настройки Django
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── users/                   # Пользователи и роли
│   ├── models.py            # Кастомный User (admin/manager/user)
│   ├── views.py             # Login, Register, Profile
│   ├── permissions.py       # AdminRequiredMixin, ManagerRequiredMixin
│   └── management/commands/seed_demo.py
├── transport/               # Транспортные средства
│   ├── models.py            # Transport + Seat (JSON layout)
│   └── views.py             # Конструктор сидений
├── routes/                  # Маршруты
│   ├── models.py            # Route с approval workflow
│   ├── views.py             # Public + Manager + Admin views
│   ├── api_views.py         # DRF API endpoints
│   └── serializers.py
├── bookings/                # Бронирования
│   ├── models.py            # Booking (уникальность: route+seat+date)
│   ├── views.py             # Atomic booking creation
│   └── api_views.py
├── payments/                # Платежи (mock)
│   ├── models.py
│   └── views.py
├── templates/               # Все HTML шаблоны
│   ├── base.html
│   ├── routes/
│   ├── transport/
│   ├── bookings/
│   ├── payments/
│   └── users/
└── fixtures/
    └── initial_data.json
```

---

## 🚀 Быстрый старт

### 1. Установка зависимостей

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Настройка окружения

```bash
cp .env.example .env
# Отредактируйте .env при необходимости
```

### 3. Миграции

```bash
python manage.py makemigrations users transport routes bookings payments
python manage.py migrate
```

### 4. Создание демо-данных

```bash
python manage.py seed_demo
```

Создаёт пользователей:
| Email | Пароль | Роль |
|-------|--------|------|
| admin@demo.com | admin123 | Администратор |
| manager@demo.com | admin123 | Менеджер |
| user@demo.com | admin123 | Пользователь |

А также 2 транспортных средства и 4 маршрута.

### 5. Запуск

```bash
python manage.py runserver
```

Открыть: http://127.0.0.1:8000

---

## 🗄️ Модели и связи

```
User ──────────────────────────┐
  role: admin/manager/user     │
                               │
Transport ────────────────┐   │ created_by
  name, total_seats       │   │
  layout (JSON)           │   │
  seats ──> Seat[]        │   │
                          │   │
Route ────────────────────┘   │
  from_city, to_city           │
  departure_time, price        │
  transport (FK)               │
  is_approved                  │ created_by
                               ▼
Booking ─────────────────────────
  route (FK)
  seat (FK)
  travel_date
  customer_name, phone
  status: booked/paid/cancelled
  unique_together: (route, seat, travel_date)
       │
       ▼
Payment
  booking (OneToOne)
  amount, status
  transaction_id
```

---

## 🔑 Роли и права доступа

| Действие | Guest | User | Manager | Admin |
|----------|-------|------|---------|-------|
| Просмотр маршрутов | ✅ | ✅ | ✅ | ✅ |
| Бронирование мест | ✅ | ✅ | ✅ | ✅ |
| Создание транспорта | ❌ | ❌ | ✅ | ✅ |
| Создание маршрутов | ❌ | ❌ | ✅ | ✅ |
| Просмотр бронирований | ❌ | ❌ | ✅ (свои) | ✅ (все) |
| Подтверждение маршрутов | ❌ | ❌ | ❌ | ✅ |
| Управление пользователями | ❌ | ❌ | ❌ | ✅ |

---

## 🌐 URL маршруты

### Публичные
- `GET /routes/` — список маршрутов (с поиском по городам)
- `GET /routes/<pk>/` — детали маршрута + схема мест + выбор даты
- `POST /bookings/create/<route_pk>/seat/<seat_pk>/` — создать бронь
- `GET /payments/checkout/<booking_pk>/` — страница оплаты
- `POST /payments/process/<booking_pk>/` — обработать платёж

### Менеджер
- `GET/POST /routes/create/` — создать маршрут
- `GET /routes/manage/` — список своих маршрутов
- `GET /transport/` — транспорт
- `GET /bookings/` — бронирования

### Администратор
- `POST /routes/<pk>/approve/` — подтвердить маршрут
- `POST /routes/<pk>/reject/` — отклонить маршрут
- `/admin/` — Django Admin (полный доступ)

### REST API
- `GET /api/routes/` — список маршрутов (JSON)
- `GET /api/routes/<pk>/` — детали маршрута
- `GET /api/bookings/seats/<route_pk>/<YYYY-MM-DD>/` — занятые места
- `POST /api/bookings/create/` — создать бронь через API

---

## 🎯 Бизнес-логика

### Бронирование (транзакционное)
```python
with transaction.atomic():
    # select_for_update предотвращает race conditions
    conflict = Booking.objects.select_for_update().filter(
        route=route, seat=seat, travel_date=date,
        status__in=['booked', 'paid']
    ).exists()
    if conflict:
        raise IntegrityError()  # Место уже занято
    booking = Booking.objects.create(...)
```

### Схема сидений (JSON)
```json
[
  {"seat_number": "1", "row": 1, "col": 1, "type": "window"},
  {"seat_number": "2", "row": 1, "col": 2, "type": "aisle"},
  ...
]
```

### Генерация стандартной схемы
```python
layout = Transport.default_layout(rows=8, cols=4)  # 32-местный автобус
transport.layout = layout
transport.generate_seats()  # Создаёт объекты Seat в БД
```

---

## 🔧 Конфигурация PostgreSQL

В `.env`:
```
DATABASE_URL=postgresql://myuser:mypassword@localhost:5432/bus_station
```

Или создать БД вручную:
```sql
CREATE DATABASE bus_station;
CREATE USER bus_user WITH PASSWORD 'secret';
GRANT ALL PRIVILEGES ON DATABASE bus_station TO bus_user;
```

---

## 📝 Примеры использования API

### Получить маршруты
```bash
curl http://localhost:8000/api/routes/
```

### Проверить занятые места
```bash
curl http://localhost:8000/api/bookings/seats/1/2025-06-15/
# Response: {"occupied_seat_ids": [3, 7, 12], "date": "2025-06-15"}
```

### Создать бронь через API
```bash
curl -X POST http://localhost:8000/api/bookings/create/ \
  -H "Content-Type: application/json" \
  -d '{
    "route": 1,
    "seat": 5,
    "travel_date": "2025-06-15",
    "customer_name": "Иван Иванов",
    "phone": "+7 777 123 45 67"
  }'
```
