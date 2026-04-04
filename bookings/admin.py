from django.contrib import admin
from .models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display  = ('id', 'route', 'from_stop', 'to_stop', 'seat',
                     'travel_date', 'customer_name', 'phone', 'status',
                     'price', 'created_at')
    list_filter   = ('status', 'travel_date', 'route')
    search_fields = ('customer_name', 'phone', 'cookie_token')
    date_hierarchy = 'travel_date'
    list_editable  = ('status',)
    readonly_fields = ('created_at', 'cookie_token')
    fieldsets = (
        (None, {
            'fields': ('route', 'seat', 'from_stop', 'to_stop',
                       'travel_date', 'status', 'price')
        }),
        ('Клиент', {
            'fields': ('customer_name', 'phone', 'extra_info')
        }),
        ('Системное', {
            'fields': ('cookie_token', 'created_at'),
            'classes': ('collapse',),
        }),
    )
