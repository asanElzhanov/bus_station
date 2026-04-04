from django.contrib import admin
from .models import Route, Stop


class StopInline(admin.TabularInline):
    model   = Stop
    extra   = 2
    fields  = ('order', 'city', 'price_from_start', 'arrival_offset_minutes',
               'is_boarding_allowed', 'is_alighting_allowed')
    ordering = ('order',)


@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display  = ('name', 'departure_time', 'transport', 'is_approved', 'created_by')
    list_filter   = ('is_approved',)
    search_fields = ('name',)
    list_editable = ('is_approved',)
    inlines       = [StopInline]
    actions       = ['approve', 'reject']

    @admin.action(description='Подтвердить маршруты')
    def approve(self, request, qs):
        qs.update(is_approved=True)

    @admin.action(description='Отклонить маршруты')
    def reject(self, request, qs):
        qs.update(is_approved=False)


@admin.register(Stop)
class StopAdmin(admin.ModelAdmin):
    list_display  = ('city', 'route', 'order', 'price_from_start',
                     'is_boarding_allowed', 'is_alighting_allowed')
    list_filter   = ('route', 'is_boarding_allowed', 'is_alighting_allowed')
    list_editable = ('is_boarding_allowed', 'is_alighting_allowed')
    ordering      = ('route', 'order')
