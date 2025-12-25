# transactions/views/classification.py
"""
Vistas y funciones para clasificación inteligente de gastos.
"""

from .base import *


# Patrones base de clasificación (todas las empresas)
CLASIFICACION_BASE = {
    '5120': ['arriendo', 'alquiler', 'renta', 'arrendamiento', 'lease', 'canon'],
    '5105': ['honorarios', 'nomina', 'nómina', 'salario', 'sueldo', 'prestaciones', 'personal'],
    '5135': ['servicios', 'aseo', 'vigilancia'],
    '5140': ['impuesto', 'gravamen', 'predial', 'vehicular', 'ica', 'reteica', 'iva'],
    '5130': ['seguros', 'póliza', 'aseguradora', 'poliza', 'seguro'],
    '5115': ['celular', 'internet', 'telecomunicaciones', 'telefono', 'datos'],
    '5145': ['mantenimiento', 'reparación', 'reparacion', 'repuesto'],
}

# Patrones específicos por empresa
CLASIFICACION_POR_EMPRESA = {
    1: {  # LOSCAREROS (pruebas)
        '5120': ['local', 'bodega'],
    },
    3: {  # CORTIJO DE RESTREPO SAS
        '5120': ['consultorio', 'oficina'],
        '5140': ['camara de comercio', 'registro'],
        '5135': ['nativa'],
        '5110': ['fernandez fernandez german tulio', 'german tulio'],
        '5395': ['seguros de vida', 'pricesmart colombia', 'pricesmart'],
        '5295': ['criadores', 'ganado', 'riviera del golfo', 'club nautico'],
    }
}


def clasificar_gasto_inteligente(nit, nombre, valor, company_id):
    """
    Clasificación inteligente de gastos usando reglas aprendidas.

    Lógica:
    1. Busca si existe una regla para este NIT en esta empresa
    2. Si existe → valida si el monto es normal o anómalo
    3. Si no existe → usa clasificación por palabras clave
    4. Siempre fallback a 5195 DIVERSOS si hay problemas
    """
    try:
        # 1. Buscar regla existente
        try:
            rule = AccountingRule.objects.get(
                company_id=company_id,
                third_party_nit=nit
            )

            # 2. Validar si el monto es anómalo
            if rule.is_amount_anomaly(Decimal(str(valor)), threshold=0.5):
                logger.warning(
                    f"⚠️ ANOMALÍA: NIT {nit} - Promedio: {rule.average_amount}, "
                    f"Actual: {valor} (>{50}% diferencia)"
                )
                return '5195', True, f"Monto anómalo: promedio ${rule.average_amount:,.0f}"

            # 3. Monto normal → Usar la regla aprendida
            rule.update_statistics(Decimal(str(valor)))
            return rule.account.code, False, f"Regla aprendida (confianza: {rule.confidence_score})"

        except AccountingRule.DoesNotExist:
            # No existe regla → Clasificación por palabras clave
            cuenta_code = clasificar_por_palabras_clave(nombre, company_id)
            return cuenta_code, False, "Clasificación por palabras clave"

    except Exception as e:
        logger.error(f"Error en clasificación inteligente: {str(e)}")
        return '5195', False, "Error en clasificación"


def clasificar_por_palabras_clave(texto, company_id=None):
    """
    Clasificación tradicional por palabras clave.
    Soporta patrones específicos por empresa.
    """
    # Combinar patrones
    clasificacion = CLASIFICACION_BASE.copy()

    company_id_int = int(company_id) if company_id else None

    if company_id_int and company_id_int in CLASIFICACION_POR_EMPRESA:
        for cuenta, palabras in CLASIFICACION_POR_EMPRESA[company_id_int].items():
            if cuenta in clasificacion:
                clasificacion[cuenta].extend(palabras)
            else:
                clasificacion[cuenta] = palabras

    texto_lower = texto.lower()

    for cuenta, keywords in clasificacion.items():
        if any(keyword in texto_lower for keyword in keywords):
            return cuenta

    # Default: Gastos diversos
    return '5195'


def aprender_de_edicion(transaction_id, movement_id, nueva_cuenta_id):
    """
    Aprende automáticamente cuando el usuario edita una transacción.
    Crea o actualiza reglas en AccountingRule.
    """
    try:
        movement = Movement.objects.select_related(
            'transaction', 'third_party', 'account'
        ).get(id=movement_id)

        nit = movement.third_party.nit
        nombre = movement.third_party.name
        company_id = movement.transaction.company_id
        valor = movement.debit if movement.debit > 0 else movement.credit
        nueva_cuenta = Account.objects.get(id=nueva_cuenta_id)

        # Crear o actualizar regla
        rule, created = AccountingRule.objects.get_or_create(
            company_id=company_id,
            third_party_nit=nit,
            defaults={
                'third_party_name': nombre,
                'account': nueva_cuenta,
                'created_by_user': True,
                'last_amount': valor,
                'average_amount': valor,
                'confidence_score': 1
            }
        )

        if not created:
            rule.account = nueva_cuenta
            rule.update_statistics(valor)
            rule.save()

            logger.info(
                f"✅ Regla actualizada: NIT {nit} → {nueva_cuenta.code} "
                f"(confianza: {rule.confidence_score})"
            )
        else:
            logger.info(f"🆕 Nueva regla creada: NIT {nit} → {nueva_cuenta.code}")

        return True

    except Exception as e:
        logger.error(f"Error aprendiendo de edición: {str(e)}")
        return False


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated, HasValidLicense])
def accounting_rules_list(request):
    """
    Lista y crea reglas de clasificación manualmente.
    """
    if request.method == 'GET':
        company_id = request.GET.get('company')
        if not company_id:
            return Response({'error': 'Se requiere company_id'}, status=400)

        rules = AccountingRule.objects.filter(
            company_id=company_id
        ).select_related('account').order_by('-confidence_score', 'third_party_name')

        rules_data = [{
            'id': rule.id,
            'third_party_nit': rule.third_party_nit,
            'third_party_name': rule.third_party_name,
            'account_code': rule.account.code,
            'account_name': rule.account.name,
            'confidence_score': rule.confidence_score,
            'average_amount': float(rule.average_amount) if rule.average_amount else None,
            'created_by_user': rule.created_by_user,
            'updated_at': rule.updated_at.isoformat()
        } for rule in rules]

        return Response(rules_data)

    elif request.method == 'POST':
        try:
            rule = AccountingRule.objects.create(
                company_id=request.data['company'],
                third_party_nit=request.data['nit'],
                third_party_name=request.data.get('name', ''),
                account_id=request.data['account'],
                created_by_user=True
            )

            return Response({
                'success': True,
                'message': 'Regla creada exitosamente',
                'rule_id': rule.id
            }, status=201)

        except Exception as e:
            return Response({'error': str(e)}, status=400)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated, HasValidLicense])
def delete_accounting_rule(request, rule_id):
    """
    Elimina una regla de clasificación.
    """
    try:
        rule = AccountingRule.objects.get(id=rule_id)
        rule.delete()

        return Response({
            'success': True,
            'message': 'Regla eliminada exitosamente'
        })

    except AccountingRule.DoesNotExist:
        return Response({'error': 'Regla no encontrada'}, status=404)
