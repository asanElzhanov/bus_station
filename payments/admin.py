from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'booking', 'amount', 'status', 'transaction_id', 'created_at', 'paid_at')
    list_filter = ('status',)
    search_fields = ('transaction_id', 'booking__customer_name')
    readonly_fields = ('created_at', 'paid_at', 'transaction_id')
