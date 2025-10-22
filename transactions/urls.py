from django.urls import path
from .views import transaction_list, export_to_excel, company_list, account_list, third_party_list

urlpatterns = [
    path('transactions/', transaction_list, name='transaction_list'),
    path('export-excel/<int:company_id>/<int:year>/<int:month>/', export_to_excel, name='export_excel'),
    path('companies/', company_list, name='company_list'),
    path('accounts/', account_list, name='account_list'),
    path('third-parties/', third_party_list, name='third_party_list'),
]
