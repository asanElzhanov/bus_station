from datetime import date
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.forms import inlineformset_factory
from django.views import View

from users.permissions import ManagerRequiredMixin, AdminRequiredMixin
from bookings.views import get_occupied_seat_ids
from .models import Route, Stop
from .forms import RouteForm, StopForm


class RouteListView(View):
    def get(self, request):
        routes = Route.objects.filter(is_approved=True).prefetch_related('stops')
        search_from = request.GET.get('from_city', '').strip()
        search_to   = request.GET.get('to_city', '').strip()
        if search_from:
            routes = routes.filter(stops__city__icontains=search_from).distinct()
        if search_to:
            routes = routes.filter(stops__city__icontains=search_to).distinct()
        cities = sorted(set(
            Stop.objects.filter(route__is_approved=True).values_list('city', flat=True)
        ))
        return render(request, 'routes/list.html', {
            'routes': routes, 'cities': cities,
            'search_from': search_from, 'search_to': search_to,
        })


class RouteDetailView(View):
    def get(self, request, pk):
        route = get_object_or_404(Route, pk=pk, is_approved=True)
        all_stops = list(route.stops.order_by('order'))

        today         = str(date.today())
        selected_date = request.GET.get('date', today)
        from_stop_pk  = request.GET.get('from_stop', '')
        to_stop_pk    = request.GET.get('to_stop', '')

        # Остановки доступные для выбора пользователем
        boarding_stops   = [s for s in all_stops if s.is_boarding_allowed]
        alighting_stops  = [s for s in all_stops if s.is_alighting_allowed]

        from_stop = to_stop = None
        if from_stop_pk and to_stop_pk:
            try:
                from_stop = route.stops.get(pk=from_stop_pk)
                to_stop   = route.stops.get(pk=to_stop_pk)
                if from_stop.order >= to_stop.order:
                    from_stop = to_stop = None
                    messages.error(request, 'Посадка должна быть раньше высадки.')
                elif not from_stop.is_boarding_allowed:
                    messages.error(request, f'Посадка в «{from_stop.city}» недоступна.')
                    from_stop = to_stop = None
                elif not to_stop.is_alighting_allowed:
                    messages.error(request, f'Высадка в «{to_stop.city}» недоступна.')
                    from_stop = to_stop = None
            except Stop.DoesNotExist:
                pass

        occupied_ids  = set()
        segment_price = None
        if from_stop and to_stop:
            try:
                date_obj = date.fromisoformat(selected_date)
            except ValueError:
                date_obj = date.today()
                selected_date = str(date_obj)
            occupied_ids  = get_occupied_seat_ids(route, date_obj, from_stop, to_stop)
            segment_price = route.segment_price(from_stop, to_stop)

        seats = route.transport.seats.all()
        for seat in seats:
            seat.is_occupied = seat.id in occupied_ids

        grid = {}
        for seat in seats:
            grid.setdefault(seat.position_y, {})[seat.position_x] = seat
        grid_rows = sorted(grid.items())

        return render(request, 'routes/detail.html', {
            'route': route,
            'all_stops': all_stops,
            'boarding_stops': boarding_stops,
            'alighting_stops': alighting_stops,
            'selected_date': selected_date,
            'today': today,
            'from_stop': from_stop,
            'to_stop': to_stop,
            'segment_price': segment_price,
            'grid_rows': grid_rows,
            'segment_selected': bool(from_stop and to_stop),
        })


StopFormSet = inlineformset_factory(
    Route, Stop, form=StopForm,
    extra=3, can_delete=True, min_num=2, validate_min=True,
)


class ManagerRouteListView(ManagerRequiredMixin, View):
    def get(self, request):
        qs = Route.objects.prefetch_related('stops').all()
        if not request.user.is_admin:
            qs = qs.filter(created_by=request.user)
        return render(request, 'routes/manager_list.html', {'routes': qs})


class RouteCreateView(ManagerRequiredMixin, View):
    template_name = 'routes/form.html'
    def get(self, request):
        return render(request, self.template_name, {
            'form': RouteForm(), 'formset': StopFormSet(), 'action': 'Создать'
        })
    def post(self, request):
        form    = RouteForm(request.POST)
        formset = StopFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            route = form.save(commit=False)
            route.created_by  = request.user
            route.is_approved = False
            route.save()
            formset.instance = route
            formset.save()
            messages.success(request, 'Маршрут создан и ожидает подтверждения.')
            return redirect('routes:manager_list')
        return render(request, self.template_name, {
            'form': form, 'formset': formset, 'action': 'Создать'
        })


class RouteEditView(ManagerRequiredMixin, View):
    template_name = 'routes/form.html'
    def _check(self, request, route):
        if not request.user.is_admin and route.created_by != request.user:
            messages.error(request, 'Нет прав.')
            return False
        return True
    def get(self, request, pk):
        route = get_object_or_404(Route, pk=pk)
        if not self._check(request, route): return redirect('routes:manager_list')
        return render(request, self.template_name, {
            'form': RouteForm(instance=route),
            'formset': StopFormSet(instance=route),
            'action': 'Сохранить', 'route': route,
        })
    def post(self, request, pk):
        route = get_object_or_404(Route, pk=pk)
        if not self._check(request, route): return redirect('routes:manager_list')
        form    = RouteForm(request.POST, instance=route)
        formset = StopFormSet(request.POST, instance=route)
        if form.is_valid() and formset.is_valid():
            r = form.save(commit=False)
            r.is_approved = False
            r.save()
            formset.save()
            messages.success(request, 'Маршрут обновлён и отправлен на подтверждение.')
            return redirect('routes:manager_list')
        return render(request, self.template_name, {
            'form': form, 'formset': formset, 'action': 'Сохранить', 'route': route
        })


class RouteDeleteView(ManagerRequiredMixin, View):
    def post(self, request, pk):
        route = get_object_or_404(Route, pk=pk)
        if not request.user.is_admin and route.created_by != request.user:
            messages.error(request, 'Нет прав.')
            return redirect('routes:manager_list')
        route.delete()
        messages.success(request, 'Маршрут удалён.')
        return redirect('routes:manager_list')


class RouteApproveView(AdminRequiredMixin, View):
    def post(self, request, pk):
        route = get_object_or_404(Route, pk=pk)
        route.is_approved = True
        route.save()
        messages.success(request, f'Маршрут «{route}» подтверждён.')
        return redirect('routes:manager_list')


class RouteRejectView(AdminRequiredMixin, View):
    def post(self, request, pk):
        route = get_object_or_404(Route, pk=pk)
        route.is_approved = False
        route.save()
        messages.warning(request, f'Маршрут «{route}» отклонён.')
        return redirect('routes:manager_list')
