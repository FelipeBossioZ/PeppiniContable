from django.contrib import admin
from .models import Company, ThirdParty, Account, Transaction, RecurringTransaction, License

admin.site.register(Company)
admin.site.register(ThirdParty)
admin.site.register(Account)
admin.site.register(Transaction)
admin.site.register(RecurringTransaction)
admin.site.register(License)
