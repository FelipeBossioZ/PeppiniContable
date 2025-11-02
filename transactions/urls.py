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
    corregir_transaccion
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