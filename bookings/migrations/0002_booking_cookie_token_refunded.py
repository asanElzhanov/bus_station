import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0001_initial'),
    ]

    operations = [
        # Добавляем cookie_token — уникальный UUID для каждой брони
        migrations.AddField(
            model_name='booking',
            name='cookie_token',
            field=models.UUIDField(
                default=uuid.uuid4,
                unique=True,
                db_index=True,
                verbose_name='Токен куки',
            ),
        ),
        # Добавляем статус 'refunded'
        migrations.AlterField(
            model_name='booking',
            name='status',
            field=models.CharField(
                choices=[
                    ('booked',    'Забронировано'),
                    ('paid',      'Оплачено'),
                    ('cancelled', 'Отменено'),
                    ('refunded',  'Возвращён'),
                ],
                default='booked',
                max_length=15,
                verbose_name='Статус',
            ),
        ),
    ]
