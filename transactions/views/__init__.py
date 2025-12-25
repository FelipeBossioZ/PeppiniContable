# transactions/views/__init__.py
"""
Vistas modularizadas para el sistema contable.
Refactorizado desde views.py monolítico para mejor mantenibilidad.
"""

# Transacciones CRUD
from .transactions import (
    transaction_list,
    edit_transaction,
    delete_or_cancel_transaction,
)

# Movimientos
from .movements import (
    movement_list,
    edit_movement,
)

# Dashboard y estadísticas
from .dashboard import dashboard_stats

# Exportación
from .export import export_to_excel_enhanced, export_to_excel

# Entidades básicas
from .entities import (
    company_list,
    account_list,
    third_party_list,
)

# Validación y corrección
from .validation import (
    validate_transaction,
    corregir_transaccion,
    calcular_correcciones,
)

# Procesamiento DIAN
from .dian import (
    procesar_facturas_dian_excel,
    procesar_archivo_comprimido,
)

# Reglas de clasificación
from .classification import (
    accounting_rules_list,
    delete_accounting_rule,
    clasificar_gasto_inteligente,
    clasificar_por_palabras_clave,
    aprender_de_edicion,
)

# Transacciones recurrentes
from .recurring import generate_recurring_transactions

__all__ = [
    # Transacciones
    'transaction_list',
    'edit_transaction',
    'delete_or_cancel_transaction',
    # Movimientos
    'movement_list',
    'edit_movement',
    # Dashboard
    'dashboard_stats',
    # Export
    'export_to_excel_enhanced',
    'export_to_excel',
    # Entidades
    'company_list',
    'account_list',
    'third_party_list',
    # Validación
    'validate_transaction',
    'corregir_transaccion',
    'calcular_correcciones',
    # DIAN
    'procesar_facturas_dian_excel',
    'procesar_archivo_comprimido',
    # Clasificación
    'accounting_rules_list',
    'delete_accounting_rule',
    'clasificar_gasto_inteligente',
    'clasificar_por_palabras_clave',
    'aprender_de_edicion',
    # Recurrentes
    'generate_recurring_transactions',
]
