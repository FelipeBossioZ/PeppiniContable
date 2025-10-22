from django.http import JsonResponse, HttpResponse
from .models import Transaction, Company, Account, ThirdParty
from .serializers import TransactionSerializer, CompanySerializer, AccountSerializer, ThirdPartySerializer
from .permissions import HasValidLicense
import openpyxl
from openpyxl.styles import Font
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from collections import defaultdict
from decimal import Decimal
from datetime import date
from calendar import monthrange

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated, HasValidLicense])
def transaction_list(request):
    if request.method == 'GET':
        transactions = Transaction.objects.all()
        serializer = TransactionSerializer(transactions, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = TransactionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated, HasValidLicense])
def company_list(request):
    companies = Company.objects.all()
    serializer = CompanySerializer(companies, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated, HasValidLicense])
def account_list(request):
    accounts = Account.objects.all()
    serializer = AccountSerializer(accounts, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated, HasValidLicense])
def third_party_list(request):
    third_parties = ThirdParty.objects.all()
    serializer = ThirdPartySerializer(third_parties, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated, HasValidLicense])
def export_to_excel(request, company_id, year, month):
    company = Company.objects.get(id=company_id)
    first_day_of_month = date(year, month, 1)
    last_day_of_month_num = monthrange(year, month)[1]
    last_day_of_month = date(year, month, last_day_of_month_num)

    transactions = Transaction.objects.filter(
        company=company,
        date__lte=last_day_of_month
    ).select_related('account', 'third_party')

    balances = defaultdict(lambda: defaultdict(Decimal))

    for t in transactions:
        key = (t.account.code, t.account.name, t.third_party.nit, t.third_party.name)
        if t.date < first_day_of_month:
            balances[key]['saldo_anterior'] += t.debit - t.credit
        else:
            balances[key]['debitos'] += t.debit
            balances[key]['creditos'] += t.credit

    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    worksheet.title = "Balance de Prueba"

    worksheet.cell(row=1, column=1, value=f"{company.name} - NIT: {company.nit}").font = Font(bold=True, size=14)
    worksheet.cell(row=2, column=1, value="Balance de Prueba por Tercero").font = Font(bold=True, size=12)
    worksheet.cell(row=3, column=1, value=f"Fecha de Corte: {last_day_of_month.strftime('%Y-%m-%d')}").font = Font(italic=True)

    headers = ["Cuenta", "Nombre Cuenta", "NIT Tercero", "Nombre Tercero", "Saldo Anterior", "Débitos", "Créditos", "Saldo Final"]
    worksheet.append([])
    worksheet.append(headers)
    for cell in worksheet[5]:
        cell.font = Font(bold=True)

    sorted_keys = sorted(balances.keys(), key=lambda x: x[0])
    row_num = 6
    for key in sorted_keys:
        data = balances[key]
        saldo_anterior = data['saldo_anterior']
        debitos = data['debitos']
        creditos = data['creditos']

        if saldo_anterior == 0 and debitos == 0 and creditos == 0:
            continue

        saldo_final = saldo_anterior + debitos - creditos

        account_code, account_name, third_party_nit, third_party_name = key

        row_data = [
            account_code,
            account_name,
            third_party_nit,
            third_party_name,
            saldo_anterior,
            debitos,
            creditos,
            saldo_final
        ]

        for col_num, cell_value in enumerate(row_data, 1):
            cell = worksheet.cell(row=row_num, column=col_num, value=cell_value)
            if isinstance(cell_value, Decimal):
                cell.number_format = '#,##0.00'
        row_num += 1

    for col in worksheet.columns:
        max_length = 0
        column = col[0].column_letter
        for cell in col:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = (max_length + 2)
        worksheet.column_dimensions[column].width = adjusted_width

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="balance_de_prueba_{company.name}_{year}_{month}.xlsx"'
    workbook.save(response)

    return response
