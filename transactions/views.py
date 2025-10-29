# transactions/views.py 
from django.http import JsonResponse, HttpResponse
from django.db import transaction as db_transaction
from django.core.cache import cache
from django.core.paginator import Paginator
from django.db.models import Q, Sum, F, DecimalField
from django.utils import timezone
from .models import Transaction, Company, Account, ThirdParty, RecurringTransaction
from .serializers import (
    TransactionSerializer, CompanySerializer, 
    AccountSerializer, ThirdPartySerializer
)
from .permissions import HasValidLicense
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from collections import defaultdict
from decimal import Decimal
from datetime import date, timedelta
from calendar import monthrange
import logging

logger = logging.getLogger(__name__)

# ==============================================
# VISTAS MEJORADAS DE TRANSACCIONES
# ==============================================

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated, HasValidLicense])
def transaction_list(request):
    """
    Lista y crea transacciones con paginación, filtros y caché
    """
    if request.method == 'GET':
        # Optimización con select_related para reducir queries
        queryset = Transaction.objects.select_related(
            'company', 'account', 'third_party'
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
        
        # Filtro por cuenta
        if account_id := request.GET.get('account'):
            filters['account_id'] = account_id
        
        # Filtro por tercero
        if third_party_id := request.GET.get('third_party'):
            filters['third_party_id'] = third_party_id
        
        # Aplicar filtros
        if filters:
            queryset = queryset.filter(**filters)
        
        # Búsqueda por concepto
        if search := request.GET.get('search'):
            queryset = queryset.filter(
                Q(concept__icontains=search) | 
                Q(additional_description__icontains=search)
            )
        
        # Paginación mejorada
        page_size = min(int(request.GET.get('page_size', 50)), 100)  # Límite máximo
        paginator = Paginator(queryset, page_size)
        page_number = request.GET.get('page', 1)
        
        try:
            page_obj = paginator.page(page_number)
        except Exception:
            return Response(
                {'error': 'Página no válida'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Calcular totales para la página actual
        page_totals = queryset.aggregate(
            total_debits=Sum('debit'),
            total_credits=Sum('credit')
        )
        
        serializer = TransactionSerializer(page_obj, many=True)
        
        return Response({
            'results': serializer.data,
            'pagination': {
                'count': paginator.count,
                'total_pages': paginator.num_pages,
                'current_page': page_obj.number,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
                'page_size': page_size
            },
            'totals': {
                'debits': float(page_totals['total_debits'] or 0),
                'credits': float(page_totals['total_credits'] or 0),
                'balance': float((page_totals['total_debits'] or 0) - (page_totals['total_credits'] or 0))
            }
        })

    elif request.method == 'POST':
        serializer = TransactionSerializer(data=request.data)
        if serializer.is_valid():
            try:
                with db_transaction.atomic():
                    # Validación de balance
                    debit = serializer.validated_data.get('debit', 0)
                    credit = serializer.validated_data.get('credit', 0)
                    
                    if debit == 0 and credit == 0:
                        return Response(
                            {'error': 'Debe especificar un débito o crédito'}, 
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    
                    if debit > 0 and credit > 0:
                        return Response(
                            {'error': 'No puede tener débito y crédito simultáneamente'}, 
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    
                    transaction_obj = serializer.save()
                    
                    # Invalidar caché relacionado
                    cache_keys = [
                        f'dashboard_{transaction_obj.company_id}',
                        f'balance_{transaction_obj.company_id}_{transaction_obj.account_id}',
                    ]
                    cache.delete_many(cache_keys)
                    
                    logger.info(f"Transacción creada: {transaction_obj.id} por usuario {request.user.id}")
                    
                return Response(serializer.data, status=status.HTTP_201_CREATED)
                
            except Exception as e:
                logger.error(f"Error creando transacción: {str(e)}")
                return Response(
                    {'error': 'Error al crear la transacción'}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# ==============================================
# DASHBOARD CON ESTADÍSTICAS
# ==============================================

@api_view(['GET'])
@permission_classes([IsAuthenticated, HasValidLicense])
def dashboard_stats(request):
    """
    Estadísticas del dashboard con caché para mejor rendimiento
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
        current_month_transactions = Transaction.objects.filter(
            company_id=company_id,
            date__gte=first_day_month,
            date__lte=today
        )
        
        # Totales del mes
        month_totals = current_month_transactions.aggregate(
            total_debits=Sum('debit'),
            total_credits=Sum('credit'),
            transaction_count=Sum(1)
        )
        
        # Balance total histórico
        all_time_totals = Transaction.objects.filter(
            company_id=company_id
        ).aggregate(
            total_debits=Sum('debit'),
            total_credits=Sum('credit')
        )
        
        # Top 5 cuentas más utilizadas
        top_accounts = (
            Transaction.objects.filter(company_id=company_id)
            .values('account__name', 'account__code')
            .annotate(
                total=Sum(F('debit') + F('credit')),
                count=Sum(1)
            )
            .order_by('-total')[:5]
        )
        
        # Tendencia últimos 6 meses
        monthly_trend = []
        for i in range(5, -1, -1):
            month_date = today - timedelta(days=30*i)
            month_start = date(month_date.year, month_date.month, 1)
            month_end_day = monthrange(month_date.year, month_date.month)[1]
            month_end = date(month_date.year, month_date.month, month_end_day)
            
            month_data = Transaction.objects.filter(
                company_id=company_id,
                date__range=[month_start, month_end]
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
        
        stats = {
            'current_month': {
                'debits': float(month_totals['total_debits'] or 0),
                'credits': float(month_totals['total_credits'] or 0),
                'transaction_count': month_totals['transaction_count'] or 0,
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

# ==============================================
# EXPORTACIÓN MEJORADA A EXCEL
# ==============================================

@api_view(['GET'])
@permission_classes([IsAuthenticated, HasValidLicense])
def export_to_excel_enhanced(request, company_id, year, month):
    """
    Exportación mejorada a Excel con formato profesional y validaciones
    """
    try:
        company = Company.objects.get(id=company_id)
    except Company.DoesNotExist:
        return Response(
            {'error': 'Empresa no encontrada'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    try:
        # Validar año y mes
        if not (2000 <= year <= 2100):
            raise ValueError("Año fuera de rango")
        if not (1 <= month <= 12):
            raise ValueError("Mes inválido")
        
        first_day_of_month = date(year, month, 1)
        last_day_of_month_num = monthrange(year, month)[1]
        last_day_of_month = date(year, month, last_day_of_month_num)

        # Obtener transacciones optimizadas
        transactions = Transaction.objects.filter(
            company=company,
            date__lte=last_day_of_month
        ).select_related('account', 'third_party').order_by(
            'account__code', 'third_party__nit', 'date'
        )

        # Calcular balances
        balances = defaultdict(lambda: {
            'saldo_anterior': Decimal('0'),
            'debitos': Decimal('0'),
            'creditos': Decimal('0'),
            'transacciones': []
        })
        
        for t in transactions:
            key = (t.account.code, t.account.name, t.third_party.nit, t.third_party.name)
            
            if t.date < first_day_of_month:
                balances[key]['saldo_anterior'] += t.debit - t.credit
            else:
                balances[key]['debitos'] += t.debit
                balances[key]['creditos'] += t.credit
                balances[key]['transacciones'].append({
                    'fecha': t.date,
                    'concepto': t.concept,
                    'debito': t.debit,
                    'credito': t.credit
                })

        # Crear libro de Excel con estilos profesionales
        workbook = openpyxl.Workbook()
        worksheet = workbook.active
        worksheet.title = "Balance de Prueba"

        # Configurar estilos
        header_font = Font(bold=True, size=16, color="FFFFFF")
        subheader_font = Font(bold=True, size=12, color="FFFFFF")
        column_header_font = Font(bold=True, size=10, color="FFFFFF")
        
        header_fill = PatternFill(start_color="2C3E50", end_color="2C3E50", fill_type="solid")
        subheader_fill = PatternFill(start_color="34495E", end_color="34495E", fill_type="solid")
        column_fill = PatternFill(start_color="3498DB", end_color="3498DB", fill_type="solid")
        alternating_fill = PatternFill(start_color="ECF0F1", end_color="ECF0F1", fill_type="solid")
        
        thin_border = Border(
            left=Side(style='thin'), 
            right=Side(style='thin'), 
            top=Side(style='thin'), 
            bottom=Side(style='thin')
        )

        # Encabezados
        worksheet.merge_cells('A1:H1')
        cell = worksheet['A1']
        cell.value = f"{company.name} - NIT: {company.nit}"
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center', vertical='center')
        
        worksheet.merge_cells('A2:H2')
        cell = worksheet['A2']
        cell.value = "BALANCE DE PRUEBA POR TERCERO"
        cell.font = subheader_font
        cell.fill = subheader_fill
        cell.alignment = Alignment(horizontal='center', vertical='center')
        
        worksheet.merge_cells('A3:H3')
        cell = worksheet['A3']
        cell.value = f"Período: {month:02d}/{year} - Fecha de Corte: {last_day_of_month.strftime('%d/%m/%Y')}"
        cell.font = Font(italic=True, size=10)
        cell.alignment = Alignment(horizontal='center')
        
        # Línea en blanco
        worksheet.append([])

        # Encabezados de columnas
        headers = ["Cuenta", "Nombre Cuenta", "NIT Tercero", "Nombre Tercero", 
                  "Saldo Anterior", "Débitos", "Créditos", "Saldo Final"]
        
        row_num = 5
        for col, header in enumerate(headers, 1):
            cell = worksheet.cell(row=row_num, column=col, value=header)
            cell.font = column_header_font
            cell.fill = column_fill
            cell.alignment = Alignment(horizontal='center', vertical='center')
            cell.border = thin_border

        # Datos con formato
        row_num = 6
        totals = defaultdict(Decimal)
        
        for key, amounts in sorted(balances.items()):
            saldo_final = amounts['saldo_anterior'] + amounts['debitos'] - amounts['creditos']
            
            row_data = [
                key[0],  # Cuenta
                key[1],  # Nombre Cuenta
                key[2],  # NIT
                key[3],  # Nombre Tercero
                float(amounts['saldo_anterior']),
                float(amounts['debitos']),
                float(amounts['creditos']),
                float(saldo_final)
            ]
            
            for col, value in enumerate(row_data, 1):
                cell = worksheet.cell(row=row_num, column=col, value=value)
                cell.border = thin_border
                
                # Formato numérico para columnas de montos
                if col >= 5:
                    cell.number_format = '#,##0.00'
                    cell.alignment = Alignment(horizontal='right')
                    
                    # Colorear valores negativos
                    if value < 0:
                        cell.font = Font(color="E74C3C")
                else:
                    cell.alignment = Alignment(horizontal='left')
                
                # Filas alternadas
                if row_num % 2 == 0:
                    cell.fill = alternating_fill
            
            # Acumular totales
            totals['saldo_anterior'] += amounts['saldo_anterior']
            totals['debitos'] += amounts['debitos']
            totals['creditos'] += amounts['creditos']
            totals['saldo_final'] += saldo_final
            
            row_num += 1

        # Línea de totales
        row_num += 1
        worksheet.cell(row=row_num, column=3, value="TOTALES").font = Font(bold=True, size=12)
        
        for col, key in enumerate(['saldo_anterior', 'debitos', 'creditos', 'saldo_final'], 5):
            cell = worksheet.cell(row=row_num, column=col, value=float(totals[key]))
            cell.font = Font(bold=True)
            cell.number_format = '#,##0.00'
            cell.fill = PatternFill(start_color="95A5A6", end_color="95A5A6", fill_type="solid")
            cell.border = thin_border

        # Ajustar anchos de columna
        column_widths = [15, 35, 15, 35, 15, 15, 15, 15]
        for i, width in enumerate(column_widths, 1):
            worksheet.column_dimensions[get_column_letter(i)].width = width

        # Información adicional
        row_num += 3
        worksheet.cell(row=row_num, column=1, value="INFORMACIÓN DEL REPORTE").font = Font(bold=True)
        row_num += 1
        worksheet.cell(row=row_num, column=1, value=f"Generado por: {request.user.get_full_name() or request.user.username}")
        row_num += 1
        worksheet.cell(row=row_num, column=1, value=f"Fecha de generación: {timezone.now().strftime('%d/%m/%Y %H:%M')}")
        row_num += 1
        worksheet.cell(row=row_num, column=1, value=f"Total de cuentas: {len(balances)}")

        # Validación del balance
        balance_check = totals['debitos'] - totals['creditos']
        row_num += 2
        worksheet.cell(row=row_num, column=1, value="VALIDACIÓN DE BALANCE:").font = Font(bold=True)
        row_num += 1
        
        if abs(balance_check) < Decimal('0.01'):
            cell = worksheet.cell(row=row_num, column=1, value="✓ Balance cuadrado correctamente")
            cell.font = Font(color="27AE60", bold=True)
        else:
            cell = worksheet.cell(row=row_num, column=1, value=f"✗ Diferencia de balance: {float(balance_check):,.2f}")
            cell.font = Font(color="E74C3C", bold=True)

        # Crear segunda hoja con detalle de transacciones del mes
        detail_sheet = workbook.create_sheet("Detalle del Mes")
        detail_sheet.append(["Fecha", "Cuenta", "Tercero", "Concepto", "Débito", "Crédito"])
        
        # Estilo para encabezados de detalle
        for cell in detail_sheet[1]:
            cell.font = column_header_font
            cell.fill = column_fill
            cell.border = thin_border
        
        # Agregar transacciones del mes
        month_transactions = Transaction.objects.filter(
            company=company,
            date__range=[first_day_of_month, last_day_of_month]
        ).select_related('account', 'third_party').order_by('date')
        
        for t in month_transactions:
            detail_sheet.append([
                t.date.strftime('%d/%m/%Y'),
                f"{t.account.code} - {t.account.name}",
                f"{t.third_party.nit} - {t.third_party.name}",
                t.concept,
                float(t.debit),
                float(t.credit)
            ])

        # Preparar respuesta HTTP
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        filename = f'Balance_{company.nit}_{year}_{month:02d}.xlsx'
        response['Content-Disposition'] = f'attachment; filename={filename}'
        
        workbook.save(response)
        
        logger.info(f"Reporte Excel generado: {filename} por usuario {request.user.id}")
        
        return response
        
    except Exception as e:
        logger.error(f"Error generando reporte Excel: {str(e)}")
        return Response(
            {'error': f'Error al generar el reporte: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# ==============================================
# TRANSACCIONES RECURRENTES MEJORADAS
# ==============================================

@api_view(['POST'])
@permission_classes([IsAuthenticated, HasValidLicense])
def generate_recurring_transactions(request):
    """
    Genera transacciones recurrentes con validaciones mejoradas
    """
    try:
        today = date.today()
        day = request.data.get('day', today.day)
        force = request.data.get('force', False)
        
        # Validar día
        if not (1 <= day <= 31):
            return Response(
                {'error': 'Día inválido'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        recurring_transactions = RecurringTransaction.objects.filter(
            day_of_month=day
        ).select_related('company', 'account', 'third_party')
        
        if not recurring_transactions.exists():
            return Response({
                'message': 'No hay transacciones recurrentes para este día',
                'created': 0
            })
        
        created_transactions = []
        skipped = []
        errors = []
        
        with db_transaction.atomic():
            for rt in recurring_transactions:
                try:
                    # Verificar si ya existe para este mes
                    transaction_date = date(today.year, today.month, min(rt.day_of_month, last_day_of_month_num))
                    
                    exists = Transaction.objects.filter(
                        company=rt.company,
                        date=transaction_date,
                        concept=rt.concept,
                        account=rt.account,
                        third_party=rt.third_party
                    ).exists()
                    
                    if exists and not force:
                        skipped.append({
                            'concept': rt.concept,
                            'reason': 'Ya existe para este mes'
                        })
                        continue
                    
                    transaction_obj = Transaction.objects.create(
                        company=rt.company,
                        date=transaction_date,
                        account=rt.account,
                        third_party=rt.third_party,
                        concept=f"[Recurrente] {rt.concept}",
                        additional_description=rt.additional_description,
                        debit=rt.debit,
                        credit=rt.credit,
                    )
                    created_transactions.append(transaction_obj)
                    
                except Exception as e:
                    errors.append({
                        'concept': rt.concept,
                        'error': str(e)
                    })
                    logger.error(f"Error creando transacción recurrente: {str(e)}")
        
        # Invalidar caché
        if created_transactions:
            company_ids = set(t.company_id for t in created_transactions)
            cache_keys = [f'dashboard_{cid}' for cid in company_ids]
            cache.delete_many(cache_keys)
        
        serializer = TransactionSerializer(created_transactions, many=True)
        
        response_data = {
            'created': len(created_transactions),
            'skipped': len(skipped),
            'errors': len(errors),
            'transactions': serializer.data
        }
        
        if skipped:
            response_data['skipped_details'] = skipped
        if errors:
            response_data['error_details'] = errors
        
        logger.info(f"Transacciones recurrentes generadas: {len(created_transactions)} por usuario {request.user.id}")
        
        return Response(response_data, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Error generando transacciones recurrentes: {str(e)}")
        return Response(
            {'error': 'Error al generar transacciones recurrentes'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
# ==============================================
# VISTAS BÁSICAS QUE FALTABAN
# ==============================================

@api_view(['GET'])
@permission_classes([IsAuthenticated, HasValidLicense])
def company_list(request):
    """Lista de empresas"""
    companies = Company.objects.all()
    serializer = CompanySerializer(companies, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated, HasValidLicense])
def account_list(request):
    """Lista de cuentas"""
    accounts = Account.objects.all()
    serializer = AccountSerializer(accounts, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated, HasValidLicense])
def third_party_list(request):
    """Lista de terceros"""
    third_parties = ThirdParty.objects.all()
    serializer = ThirdPartySerializer(third_parties, many=True)
    return Response(serializer.data)

# Alias para compatibilidad con el nombre antiguo
export_to_excel = export_to_excel_enhanced
