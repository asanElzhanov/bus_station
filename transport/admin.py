from django.contrib import admin
from .models import Transport, Seat

class SeatInline(admin.TabularInline):
    model = Seat
    extra = 0
    readonly_fields = ('seat_number', 'position_x', 'position_y', 'seat_type')

@admin.register(Transport)
class TransportAdmin(admin.ModelAdmin):
    list_display = ('name', 'total_seats', 'created_by', 'created_at')
    inlines = [SeatInline]

@admin.register(Seat)
class SeatAdmin(admin.ModelAdmin):
    list_display = ('seat_number', 'transport', 'position_x', 'position_y', 'seat_type')
    list_filter = ('transport', 'seat_type')
