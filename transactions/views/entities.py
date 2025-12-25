# transactions/views/entities.py
"""
Vistas para entidades básicas: empresas, cuentas, terceros.
"""

from .base import *


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
    """Lista de cuentas con jerarquía"""
    accounts = Account.objects.all().order_by('code')
    serializer = AccountSerializer(accounts, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated, HasValidLicense])
def third_party_list(request):
    """Lista de terceros"""
    third_parties = ThirdParty.objects.all()
    serializer = ThirdPartySerializer(third_parties, many=True)
    return Response(serializer.data)
