"""
Views for transport management (manager/admin only).
"""

import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views import View

from users.permissions import ManagerRequiredMixin
from .models import Transport, Seat
from .forms import TransportForm


class TransportListView(ManagerRequiredMixin, View):
    def get(self, request):
        if request.user.is_admin:
            transports = Transport.objects.all().order_by('-created_at')
        else:
            transports = Transport.objects.filter(created_by=request.user).order_by('-created_at')
        return render(request, 'transport/list.html', {'transports': transports})


class TransportCreateView(ManagerRequiredMixin, View):
    template_name = 'transport/create.html'

    def get(self, request):
        form = TransportForm()
        # Provide a default 4x8 layout as example
        default_layout = json.dumps(Transport.default_layout(rows=8, cols=4), ensure_ascii=False)
        return render(request, self.template_name, {'form': form, 'default_layout': default_layout})

    def post(self, request):
        form = TransportForm(request.POST)
        layout_json = request.POST.get('layout_json', '[]')

        try:
            layout = json.loads(layout_json)
        except json.JSONDecodeError:
            messages.error(request, 'Неверный формат схемы сидений')
            return render(request, self.template_name, {'form': form})

        if form.is_valid():
            transport = form.save(commit=False)
            transport.created_by = request.user
            transport.layout = layout
            transport.total_seats = len(layout)
            transport.save()
            # Generate individual Seat objects from layout
            transport.generate_seats()
            messages.success(request, f'Транспорт "{transport.name}" создан с {transport.total_seats} местами.')
            return redirect('transport:list')

        return render(request, self.template_name, {'form': form, 'default_layout': layout_json})


class TransportDetailView(ManagerRequiredMixin, View):
    def get(self, request, pk):
        transport = get_object_or_404(Transport, pk=pk)
        seats = transport.seats.all()
        return render(request, 'transport/detail.html', {
            'transport': transport,
            'seats': seats,
        })


class TransportDeleteView(ManagerRequiredMixin, View):
    def post(self, request, pk):
        transport = get_object_or_404(Transport, pk=pk)
        if not request.user.is_admin and transport.created_by != request.user:
            messages.error(request, 'Нет прав для удаления.')
            return redirect('transport:list')
        transport.delete()
        messages.success(request, 'Транспорт удалён.')
        return redirect('transport:list')
