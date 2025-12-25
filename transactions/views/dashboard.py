# transactions/views/dashboard.py
"""
Vista del dashboard con estadísticas.
"""

from .base import *


@api_view(['GET'])
@permission_classes([IsAuthenticated, HasValidLicense])
def dashboard_stats(request):
    """
    Estadísticas del dashboard actualizadas para partida doble.
    """
    company_id = request.GET.get('company')
    if not company_id:
        return Response(
            {'error': 'Se requiere el ID de la empresa'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Intentar obtener del caché
    cache_key = f'dashboard_{company_id}'
    cached_data = cache.get(cache_key)
    if cached_data:
        return Response(cached_data)

    try:
        today = date.today()
        first_day_month = date(today.year, today.month, 1)

        # Estadísticas del mes actual
        current_month_movements = Movement.objects.filter(
            transaction__company_id=company_id,
            transaction__date__gte=first_day_month,
            transaction__date__lte=today
        )

        # Totales del mes
        month_totals = current_month_movements.aggregate(
            total_debits=Sum('debit'),
            total_credits=Sum('credit'),
            movement_count=Sum(1)
        )

        # Balance total histórico
        all_time_totals = Movement.objects.filter(
            transaction__company_id=company_id
        ).aggregate(
            total_debits=Sum('debit'),
            total_credits=Sum('credit')
        )

        # Top 5 cuentas más utilizadas
        top_accounts = (
            Movement.objects.filter(transaction__company_id=company_id)
            .values('account__name', 'account__code')
            .annotate(
                total=Sum(F('debit') + F('credit')),
                count=Sum(1)
            )
            .order_by('-total')[:5]
        )

        # Tendencia últimos 6 meses
        monthly_trend = _calculate_monthly_trend(company_id, today)

        stats = {
            'current_month': {
                'debits': float(month_totals['total_debits'] or 0),
                'credits': float(month_totals['total_credits'] or 0),
                'movement_count': month_totals['movement_count'] or 0,
                'balance': float((month_totals['total_debits'] or 0) - (month_totals['total_credits'] or 0))
            },
            'all_time': {
                'debits': float(all_time_totals['total_debits'] or 0),
                'credits': float(all_time_totals['total_credits'] or 0),
                'balance': float((all_time_totals['total_debits'] or 0) - (all_time_totals['total_credits'] or 0))
            },
            'top_accounts': list(top_accounts),
            'monthly_trend': monthly_trend,
            'last_updated': timezone.now().isoformat()
        }

        # Guardar en caché por 5 minutos
        cache.set(cache_key, stats, 300)

        return Response(stats)

    except Exception as e:
        logger.error(f"Error generando estadísticas: {str(e)}")
        return Response(
            {'error': 'Error al generar estadísticas'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def _calculate_monthly_trend(company_id, today):
    """Calcula la tendencia de los últimos 6 meses."""
    monthly_trend = []

    for i in range(5, -1, -1):
        month_date = today - timedelta(days=30 * i)
        month_start = date(month_date.year, month_date.month, 1)
        month_end_day = monthrange(month_date.year, month_date.month)[1]
        month_end = date(month_date.year, month_date.month, month_end_day)

        month_data = Movement.objects.filter(
            transaction__company_id=company_id,
            transaction__date__range=[month_start, month_end]
        ).aggregate(
            debits=Sum('debit'),
            credits=Sum('credit')
        )

        monthly_trend.append({
            'month': month_start.strftime('%Y-%m'),
            'month_name': month_start.strftime('%B %Y'),
            'debits': float(month_data['debits'] or 0),
            'credits': float(month_data['credits'] or 0),
            'balance': float((month_data['debits'] or 0) - (month_data['credits'] or 0))
        })

    return monthly_trend
