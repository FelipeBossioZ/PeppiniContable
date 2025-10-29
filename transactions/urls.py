# transactions/urls.py
from django.urls import path
from .views import (
    transaction_list, 
    company_list, 
    account_list, 
    third_party_list,
    # Importar solo lo que ya tienes implementado
)

urlpatterns = [
    path('transactions/', transaction_list, name='transaction_list'),
    path('companies/', company_list, name='company_list'),
    path('accounts/', account_list, name='account_list'),
    path('third-parties/', third_party_list, name='third_party_list'),
]

# Si ya implementaste las vistas mejoradas, agrega estas líneas:
try:
    from .views import export_to_excel_enhanced, dashboard_stats, generate_recurring_transactions
    
    # Agregar las nuevas rutas
    urlpatterns += [
        path('export-excel/<int:company_id>/<int:year>/<int:month>/', 
             export_to_excel_enhanced, name='export_excel'),
        path('dashboard/stats/', dashboard_stats, name='dashboard_stats'),
        path('recurring/generate/', generate_recurring_transactions, 
             name='generate_recurring'),
    ]
except ImportError:
    # Si no has implementado las nuevas vistas, usar la antigua
    try:
        from .views import export_to_excel
        urlpatterns += [
            path('export-excel/<int:company_id>/<int:year>/<int:month>/', 
                 export_to_excel, name='export_excel'),
        ]
    except ImportError:
        pass  # La función export_to_excel no existe aún