from django.db import models

class Company(models.Model):
    name = models.CharField(max_length=255)
    nit = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.name

class ThirdParty(models.Model):
    name = models.CharField(max_length=255)
    nit = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.name

class Account(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.code} - {self.name}"

class Transaction(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    date = models.DateField()
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    third_party = models.ForeignKey(ThirdParty, on_delete=models.CASCADE)
    concept = models.CharField(max_length=255)
    additional_description = models.TextField(blank=True, null=True)
    debit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    credit = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.date} - {self.account} - {self.concept}"

class RecurringTransaction(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    third_party = models.ForeignKey(ThirdParty, on_delete=models.CASCADE)
    concept = models.CharField(max_length=255)
    additional_description = models.TextField(blank=True, null=True)
    debit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    credit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    day_of_month = models.IntegerField()

    def __str__(self):
        return f"Recurring: {self.account} - {self.concept}"

class License(models.Model):
    user = models.OneToOneField('auth.User', on_delete=models.CASCADE)
    expiration_date = models.DateField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"License for {self.user.username}"
