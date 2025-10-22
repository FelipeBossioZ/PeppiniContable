from django.urls import path
from .views import transaction_list, export_to_excel

urlpatterns = [
    path('transactions/', transaction_list, name='transaction_list'),
    path('export-excel/<int:company_id>/<int:year>/<int:month>/', export_to_excel, name='export_excel'),
]
