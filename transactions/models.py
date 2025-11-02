from django.db import models
from django.core.exceptions import ValidationError

class Company(models.Model):
    name = models.CharField(max_length=255)
    nit = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.name

class ThirdParty(models.Model):
    name = models.CharField(max_length=255)
    nit = models.CharField(max_length=20, unique=True)
    alias = models.CharField(max_length=100, blank=True, null=True)  # 🔥 NUEVO: Para búsquedas inteligentes

    def __str__(self):
        return self.name
# AGREGAR al modelo Account
class Account(models.Model):
    TIPO_CUENTA_CHOICES = [
        ('ACTIVO', 'Activo'),
        ('PASIVO', 'Pasivo'),
        ('PATRIMONIO', 'Patrimonio'),
        ('INGRESO', 'Ingreso'),
        ('GASTO', 'Gasto'),
        ('ORDEN_DEUDOR', 'Orden Deudor'),
        ('ORDEN_ACREEDOR', 'Orden Acreedor'),
    ]
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=255)
    tipo = models.CharField(max_length=20, choices=TIPO_CUENTA_CHOICES, default='ACTIVO')  # ← NUEVO
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    level = models.IntegerField(default=1)
    is_group = models.BooleanField(default=False)
        # 🔥 NUEVO: Detectar tipo automáticamente por código PUC
    def detectar_tipo_automatico(self):
        if self.code.startswith(('1', '14', '15', '16')):  # Activos
            return 'ACTIVO'
        elif self.code.startswith(('2', '25', '26', '27')):  # Pasivos
            return 'PASIVO'
        elif self.code.startswith(('3', '33', '34', '35')):  # Patrimonio
            return 'PATRIMONIO'
        elif self.code.startswith(('4', '41', '42', '43')):  # Ingresos
            return 'INGRESO'
        elif self.code.startswith(('5', '51', '52', '53')):  # Gastos
            return 'GASTO'
        elif self.code.startswith(('6', '7')):  # Orden
            return 'ORDEN_DEUDOR' if self.code.startswith('6') else 'ORDEN_ACREEDOR'
        return 'ACTIVO'  # Default
    def save(self, *args, **kwargs):
        if not self.tipo:  # Si no tiene tipo, detectar automáticamente
            self.tipo = self.detectar_tipo_automatico()
        super().save(*args, **kwargs)

class Transaction(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    date = models.DateField()
    concept = models.CharField(max_length=255)
    additional_description = models.TextField(blank=True, null=True)
    number = models.CharField(max_length=20, unique=True)
    
    class Meta:
        ordering = ['-date', '-id']

    def __str__(self):
        return f"Comp #{self.number} - {self.date} - {self.concept}"
    
    def clean(self):
        """Validación automática débito = crédito + lógica contable"""
        movimientos = self.movements.all()
        
        # Validación básica (débito = crédito)
        if movimientos:
            total_debit = sum(m.debit for m in movimientos)
            total_credit = sum(m.credit for m in movimientos)
            
            if total_debit != total_credit:
                raise ValidationError(
                    f"EL ASIENTO NO CUADRA: Débito ${total_debit} ≠ Crédito ${total_credit}"
                )
        
        # 🔥 NUEVO: Validación inteligente
        if self.pk:  # Solo si ya está guardado (tiene movimientos)
            alertas, sugerencias = self.validar_logica_contable()
            if alertas:
                print("🚨 ALERTAS CONTABLES:", alertas)
                print("💡 SUGERENCIAS:", sugerencias)

    def save(self, *args, **kwargs):
        if not self.number:
            last_transaction = Transaction.objects.order_by('-id').first()
            last_number = int(last_transaction.number.split('-')[1]) if last_transaction and last_transaction.number else 0
            self.number = f"TRX-{str(last_number + 1).zfill(5)}"
        super().save(*args, **kwargs)

    def validar_logica_contable(self):
        """Validación inteligente de movimientos contables"""
        alertas = []
        sugerencias = []
        
        for movimiento in self.movements.all():
            cuenta = movimiento.account
            tipo_cuenta = cuenta.tipo
            
            if movimiento.debit > 0:
                if tipo_cuenta in ['PASIVO', 'INGRESO']:
                    alertas.append(f"⚠️ DÉBITO a {cuenta.code} - {cuenta.name} ({tipo_cuenta})")
                    sugerencias.append(f"Los {tipo_cuenta.lower()} normalmente disminuyen con DÉBITO")
                    
            elif movimiento.credit > 0:
                if tipo_cuenta in ['ACTIVO', 'GASTO']:
                    alertas.append(f"⚠️ CRÉDITO a {cuenta.code} - {cuenta.name} ({tipo_cuenta})")
                    sugerencias.append(f"Los {tipo_cuenta.lower()} normalmente disminuyen con CRÉDITO")
        
        return alertas, sugerencias

class Movement(models.Model):  # 🔥 NUEVO: Modelo para múltiples movimientos por transacción
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='movements')
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    third_party = models.ForeignKey(ThirdParty, on_delete=models.CASCADE)
    debit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    credit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    description = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-debit', 'account__code']  # Débitos primero, luego por código

    def __str__(self):
        return f"Mov: {self.account.code} - D:${self.debit} C:${self.credit}"

# 🔥 MANTENEMOS LOS MODELOS EXISTENTES PERO ACTUALIZAMOS:
class RecurringTransaction(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    # Cambiamos a múltiples movimientos también
    concept = models.CharField(max_length=255)
    additional_description = models.TextField(blank=True, null=True)
    day_of_month = models.IntegerField()

    def __str__(self):
        return f"Recurring: {self.concept}"

class License(models.Model):
    user = models.OneToOneField('auth.User', on_delete=models.CASCADE)
    expiration_date = models.DateField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"License for {self.user.username}"