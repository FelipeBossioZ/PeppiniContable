# transactions/utils.py
"""
Utilidades y funciones helper para el sistema contable PeppiniContable
"""

import re
import logging
from decimal import Decimal, InvalidOperation
from datetime import date, datetime
from typing import Optional, Tuple, Dict, Any, List

from django.conf import settings
from django.core.cache import cache
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


# ==============================================================================
# CONSTANTES
# ==============================================================================

# Cuentas especiales con comportamiento invertido
CUENTAS_ESPECIALES_DEBITO = ['4175']  # Devoluciones en ventas (ingreso que aumenta con débito)
CUENTAS_ESPECIALES_CREDITO = ['5905']  # Gastos recuperados (gasto que aumenta con crédito)

# Códigos PUC para clasificación automática
CLASIFICACION_GASTOS = {
    '5120': ['arriendo', 'alquiler', 'renta', 'arrendamiento', 'lease', 'canon'],
    '5105': ['honorarios', 'nomina', 'nómina', 'salario', 'sueldo', 'prestaciones', 'personal'],
    '5135': ['servicios', 'aseo', 'vigilancia', 'limpieza'],
    '5140': ['impuesto', 'gravamen', 'predial', 'vehicular', 'ica', 'reteica', 'iva'],
    '5130': ['seguros', 'póliza', 'aseguradora', 'poliza', 'seguro'],
    '5115': ['celular', 'internet', 'telecomunicaciones', 'telefono', 'teléfono', 'datos', 'móvil'],
    '5145': ['mantenimiento', 'reparación', 'reparacion', 'repuesto', 'taller'],
    '5110': ['publicidad', 'propaganda', 'marketing', 'anuncios'],
    '5125': ['papelería', 'papeleria', 'útiles', 'utiles', 'oficina'],
    '5155': ['transporte', 'flete', 'envío', 'envio', 'mensajería'],
    '5160': ['combustible', 'gasolina', 'diesel', 'acpm'],
    '5195': [],  # Gastos diversos (default)
}

# Tipos de cuenta por primer dígito PUC
TIPO_CUENTA_POR_DIGITO = {
    '1': 'ACTIVO',
    '2': 'PASIVO',
    '3': 'PATRIMONIO',
    '4': 'INGRESO',
    '5': 'GASTO',
    '6': 'COSTO',
    '7': 'COSTO',
    '8': 'ORDEN_DEUDOR',
    '9': 'ORDEN_ACREEDOR',
}

# Naturaleza por tipo de cuenta
NATURALEZA_POR_TIPO = {
    'ACTIVO': 'DEBITO',
    'GASTO': 'DEBITO',
    'COSTO': 'DEBITO',
    'ORDEN_DEUDOR': 'DEBITO',
    'PASIVO': 'CREDITO',
    'PATRIMONIO': 'CREDITO',
    'INGRESO': 'CREDITO',
    'ORDEN_ACREEDOR': 'CREDITO',
}


# ==============================================================================
# EXCEPTION HANDLER PERSONALIZADO
# ==============================================================================

def custom_exception_handler(exc, context):
    """
    Manejador de excepciones personalizado para la API REST.
    Proporciona respuestas de error consistentes y detalladas.
    """
    # Llamar al manejador por defecto primero
    response = exception_handler(exc, context)

    if response is not None:
        # Personalizar la respuesta
        custom_response_data = {
            'success': False,
            'error': {
                'code': response.status_code,
                'message': get_error_message(response.status_code),
                'details': response.data
            }
        }

        # Agregar información adicional en modo debug
        if settings.DEBUG:
            custom_response_data['error']['exception'] = str(exc)
            custom_response_data['error']['view'] = context.get('view').__class__.__name__ if context.get('view') else None

        response.data = custom_response_data

        # Log del error
        logger.warning(
            f"API Error {response.status_code}: {exc} - View: {context.get('view')}"
        )

    return response


def get_error_message(status_code: int) -> str:
    """Devuelve un mensaje de error legible según el código de estado"""
    messages = {
        400: 'Solicitud incorrecta',
        401: 'No autorizado',
        403: 'Acceso denegado',
        404: 'Recurso no encontrado',
        405: 'Método no permitido',
        409: 'Conflicto',
        422: 'Datos no procesables',
        429: 'Demasiadas solicitudes',
        500: 'Error interno del servidor',
        502: 'Bad Gateway',
        503: 'Servicio no disponible',
    }
    return messages.get(status_code, 'Error desconocido')


# ==============================================================================
# UTILIDADES DE FORMATO
# ==============================================================================

def format_currency(amount: Decimal, currency: str = 'COP') -> str:
    """
    Formatea un monto como moneda colombiana.

    Args:
        amount: Monto a formatear
        currency: Código de moneda (por defecto COP)

    Returns:
        String formateado (ej: "$1.234.567,89")
    """
    if amount is None:
        return "$0"

    try:
        amount = Decimal(str(amount))
        # Formatear con separadores colombianos
        formatted = "{:,.2f}".format(amount)
        # Cambiar separadores (US -> CO)
        formatted = formatted.replace(',', 'X').replace('.', ',').replace('X', '.')
        return f"${formatted}"
    except (InvalidOperation, ValueError):
        return "$0"


def format_nit(nit: str) -> str:
    """
    Formatea un NIT colombiano con guiones.

    Args:
        nit: NIT sin formato

    Returns:
        NIT formateado (ej: "900.123.456-7")
    """
    # Limpiar caracteres no numéricos
    clean_nit = re.sub(r'[^\d]', '', str(nit))

    if len(clean_nit) < 2:
        return clean_nit

    # Separar dígito de verificación
    base = clean_nit[:-1]
    dv = clean_nit[-1]

    # Agregar puntos cada 3 dígitos
    formatted_base = ""
    for i, digit in enumerate(reversed(base)):
        if i > 0 and i % 3 == 0:
            formatted_base = "." + formatted_base
        formatted_base = digit + formatted_base

    return f"{formatted_base}-{dv}"


def clean_nit(nit: str) -> str:
    """
    Limpia un NIT, dejando solo números.

    Args:
        nit: NIT con cualquier formato

    Returns:
        Solo números
    """
    if not nit:
        return ''
    return re.sub(r'[^\d]', '', str(nit))


def parse_date(date_str: Any) -> Optional[date]:
    """
    Parsea una fecha de múltiples formatos.

    Args:
        date_str: Fecha en string o datetime

    Returns:
        Objeto date o None si no se puede parsear
    """
    if not date_str:
        return None

    if isinstance(date_str, date):
        return date_str

    if isinstance(date_str, datetime):
        return date_str.date()

    # Formatos comunes en Colombia
    formats = [
        '%d/%m/%Y',
        '%d-%m-%Y',
        '%Y-%m-%d',
        '%d.%m.%Y',
        '%Y/%m/%d',
    ]

    date_str = str(date_str).strip()

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue

    # Intentar con pandas si está disponible
    try:
        import pandas as pd
        parsed = pd.to_datetime(date_str, dayfirst=True)
        return parsed.date()
    except Exception:
        pass

    logger.warning(f"No se pudo parsear la fecha: {date_str}")
    return None


def safe_decimal(value: Any, default: Decimal = Decimal('0')) -> Decimal:
    """
    Convierte un valor a Decimal de forma segura.

    Args:
        value: Valor a convertir
        default: Valor por defecto si falla la conversión

    Returns:
        Valor como Decimal
    """
    if value is None:
        return default

    try:
        if isinstance(value, Decimal):
            return value
        return Decimal(str(value).replace(',', '.'))
    except (InvalidOperation, ValueError):
        return default


# ==============================================================================
# UTILIDADES DE CLASIFICACIÓN
# ==============================================================================

def clasificar_gasto_por_texto(texto: str, company_id: Optional[int] = None) -> str:
    """
    Clasifica un gasto por palabras clave en el texto.

    Args:
        texto: Texto a analizar (nombre del tercero, concepto, etc.)
        company_id: ID de la empresa para reglas específicas

    Returns:
        Código de cuenta PUC
    """
    if not texto:
        return settings.ACCOUNTING_SETTINGS.get('DEFAULT_EXPENSE_ACCOUNT', '5195')

    texto_lower = texto.lower()

    # Primero buscar en clasificación general
    for cuenta, keywords in CLASIFICACION_GASTOS.items():
        if any(keyword in texto_lower for keyword in keywords):
            return cuenta

    # Reglas específicas por empresa (podrían cargarse de BD)
    # Por ahora hardcodeadas
    REGLAS_POR_EMPRESA = {
        3: {  # CORTIJO DE RESTREPO SAS
            '5120': ['consultorio', 'oficina', 'local', 'bodega'],
            '5140': ['camara de comercio', 'registro mercantil'],
        }
    }

    if company_id and company_id in REGLAS_POR_EMPRESA:
        for cuenta, keywords in REGLAS_POR_EMPRESA[company_id].items():
            if any(keyword in texto_lower for keyword in keywords):
                return cuenta

    # Default
    return settings.ACCOUNTING_SETTINGS.get('DEFAULT_EXPENSE_ACCOUNT', '5195')


def detectar_tipo_cuenta(codigo: str) -> str:
    """
    Detecta el tipo de cuenta según el código PUC.

    Args:
        codigo: Código de la cuenta

    Returns:
        Tipo de cuenta (ACTIVO, PASIVO, etc.)
    """
    if not codigo:
        return 'ACTIVO'

    primer_digito = codigo[0]
    return TIPO_CUENTA_POR_DIGITO.get(primer_digito, 'ACTIVO')


def detectar_naturaleza(tipo_cuenta: str) -> str:
    """
    Detecta la naturaleza de una cuenta según su tipo.

    Args:
        tipo_cuenta: Tipo de cuenta

    Returns:
        Naturaleza (DEBITO o CREDITO)
    """
    return NATURALEZA_POR_TIPO.get(tipo_cuenta, 'DEBITO')


# ==============================================================================
# UTILIDADES DE VALIDACIÓN
# ==============================================================================

def validar_nit(nit: str) -> Tuple[bool, str]:
    """
    Valida un NIT colombiano.

    Args:
        nit: NIT a validar

    Returns:
        Tupla (es_valido, mensaje)
    """
    clean = clean_nit(nit)

    if not clean:
        return False, "NIT vacío"

    if len(clean) < 9:
        return False, "NIT muy corto"

    if len(clean) > 10:
        return False, "NIT muy largo"

    # Validar dígito de verificación (algoritmo módulo 11)
    if len(clean) >= 10:
        base = clean[:-1]
        dv = int(clean[-1])

        # Pesos del algoritmo
        pesos = [3, 7, 13, 17, 19, 23, 29, 37, 41, 43, 47, 53, 59, 67, 71]

        suma = 0
        for i, digito in enumerate(reversed(base)):
            suma += int(digito) * pesos[i]

        residuo = suma % 11
        dv_calculado = 11 - residuo if residuo >= 2 else residuo

        if dv_calculado != dv:
            return False, f"Dígito de verificación incorrecto (debería ser {dv_calculado})"

    return True, "NIT válido"


def validar_balance(debito: Decimal, credito: Decimal, tolerancia: Decimal = Decimal('0.01')) -> Tuple[bool, Decimal]:
    """
    Valida que débito y crédito estén balanceados.

    Args:
        debito: Total débito
        credito: Total crédito
        tolerancia: Diferencia permitida

    Returns:
        Tupla (está_balanceado, diferencia)
    """
    diferencia = abs(debito - credito)
    return diferencia <= tolerancia, diferencia


# ==============================================================================
# UTILIDADES DE CACHÉ
# ==============================================================================

def get_cached_or_compute(key: str, compute_func, timeout: int = None):
    """
    Obtiene un valor del caché o lo computa si no existe.

    Args:
        key: Clave del caché
        compute_func: Función para computar el valor si no está en caché
        timeout: Tiempo de expiración en segundos

    Returns:
        Valor del caché o computado
    """
    if timeout is None:
        timeout = settings.CACHE_TTL

    cached = cache.get(key)
    if cached is not None:
        return cached

    value = compute_func()
    cache.set(key, value, timeout)
    return value


def invalidate_cache_for_company(company_id: int):
    """
    Invalida todo el caché relacionado con una empresa.

    Args:
        company_id: ID de la empresa
    """
    cache_keys = [
        f'dashboard_{company_id}',
        f'stats_{company_id}',
        f'accounts_{company_id}',
        f'third_parties_{company_id}',
    ]
    cache.delete_many(cache_keys)


# ==============================================================================
# UTILIDADES DE AUDITORÍA
# ==============================================================================

def log_audit(
    user,
    action: str,
    model_name: str,
    object_id: int,
    object_repr: str,
    changes: Dict[str, Any] = None,
    request=None
):
    """
    Registra una acción en el log de auditoría.

    Args:
        user: Usuario que realiza la acción
        action: Tipo de acción (CREATE, UPDATE, DELETE, etc.)
        model_name: Nombre del modelo afectado
        object_id: ID del objeto afectado
        object_repr: Representación del objeto
        changes: Diccionario con los cambios realizados
        request: Request HTTP para obtener IP y User Agent
    """
    from .models import AuditLog

    ip_address = None
    user_agent = None

    if request:
        # Obtener IP real (considerando proxies)
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0].strip()
        else:
            ip_address = request.META.get('REMOTE_ADDR')

        user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]

    try:
        AuditLog.objects.create(
            user=user,
            action=action,
            model_name=model_name,
            object_id=object_id,
            object_repr=object_repr[:255],
            changes=changes,
            ip_address=ip_address,
            user_agent=user_agent
        )
    except Exception as e:
        logger.error(f"Error creando log de auditoría: {e}")


# ==============================================================================
# UTILIDADES DE EXPORTACIÓN
# ==============================================================================

def get_excel_column_letter(col_num: int) -> str:
    """
    Convierte un número de columna a letra de Excel.

    Args:
        col_num: Número de columna (1-indexed)

    Returns:
        Letra(s) de columna (A, B, ..., Z, AA, AB, ...)
    """
    result = ""
    while col_num > 0:
        col_num, remainder = divmod(col_num - 1, 26)
        result = chr(65 + remainder) + result
    return result


def sanitize_excel_sheet_name(name: str) -> str:
    """
    Sanitiza un nombre para usarlo como nombre de hoja en Excel.

    Args:
        name: Nombre original

    Returns:
        Nombre sanitizado
    """
    # Caracteres no permitidos en nombres de hojas de Excel
    invalid_chars = ['\\', '/', '*', '?', ':', '[', ']']

    for char in invalid_chars:
        name = name.replace(char, '_')

    # Limitar a 31 caracteres
    return name[:31]


# ==============================================================================
# UTILIDADES DE PROCESAMIENTO
# ==============================================================================

def chunk_list(lst: List, chunk_size: int) -> List[List]:
    """
    Divide una lista en chunks de tamaño específico.

    Args:
        lst: Lista a dividir
        chunk_size: Tamaño de cada chunk

    Returns:
        Lista de chunks
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def retry_on_failure(func, max_retries: int = 3, delay: float = 1.0):
    """
    Decorator para reintentar una función en caso de fallo.

    Args:
        func: Función a ejecutar
        max_retries: Número máximo de reintentos
        delay: Delay entre reintentos en segundos
    """
    import time
    from functools import wraps

    @wraps(func)
    def wrapper(*args, **kwargs):
        last_exception = None
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < max_retries - 1:
                    time.sleep(delay * (attempt + 1))  # Backoff exponencial
                    logger.warning(f"Reintento {attempt + 1}/{max_retries} para {func.__name__}: {e}")
        raise last_exception

    return wrapper
