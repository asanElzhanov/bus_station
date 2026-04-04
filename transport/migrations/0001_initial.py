from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Transport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Название')),
                ('total_seats', models.PositiveIntegerField(verbose_name='Количество мест')),
                ('layout', models.JSONField(default=list, verbose_name='Схема сидений')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='transports',
                    to='users.user',
                    verbose_name='Создан менеджером'
                )),
            ],
            options={
                'verbose_name': 'Транспорт',
                'verbose_name_plural': 'Транспорт',
            },
        ),
        migrations.CreateModel(
            name='Seat',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('seat_number', models.CharField(max_length=10, verbose_name='Номер места')),
                ('position_x', models.PositiveIntegerField(verbose_name='Колонка (X)')),
                ('position_y', models.PositiveIntegerField(verbose_name='Ряд (Y)')),
                ('seat_type', models.CharField(
                    choices=[('window', 'У окна'), ('aisle', 'У прохода'), ('standard', 'Стандартное')],
                    default='standard', max_length=20, verbose_name='Тип места'
                )),
                ('transport', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='seats',
                    to='transport.transport',
                    verbose_name='Транспорт'
                )),
            ],
            options={
                'verbose_name': 'Место',
                'verbose_name_plural': 'Места',
                'ordering': ['position_y', 'position_x'],
            },
        ),
        migrations.AlterUniqueTogether(
            name='seat',
            unique_together={('transport', 'seat_number')},
        ),
    ]
