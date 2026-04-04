from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('routes', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='stop',
            name='is_boarding_allowed',
            field=models.BooleanField(
                default=True,
                verbose_name='Посадка разрешена',
                help_text='Можно ли купить билет ОТ этой остановки'
            ),
        ),
        migrations.AddField(
            model_name='stop',
            name='is_alighting_allowed',
            field=models.BooleanField(
                default=True,
                verbose_name='Высадка разрешена',
                help_text='Можно ли купить билет ДО этой остановки'
            ),
        ),
    ]
