from django.core.management.base import BaseCommand
from transactions.models import RecurringTransaction, Transaction
from datetime import date

class Command(BaseCommand):
    help = 'Create transactions from recurring transactions for the current month'

    def handle(self, *args, **kwargs):
        today = date.today()
        recurring_transactions = RecurringTransaction.objects.filter(day_of_month=today.day)

        for rt in recurring_transactions:
            Transaction.objects.create(
                company=rt.company,
                date=today,
                account=rt.account,
                third_party=rt.third_party,
                concept=rt.concept,
                additional_description=rt.additional_description,
                debit=rt.debit,
                credit=rt.credit,
            )
            self.stdout.write(self.style.SUCCESS(f'Successfully created transaction for {rt.concept}'))
