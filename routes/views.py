from datetime import date
from django import forms
from django.db.models import Count
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.forms import inlineformset_factory, BaseInlineFormSet
from django.views import View

from users.permissions import ManagerRequiredMixin, AdminRequiredMixin
from bookings.views import get_occupied_seat_ids
from bookings.models import Booking
from .models import Route, Stop
from .forms import RouteForm, StopForm


class StopInlineFormSet(BaseInlineFormSet):
    deletion_widget = forms.HiddenInput


class RouteListView(View):
    def get(self, request):
        routes_qs = Route.objects.filter(is_approved=True).prefetch_related('stops').annotate(
            total_seats=Count('transport__seats', distinct=True)
        )
        search_from = request.GET.get('from_city', '').strip()
        search_to   = request.GET.get('to_city', '').strip()
        search_date_raw = request.GET.get('date', '').strip()

        try:
            search_date_obj = date.fromisoformat(search_date_raw) if search_date_raw else date.today()
        except ValueError:
            search_date_obj = date.today()
        search_date = str(search_date_obj)

        if search_from:
            routes_qs = routes_qs.filter(stops__city__icontains=search_from).distinct()
        if search_to:
            routes_qs = routes_qs.filter(stops__city__icontains=search_to).distinct()

        routes = list(routes_qs)

        def pick_stop(candidates, city_query):
            if not city_query:
                return None
            city_query_l = city_query.lower()
            exact = next((s for s in candidates if s.city.lower() == city_query_l), None)
            if exact:
                return exact
            return next((s for s in candidates if city_query_l in s.city.lower()), None)

        prepared_routes = []
        for route in routes:
            stops = list(route.stops.all())
            boarding_stops = [s for s in stops if s.is_boarding_allowed]
            alighting_stops = [s for s in stops if s.is_alighting_allowed]

            selected_from = pick_stop(boarding_stops, search_from)
            to_candidates = alighting_stops
            if selected_from:
                to_candidates = [s for s in alighting_stops if s.order > selected_from.order]
            selected_to = pick_stop(to_candidates, search_to)

            if search_from and not selected_from:
                continue
            if search_to and not selected_to:
                continue

            route.prefill_from_stop_id = str(selected_from.pk) if selected_from else ''
            route.prefill_to_stop_id = str(selected_to.pk) if selected_to else ''
            prepared_routes.append(route)

        routes = prepared_routes

        route_ids = [route.id for route in routes]
        occupied_rows = Booking.objects.filter(
            route_id__in=route_ids,
            travel_date=search_date_obj,
            status__in=[Booking.Status.BOOKED, Booking.Status.PAID],
        ).values('route_id').annotate(occupied=Count('seat_id', distinct=True))
        occupied_map = {row['route_id']: row['occupied'] for row in occupied_rows}

        routes = [route for route in routes if route.total_seats > occupied_map.get(route.id, 0)]

        boarding_cities = list(
            Stop.objects.filter(
                route__is_approved=True,
                is_boarding_allowed=True,
            )
            .order_by('city')
            .values_list('city', flat=True)
            .distinct()
        )
        alighting_cities = list(
            Stop.objects.filter(
                route__is_approved=True,
                is_alighting_allowed=True,
            )
            .order_by('city')
            .values_list('city', flat=True)
            .distinct()
        )
        return render(request, 'routes/list.html', {
            'routes': routes,
            'boarding_cities': boarding_cities,
            'alighting_cities': alighting_cities,
            'search_from': search_from, 'search_to': search_to,
            'search_date': search_date,
        })


class RouteDetailView(View):
    def get(self, request, pk):
        route = get_object_or_404(Route, pk=pk, is_approved=True)
        all_stops = list(route.stops.order_by('order'))

        today         = str(date.today())
        selected_date = request.GET.get('date', today)
        search_from = request.GET.get('from_city', '').strip()
        search_to = request.GET.get('to_city', '').strip()
        from_stop_pk  = request.GET.get('from_stop', '')
        to_stop_pk    = request.GET.get('to_stop', '')

        # Остановки доступные для выбора пользователем
        boarding_stops = sorted(
            [s for s in all_stops if s.is_boarding_allowed],
            key=lambda s: (s.city or '').lower(),
        )
        alighting_stops = sorted(
            [s for s in all_stops if s.is_alighting_allowed],
            key=lambda s: (s.city or '').lower(),
        )

        if not from_stop_pk and search_from:
            matched_from = next(
                (s for s in boarding_stops if s.city.lower() == search_from.lower()),
                None,
            )
            if not matched_from:
                matched_from = next(
                    (s for s in boarding_stops if search_from.lower() in s.city.lower()),
                    None,
                )
            if matched_from:
                from_stop_pk = str(matched_from.pk)

        if not to_stop_pk and search_to:
            to_candidates = alighting_stops
            if from_stop_pk:
                from_candidate = next((s for s in all_stops if str(s.pk) == str(from_stop_pk)), None)
                if from_candidate:
                    to_candidates = [s for s in alighting_stops if s.order > from_candidate.order]

            matched_to = next(
                (s for s in to_candidates if s.city.lower() == search_to.lower()),
                None,
            )
            if not matched_to:
                matched_to = next(
                    (s for s in to_candidates if search_to.lower() in s.city.lower()),
                    None,
                )
            if matched_to:
                to_stop_pk = str(matched_to.pk)

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
            'search_from': search_from,
            'search_to': search_to,
        })


StopFormSet = inlineformset_factory(
    Route, Stop, form=StopForm,
    formset=StopInlineFormSet,
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
