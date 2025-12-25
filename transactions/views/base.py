# transactions/views/base.py
"""
Importaciones y utilidades compartidas por todos los módulos de vistas.
"""

from django.http import JsonResponse, HttpResponse
from django.db import transaction as db_transaction
from django.core.cache import cache
from django.core.paginator import Paginator
from django.db.models import Q, Sum, F, DecimalField
from django.utils import timezone
from django.conf import settings

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from transactions.models import (
    Transaction, Movement, Company, Account,
    ThirdParty, RecurringTransaction, AccountingRule
)
from transactions.serializers import (
    TransactionSerializer, TransactionCreateSerializer, MovementSerializer,
    CompanySerializer, AccountSerializer, ThirdPartySerializer
)
from transactions.permissions import HasValidLicense

from collections import defaultdict
from decimal import Decimal
from datetime import date, timedelta, datetime
from calendar import monthrange
import logging
import re

logger = logging.getLogger(__name__)

# Decoradores comunes
def authenticated_view(func):
    """Decorador que combina autenticación y licencia válida"""
    return api_view(['GET', 'POST', 'PUT', 'DELETE'])(
        permission_classes([IsAuthenticated, HasValidLicense])(func)
    )


def invalidate_company_cache(company_id):
    """Invalida el caché de una empresa"""
    cache_keys = [f'dashboard_{company_id}']
    cache.delete_many(cache_keys)


def paginate_queryset(queryset, request, default_page_size=50, max_page_size=100):
    """
    Pagina un queryset y retorna el objeto página con metadatos.
    """
    page_size = min(int(request.GET.get('page_size', default_page_size)), max_page_size)
    paginator = Paginator(queryset, page_size)
    page_number = request.GET.get('page', 1)

    try:
        page_obj = paginator.page(page_number)
    except Exception:
        return None, {
            'error': 'Página no válida',
            'status': status.HTTP_400_BAD_REQUEST
        }

    pagination_data = {
        'count': paginator.count,
        'total_pages': paginator.num_pages,
        'current_page': page_obj.number,
        'has_next': page_obj.has_next(),
        'has_previous': page_obj.has_previous(),
        'page_size': page_size
    }

    return page_obj, pagination_data
