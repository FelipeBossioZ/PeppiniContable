# transactions/urls.py
from django.urls import path
from .views import (
    transaction_list, 
    company_list, 
    account_list, 
    third_party_list,
    movement_list,
    export_to_excel_enhanced, 
    dashboard_stats, 
    generate_recurring_transactions,
    corregir_transaccion,
    calcular_correcciones,
    validate_transaction,
    procesar_facturas_dian_excel,
    procesar_archivo_comprimido,
    accounting_rules_list,
    delete_accounting_rule,
    edit_transaction,
    edit_movement,
    delete_or_cancel_transaction,
)

urlpatterns = [
    # ==============================================
    # URLs BÁSICAS
    # ==============================================
    path('transactions/', transaction_list, name='transaction_list'),
    path('companies/', company_list, name='company_list'),
    path('accounts/', account_list, name='account_list'),
    path('third-parties/', third_party_list, name='third_party_list'),
    path('movements/', movement_list, name='movement_list'),
    path('transactions/<int:transaction_id>/corregir/', corregir_transaccion, name='corregir_transaccion'),
    path('transactions/<int:transaction_id>/calcular-correcciones/', calcular_correcciones, name='calcular_correcciones'),
    path('transactions/validate/', validate_transaction, name='validate_transaction'),
    path('procesar-facturas-excel/', procesar_facturas_dian_excel, name='procesar-facturas-excel'),
    path('procesar-comprimido/', procesar_archivo_comprimido, name='procesar-comprimido'),
    # 🤖 SISTEMA INTELIGENTE DE CLASIFICACIÓN
    path('accounting-rules/', accounting_rules_list, name='accounting-rules-list'),
    path('accounting-rules/<int:rule_id>/delete/', delete_accounting_rule, name='delete-accounting-rule'),
    
    # ✏️ EDICIÓN DE TRANSACCIONES
    path('transactions/<int:transaction_id>/edit/', edit_transaction, name='edit-transaction'),
    path('movements/<int:movement_id>/edit/', edit_movement, name='edit-movement'),

    # 🗑️ ELIMINACIÓN/ANULACIÓN HÍBRIDA
    path('transactions/<int:transaction_id>/delete/', delete_or_cancel_transaction, name='delete-or-cancel-transaction'),
    
    # ==============================================
    # URLs MEJORADAS - PARTIDA DOBLE
    # ==============================================
    path('export-excel/<int:company_id>/<int:year>/<int:month>/', 
         export_to_excel_enhanced, name='export_excel'),
    path('dashboard/stats/', dashboard_stats, name='dashboard_stats'),
    path('recurring/generate/', generate_recurring_transactions, 
         name='generate_recurring'),
]

# ==============================================
# ALIAS PARA COMPATIBILIDAD
# ==============================================
export_to_excel = export_to_excel_enhanced