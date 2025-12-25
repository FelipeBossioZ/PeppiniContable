# transactions/views/movements.py
"""
Vistas para gestión de movimientos individuales.
"""

from .base import *


@api_view(['GET'])
@permission_classes([IsAuthenticated, HasValidLicense])
def movement_list(request):
    """Lista de movimientos con filtros"""
    movements = Movement.objects.select_related(
        'transaction', 'account', 'third_party'
    ).order_by('-transaction__date', '-id')

    # Aplicar filtros
    if company_id := request.GET.get('company'):
        movements = movements.filter(transaction__company_id=company_id)

    if start_date := request.GET.get('start_date'):
        movements = movements.filter(transaction__date__gte=start_date)

    if end_date := request.GET.get('end_date'):
        movements = movements.filter(transaction__date__lte=end_date)

    if account_id := request.GET.get('account'):
        movements = movements.filter(account_id=account_id)

    serializer = MovementSerializer(movements, many=True)
    return Response(serializer.data)


@api_view(['PUT'])
@permission_classes([IsAuthenticated, HasValidLicense])
def edit_movement(request, movement_id):
    """
    Edita un movimiento individual y aprende de los cambios.
    """
    try:
        movement = Movement.objects.select_related('transaction').get(id=movement_id)

        # Datos anteriores para el aprendizaje
        old_account_id = movement.account_id

        # Actualizar campos
        if 'account' in request.data:
            movement.account_id = request.data['account']
        if 'third_party' in request.data:
            movement.third_party_id = request.data['third_party']
        if 'debit' in request.data:
            movement.debit = Decimal(str(request.data['debit']))
        if 'credit' in request.data:
            movement.credit = Decimal(str(request.data['credit']))
        if 'description' in request.data:
            movement.description = request.data['description']

        movement.save()

        # Aprendizaje automático cuando se cambia la cuenta
        if 'account' in request.data and old_account_id != movement.account_id:
            from .classification import aprender_de_edicion
            aprender_de_edicion(
                movement.transaction_id,
                movement_id,
                movement.account_id
            )

        # Invalidar caché
        invalidate_company_cache(movement.transaction.company_id)

        return Response({
            'success': True,
            'message': 'Movimiento actualizado exitosamente',
            'movement': MovementSerializer(movement).data
        })

    except Movement.DoesNotExist:
        return Response({'error': 'Movimiento no encontrado'}, status=404)
    except Exception as e:
        logger.error(f"Error editando movimiento: {str(e)}")
        return Response({'error': str(e)}, status=500)
