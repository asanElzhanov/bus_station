"""
Утилиты для работы с куки гостевых билетов.

Схема:
    - При каждом создании гостевой брони её UUID cookie_token добавляется
        в куки браузера (список токенов, JSON, TTL=7 дней).
    - Для авторизованных пользователей брони сохраняются на аккаунт,
        а куки не используются.
    - При просмотре «Мои билеты» гостя читаем список токенов из куки
        и делаем Booking.objects.filter(cookie_token__in=tokens).
  - Каждый раз при чтении куки TTL сбрасывается на 7 дней заново.
"""

import json
from datetime import datetime, timedelta, timezone

COOKIE_NAME = 'guest_booking_tokens'
COOKIE_MAX_AGE = 7 * 24 * 60 * 60  # 7 дней в секундах


def get_guest_tokens(request) -> list[str]:
    """Читает список UUID-строк из куки."""
    raw = request.COOKIES.get(COOKIE_NAME, '[]')
    try:
        tokens = json.loads(raw)
        if isinstance(tokens, list):
            return [str(t) for t in tokens]
    except (json.JSONDecodeError, TypeError):
        pass
    return []


def add_guest_token(response, existing_tokens: list[str], new_token: str) -> None:
    """
    Добавляет новый токен в куки и сбрасывает TTL на 7 дней.
    existing_tokens — текущий список (из get_guest_tokens).
    Дубликаты игнорируются. Список не растёт бесконечно — хранит последние 50.
    """
    tokens = list(dict.fromkeys(existing_tokens + [str(new_token)]))  # dedup
    tokens = tokens[-50:]  # ограничение на размер
    response.set_cookie(
        COOKIE_NAME,
        json.dumps(tokens),
        max_age=COOKIE_MAX_AGE,
        httponly=True,
        samesite='Lax',
    )


def refresh_guest_tokens(response, tokens: list[str]) -> None:
    """Обновляет TTL существующего списка (сбрасывает на 7 дней)."""
    if not tokens:
        return
    response.set_cookie(
        COOKIE_NAME,
        json.dumps(tokens),
        max_age=COOKIE_MAX_AGE,
        httponly=True,
        samesite='Lax',
    )
