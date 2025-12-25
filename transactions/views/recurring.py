# transactions/views/recurring.py
"""
Vista para transacciones recurrentes.
"""

from .base import *


@api_view(['POST'])
@permission_classes([IsAuthenticated, HasValidLicense])
def generate_recurring_transactions(request):
    """
    Genera transacciones recurrentes.
    """
    # TODO: Implementar lógica completa de transacciones recurrentes
    return Response({
        'message': 'Funcionalidad de transacciones recurrentes en desarrollo',
        'created': 0,
        'skipped': 0,
        'errors': 0
    }, status=status.HTTP_200_OK)
