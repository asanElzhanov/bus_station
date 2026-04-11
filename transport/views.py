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


def normalize_layout_seat_numbers(layout):
    """Preserve custom visible seat numbers and assign sequential defaults when missing."""
    normalized = []
    seat_num = 1

    for item in sorted(layout, key=lambda i: (int(i.get('row', 0)), int(i.get('col', 0)))):
        row = int(item.get('row', 0))
        col = int(item.get('col', 0))
        seat_type = item.get('type')
        if row <= 0 or col <= 0 or seat_type is None:
            continue

        normalized_item = {
            'row': row,
            'col': col,
            'type': seat_type,
        }

        if seat_type != 'passage':
            custom_number = str(item.get('seat_number', '')).strip()
            if custom_number:
                normalized_item['seat_number'] = custom_number
            else:
                normalized_item['seat_number'] = str(seat_num)
            seat_num += 1

        normalized.append(normalized_item)

    return normalized


def build_layout_rows(transport, occupied_ids=None):
    occupied_ids = occupied_ids or set()
    seat_map = {
        (seat.position_y, seat.position_x): seat
        for seat in transport.seats.all()
    }

    layout_items = transport.layout or []
    if not layout_items:
        max_row = max([seat.position_y for seat in transport.seats.all()], default=0)
        max_col = max([seat.position_x for seat in transport.seats.all()], default=0)
        layout_items = [
            {'row': r, 'col': c, 'type': 'standard'}
            for r in range(1, max_row + 1)
            for c in range(1, max_col + 1)
            if (r, c) in seat_map
        ]

    sorted_items = sorted(
        layout_items,
        key=lambda item: (int(item.get('row', 0)), int(item.get('col', 0))),
    )

    rows_map = {}
    for item in sorted_items:
        row = int(item.get('row', 0))
        col = int(item.get('col', 0))
        if row <= 0 or col <= 0:
            continue

        if item.get('type') == 'passage':
            rows_map.setdefault(row, []).append({'kind': 'passage', 'col': col})
            continue

        seat = seat_map.get((row, col))
        if not seat:
            continue

        rows_map.setdefault(row, []).append({
            'kind': 'seat',
            'seat': seat,
            'is_occupied': seat.id in occupied_ids,
            'col': col,
        })

    rows = [(row, cells, len(cells)) for row, cells in sorted(rows_map.items())]
    max_slots = max((slot_count for _, _, slot_count in rows), default=1)
    return rows, max_slots


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
            normalized_layout = normalize_layout_seat_numbers(layout)

            seat_numbers = [
                str(item.get('seat_number', '')).strip()
                for item in normalized_layout
                if item.get('type') not in ('passage', None)
            ]
            duplicates = sorted({number for number in seat_numbers if number and seat_numbers.count(number) > 1})
            if duplicates:
                messages.error(
                    request,
                    'Номера мест должны быть уникальными. Повторяются: ' + ', '.join(duplicates)
                )
                return render(request, self.template_name, {'form': form, 'default_layout': layout_json})

            transport.layout = normalized_layout
            transport.total_seats = sum(
                1 for item in normalized_layout if item.get('type') not in ('passage', None)
            )
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
        layout_rows, layout_max_slots = build_layout_rows(transport)
        return render(request, 'transport/detail.html', {
            'transport': transport,
            'seats': seats,
            'layout_rows': layout_rows,
            'layout_max_slots': layout_max_slots,
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
