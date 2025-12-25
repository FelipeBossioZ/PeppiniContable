# transactions/views/validation.py
"""
Vistas para validación y corrección de transacciones.
"""

from .base import *

# Cuentas con comportamiento especial
CUENTAS_ESPECIALES_DEBITO = ['4175']
CUENTAS_ESPECIALES_CREDITO = ['5905']


@api_view(['POST'])
@permission_classes([IsAuthenticated, HasValidLicense])
def validate_transaction(request):
    """
    Valida un asiento SIN guardarlo en la base de datos.
    Devuelve alertas y sugerencias si las hay.

    Solo valida clases 3, 4 y 5 (Patrimonio, Ingresos, Gastos).
    No valida Clase 1 (Activos) ni Clase 2 (Pasivos).
    """
    try:
        movements_data = request.data.get('movements', [])

        alertas = []
        sugerencias = []
        correcciones = []

        for index, mov_data in enumerate(movements_data):
            try:
                cuenta = Account.objects.get(id=mov_data['account'])
                tipo_cuenta = cuenta.tipo
                codigo_cuenta = cuenta.code

                debito = float(mov_data.get('debit', 0))
                credito = float(mov_data.get('credit', 0))

                debito_corregido = debito
                credito_corregido = credito

                # Ignorar validaciones para ACTIVO y PASIVO
                if tipo_cuenta in ['ACTIVO', 'PASIVO']:
                    correcciones.append({
                        'movement_index': index,
                        'account_id': cuenta.id,
                        'third_party_id': mov_data['third_party'],
                        'debito_corregido': debito,
                        'credito_corregido': credito
                    })
                    continue

                # Validar SOLO para PATRIMONIO, INGRESOS y GASTOS
                if debito > 0:
                    if tipo_cuenta in ['PATRIMONIO', 'INGRESO'] and codigo_cuenta not in CUENTAS_ESPECIALES_DEBITO:
                        alertas.append(f"⚠️ DÉBITO a {codigo_cuenta} - {cuenta.name} ({tipo_cuenta})")
                        sugerencias.append(f"Los {tipo_cuenta.lower()}s normalmente aumentan con CRÉDITO")
                        credito_corregido = debito
                        debito_corregido = 0

                elif credito > 0:
                    if tipo_cuenta == 'GASTO' and codigo_cuenta not in CUENTAS_ESPECIALES_CREDITO:
                        alertas.append(f"⚠️ CRÉDITO a {codigo_cuenta} - {cuenta.name} ({tipo_cuenta})")
                        sugerencias.append(f"Los gastos normalmente aumentan con DÉBITO")
                        debito_corregido = credito
                        credito_corregido = 0

                correcciones.append({
                    'movement_index': index,
                    'account_id': cuenta.id,
                    'third_party_id': mov_data['third_party'],
                    'debito_corregido': debito_corregido,
                    'credito_corregido': credito_corregido
                })

            except Account.DoesNotExist:
                continue

        return Response({
            'alertas': alertas,
            'sugerencias': sugerencias,
            'correcciones': correcciones
        })

    except Exception as e:
        logger.error(f"Error validando transacción: {str(e)}")
        return Response({'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated, HasValidLicense])
def corregir_transaccion(request, transaction_id):
    """
    Corrección inteligente de transacciones.
    Solo corrige clases 3, 4 y 5 (Patrimonio, Ingresos, Gastos).
    """
    try:
        transaction = Transaction.objects.get(id=transaction_id)

        movimientos_corregidos = 0
        movimientos_detalle = []

        for movimiento in transaction.movements.all():
            cuenta = movimiento.account
            tipo_cuenta = cuenta.tipo
            codigo_cuenta = cuenta.code

            movimiento_original = {
                'id': movimiento.id,
                'cuenta': f"{codigo_cuenta} - {cuenta.name}",
                'tipo': tipo_cuenta,
                'debito_original': float(movimiento.debit),
                'credito_original': float(movimiento.credit)
            }

            # Ignorar ACTIVOS y PASIVOS
            if tipo_cuenta in ['ACTIVO', 'PASIVO']:
                movimientos_detalle.append({
                    **movimiento_original,
                    'corregido': False,
                    'razon': f"{tipo_cuenta} - No requiere corrección automática"
                })
                continue

            necesita_correccion = False
            razon = ""

            # Validar clases 3, 4, 5
            if codigo_cuenta in CUENTAS_ESPECIALES_DEBITO:
                if movimiento.credit > 0 and tipo_cuenta == 'INGRESO':
                    movimiento.debit = movimiento.credit
                    movimiento.credit = Decimal('0')
                    necesita_correccion = True
                    razon = f"Cuenta especial {codigo_cuenta} (ingreso) debe aumentar con débito"

            elif codigo_cuenta in CUENTAS_ESPECIALES_CREDITO:
                if movimiento.debit > 0 and tipo_cuenta == 'GASTO':
                    movimiento.credit = movimiento.debit
                    movimiento.debit = Decimal('0')
                    necesita_correccion = True
                    razon = f"Cuenta especial {codigo_cuenta} (gasto) debe aumentar con crédito"

            else:
                # PATRIMONIO e INGRESOS: Aumentan con CRÉDITO
                if movimiento.debit > 0 and tipo_cuenta in ['PATRIMONIO', 'INGRESO']:
                    movimiento.credit = movimiento.debit
                    movimiento.debit = Decimal('0')
                    necesita_correccion = True
                    razon = f"{tipo_cuenta} normal debe aumentar con crédito"

                # GASTOS: Aumentan con DÉBITO
                elif movimiento.credit > 0 and tipo_cuenta == 'GASTO':
                    movimiento.debit = movimiento.credit
                    movimiento.credit = Decimal('0')
                    necesita_correccion = True
                    razon = f"{tipo_cuenta} normal debe aumentar con débito"

            if necesita_correccion:
                movimiento.save()
                movimientos_corregidos += 1

            movimientos_detalle.append({
                **movimiento_original,
                'corregido': necesita_correccion,
                'razon': razon if necesita_correccion else 'Sin cambios'
            })

        # Validar balance
        total_debit = sum(m.debit for m in transaction.movements.all())
        total_credit = sum(m.credit for m in transaction.movements.all())
        diferencia = total_debit - total_credit

        return Response({
            'success': True,
            'message': f'Se corrigieron {movimientos_corregidos} movimientos',
            'movimientos_corregidos': movimientos_corregidos,
            'detalle_correcciones': movimientos_detalle,
            'balance_final': {
                'debitos': float(total_debit),
                'creditos': float(total_credit),
                'diferencia': float(diferencia),
                'balanceado': abs(diferencia) < Decimal('0.01')
            },
            'transaction': TransactionSerializer(transaction).data
        })

    except Transaction.DoesNotExist:
        return Response({'error': 'Transacción no encontrada'}, status=404)
    except Exception as e:
        logger.error(f"Error en corrección automática: {str(e)}")
        return Response({'error': f'Error interno: {str(e)}'}, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated, HasValidLicense])
def calcular_correcciones(request, transaction_id):
    """
    Calcula cómo deberían estar los movimientos SIN guardar nada.
    """
    try:
        transaction = Transaction.objects.get(id=transaction_id)

        correcciones = []

        for movimiento in transaction.movements.all():
            cuenta = movimiento.account
            tipo_cuenta = cuenta.tipo
            codigo_cuenta = cuenta.code

            debito_actual = float(movimiento.debit)
            credito_actual = float(movimiento.credit)

            debito_corregido = debito_actual
            credito_corregido = credito_actual

            # Lógica de corrección
            if codigo_cuenta in CUENTAS_ESPECIALES_DEBITO:
                if credito_actual > 0 and tipo_cuenta == 'INGRESO':
                    debito_corregido = credito_actual
                    credito_corregido = 0

            elif codigo_cuenta in CUENTAS_ESPECIALES_CREDITO:
                if debito_actual > 0 and tipo_cuenta == 'GASTO':
                    credito_corregido = debito_actual
                    debito_corregido = 0

            else:
                # Reglas normales
                if credito_actual > 0 and tipo_cuenta in ['ACTIVO', 'GASTO']:
                    debito_corregido = credito_actual
                    credito_corregido = 0

                elif debito_actual > 0 and tipo_cuenta in ['PASIVO', 'INGRESO', 'PATRIMONIO']:
                    credito_corregido = debito_actual
                    debito_corregido = 0

            correcciones.append({
                'movement_index': list(transaction.movements.all()).index(movimiento),
                'account_id': cuenta.id,
                'third_party_id': movimiento.third_party.id,
                'debito_corregido': debito_corregido,
                'credito_corregido': credito_corregido
            })

        return Response({
            'correcciones': correcciones
        })

    except Transaction.DoesNotExist:
        return Response({'error': 'Transacción no encontrada'}, status=404)
    except Exception as e:
        logger.error(f"Error calculando correcciones: {str(e)}")
        return Response({'error': str(e)}, status=500)
