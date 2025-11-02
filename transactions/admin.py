#transactios/admin.py
from django.contrib import admin
from .models import Company, ThirdParty, Account, Transaction, Movement, RecurringTransaction, License

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ['name', 'nit', 'get_transaction_count']
    search_fields = ['name', 'nit']
    
    def get_transaction_count(self, obj):
        return obj.transaction_set.count()
    get_transaction_count.short_description = 'Transacciones'

@admin.register(ThirdParty)
class ThirdPartyAdmin(admin.ModelAdmin):
    list_display = ['name', 'nit', 'alias', 'get_transaction_count']
    search_fields = ['name', 'nit', 'alias']
    
    def get_transaction_count(self, obj):
        return obj.movement_set.count()
    get_transaction_count.short_description = 'Movimientos'

@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'parent', 'level', 'is_group']
    list_filter = ['level', 'is_group']
    search_fields = ['code', 'name']
    ordering = ['code']

class MovementInline(admin.TabularInline):
    model = Movement
    extra = 2
    fields = ['account', 'third_party', 'debit', 'credit', 'description']

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['number', 'date', 'company', 'concept', 'get_total_debit', 'get_total_credit']
    list_filter = ['date', 'company']
    search_fields = ['number', 'concept', 'company__name']
    inlines = [MovementInline]
    
    def get_total_debit(self, obj):
        return sum(m.debit for m in obj.movements.all())
    get_total_debit.short_description = 'Total Débito'
    
    def get_total_credit(self, obj):
        return sum(m.credit for m in obj.movements.all())
    get_total_credit.short_description = 'Total Crédito'

@admin.register(Movement)
class MovementAdmin(admin.ModelAdmin):
    list_display = ['transaction', 'account', 'third_party', 'debit', 'credit']
    list_filter = ['account', 'third_party']
    search_fields = ['transaction__number', 'account__name', 'third_party__name']

@admin.register(RecurringTransaction)
class RecurringTransactionAdmin(admin.ModelAdmin):
    list_display = ['concept', 'company', 'day_of_month']
    list_filter = ['company', 'day_of_month']

@admin.register(License)
class LicenseAdmin(admin.ModelAdmin):
    list_display = ['user', 'expiration_date', 'is_active', 'get_days_remaining']
    list_filter = ['is_active', 'expiration_date']
    
    def get_days_remaining(self, obj):
        from datetime import date
        delta = obj.expiration_date - date.today()
        return max(0, delta.days)
    get_days_remaining.short_description = 'Días Restantes'