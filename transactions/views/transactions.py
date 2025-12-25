# transactions/views/transactions.py
"""
Vistas para gestión de transacciones (CRUD).
"""

from .base import *

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated, HasValidLicense])
def transaction_list(request):
    """
    Lista y crea transacciones con múltiples movimientos (partida doble)
    """
    if request.method == 'GET':
        return _list_transactions(request)
    elif request.method == 'POST':
        return _create_transaction(request)


def _list_transactions(request):
    """Lista transacciones con filtros y paginación"""
    # Optimización con select_related para reducir queries
    queryset = Transaction.objects.select_related('company').prefetch_related(
        'movements__account', 'movements__third_party'
    ).order_by('-date', '-id')

    # Sistema de filtros avanzados
    filters = {}

    # Filtro por empresa
    if company_id := request.GET.get('company'):
        filters['company_id'] = company_id

    # Filtro por rango de fechas
    if start_date := request.GET.get('start_date'):
        filters['date__gte'] = start_date
    if end_date := request.GET.get('end_date'):
        filters['date__lte'] = end_date

    # Filtro por concepto
    if search := request.GET.get('search'):
        queryset = queryset.filter(
            Q(concept__icontains=search) |
            Q(additional_description__icontains=search)
        )

    # Aplicar filtros
    if filters:
        queryset = queryset.filter(**filters)

    # Paginación mejorada
    page_obj, pagination_data = paginate_queryset(queryset, request)

    if page_obj is None:
        return Response(pagination_data, status=pagination_data.get('status'))

    # Calcular totales para la página actual
    total_debits = Decimal('0')
    total_credits = Decimal('0')

    for transaction in page_obj:
        for movement in transaction.movements.all():
            total_debits += movement.debit
            total_credits += movement.credit

    serializer = TransactionSerializer(page_obj, many=True)

    return Response({
        'results': serializer.data,
        'pagination': pagination_data,
        'totals': {
            'debits': float(total_debits),
            'credits': float(total_credits),
            'balance': float(total_debits - total_credits)
        }
    })


def _create_transaction(request):
    """Crea una nueva transacción con movimientos"""
    serializer = TransactionCreateSerializer(data=request.data)

    if serializer.is_valid():
        try:
            with db_transaction.atomic():
                transaction_obj = serializer.save()

                # Obtener alertas y enviarlas al frontend
                alertas, sugerencias = transaction_obj.validar_logica_contable()

                # Invalidar caché
                invalidate_company_cache(transaction_obj.company_id)

                logger.info(f"Transacción creada: {transaction_obj.id}")

                # Incluir alertas en la respuesta
                response_data = TransactionSerializer(transaction_obj).data
                if alertas:
                    response_data['alertas'] = alertas
                    response_data['sugerencias'] = sugerencias

                return Response(response_data, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Error creando transacción: {str(e)}")
            return Response(
                {'error': f'Error al crear la transacción: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT'])
@permission_classes([IsAuthenticated, HasValidLicense])
def edit_transaction(request, transaction_id):
    """
    Edita una transacción COMPLETA incluyendo sus movimientos.
    Permite agregar, editar y eliminar movimientos.
    """
    try:
        transaction = Transaction.objects.get(id=transaction_id)

        # Actualizar datos generales
        if 'date' in request.data:
            transaction.date = request.data['date']
        if 'concept' in request.data:
            transaction.concept = request.data['concept']
        if 'additional_description' in request.data:
            transaction.additional_description = request.data['additional_description']

        # Si vienen movimientos, reemplazarlos todos
        if 'movements' in request.data:
            # Eliminar movimientos actuales
            transaction.movements.all().delete()

            # Crear los nuevos movimientos
            for mov_data in request.data['movements']:
                Movement.objects.create(
                    transaction=transaction,
                    account_id=mov_data['account'],
                    third_party_id=mov_data['third_party'],
                    debit=Decimal(str(mov_data.get('debit', 0))),
                    credit=Decimal(str(mov_data.get('credit', 0))),
                    description=mov_data.get('description', '')
                )

        transaction.save()
        invalidate_company_cache(transaction.company_id)

        return Response({
            'success': True,
            'message': 'Transacción actualizada exitosamente',
            'transaction': TransactionSerializer(transaction).data
        })

    except Transaction.DoesNotExist:
        return Response({'error': 'Transacción no encontrada'}, status=404)
    except Exception as e:
        logger.error(f"Error editando transacción: {str(e)}")
        return Response({'error': str(e)}, status=500)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated, HasValidLicense])
def delete_or_cancel_transaction(request, transaction_id):
    """
    Sistema híbrido inteligente:
    - Admin + fecha reciente (≤2 días) → Elimina
    - Otros casos → Anula (asiento inverso)
    """
    try:
        transaction = Transaction.objects.get(id=transaction_id)

        # Calcular días de antigüedad
        days_old = (date.today() - transaction.date).days

        # Verificar si es admin (superuser)
        is_admin = request.user.is_superuser

        # CASO 1: Admin + fecha reciente → ELIMINAR
        if is_admin and days_old <= 2:
            company_id = transaction.company_id
            transaction.delete()

            invalidate_company_cache(company_id)

            return Response({
                'success': True,
                'action': 'deleted',
                'message': f'Transacción eliminada (fecha reciente: {days_old} días)'
            })

        # CASO 2: Usuario normal o fecha antigua → ANULAR
        else:
            return _anular_transaction(transaction, request.user)

    except Transaction.DoesNotExist:
        return Response({'error': 'Transacción no encontrada'}, status=404)
    except Exception as e:
        logger.error(f"Error en delete_or_cancel: {str(e)}")
        return Response({'error': str(e)}, status=500)


def _anular_transaction(transaction, user):
    """
    Crea un asiento inverso (anulación contable profesional)
    """
    try:
        with db_transaction.atomic():
            # Crear transacción de anulación
            anulacion = Transaction.objects.create(
                company=transaction.company,
                date=date.today(),
                concept=f"ANULACIÓN - {transaction.concept}",
                additional_description=f"Anula comprobante {transaction.number} del {transaction.date}. Usuario: {user.username}"
            )

            # Crear movimientos inversos
            for mov in transaction.movements.all():
                Movement.objects.create(
                    transaction=anulacion,
                    account=mov.account,
                    third_party=mov.third_party,
                    debit=mov.credit,  # Invertido
                    credit=mov.debit,  # Invertido
                    description=f"Anulación: {mov.description or ''}"
                )

            invalidate_company_cache(transaction.company_id)

            logger.info(
                f"Transacción {transaction.number} anulada por {user.username}. "
                f"Comprobante anulación: {anulacion.number}"
            )

            return Response({
                'success': True,
                'action': 'cancelled',
                'message': f'Transacción anulada. Comprobante: {anulacion.number}',
                'cancellation_number': anulacion.number,
                'cancellation_id': anulacion.id
            })

    except Exception as e:
        logger.error(f"Error anulando transacción: {str(e)}")
        return Response({'error': f'Error al anular: {str(e)}'}, status=500)
