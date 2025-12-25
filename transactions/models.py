# transactions/models.py
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal


class TimestampMixin(models.Model):
    """Mixin para agregar campos de auditoría a todos los modelos"""
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última actualización")

    class Meta:
        abstract = True


class SoftDeleteMixin(models.Model):
    """Mixin para soft-delete (nunca eliminar, solo marcar como inactivo)"""
    is_deleted = models.BooleanField(default=False, db_index=True, verbose_name="Eliminado")
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de eliminación")

    class Meta:
        abstract = True

    def soft_delete(self):
        """Marca el registro como eliminado sin borrarlo de la BD"""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_at'])

    def restore(self):
        """Restaura un registro eliminado"""
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=['is_deleted', 'deleted_at'])


class Company(TimestampMixin, models.Model):
    """Empresa/Compañía para multi-tenancy"""
    name = models.CharField(max_length=200, verbose_name="Nombre")
    nit = models.CharField(max_length=20, unique=True, db_index=True, verbose_name="NIT")
    transaction_prefix = models.CharField(
        max_length=10,
        default='TRX',
        help_text='Prefijo para números de comprobante (ej: TRX, CRTJ)'
    )
    # Nuevos campos útiles
    address = models.TextField(blank=True, null=True, verbose_name="Dirección")
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Teléfono")
    email = models.EmailField(blank=True, null=True, verbose_name="Email")
    is_active = models.BooleanField(default=True, db_index=True, verbose_name="Activo")

    class Meta:
        verbose_name = "Empresa"
        verbose_name_plural = "Empresas"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.nit})"

    def get_next_transaction_number(self):
        """Genera el siguiente número de transacción para esta empresa"""
        last_transaction = Transaction.objects.filter(
            company=self,
            number__startswith=self.transaction_prefix
        ).order_by('-id').first()

        if last_transaction and last_transaction.number:
            try:
                last_num = int(last_transaction.number.split('-')[-1])
                new_num = last_num + 1
            except (ValueError, IndexError):
                new_num = 1
        else:
            new_num = 1

        return f"{self.transaction_prefix}-{new_num:05d}"


class ThirdParty(TimestampMixin, SoftDeleteMixin, models.Model):
    """Terceros (Clientes, Proveedores, etc.)"""
    name = models.CharField(max_length=255, db_index=True, verbose_name="Nombre")
    nit = models.CharField(max_length=20, unique=True, db_index=True, verbose_name="NIT")
    alias = models.CharField(max_length=100, blank=True, null=True, verbose_name="Alias")
    # Nuevos campos útiles
    email = models.EmailField(blank=True, null=True, verbose_name="Email")
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Teléfono")
    address = models.TextField(blank=True, null=True, verbose_name="Dirección")
    contact_name = models.CharField(max_length=200, blank=True, null=True, verbose_name="Contacto")
    notes = models.TextField(blank=True, null=True, verbose_name="Notas")

    class Meta:
        verbose_name = "Tercero"
        verbose_name_plural = "Terceros"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} - {self.nit}"

    @property
    def display_name(self):
        """Nombre para mostrar (alias o nombre completo)"""
        return self.alias if self.alias else self.name


class Account(TimestampMixin, models.Model):
    """Cuenta contable del PUC (Plan Único de Cuentas)"""
    TIPO_CUENTA_CHOICES = [
        ('ACTIVO', 'Activo'),
        ('PASIVO', 'Pasivo'),
        ('PATRIMONIO', 'Patrimonio'),
        ('INGRESO', 'Ingreso'),
        ('GASTO', 'Gasto'),
        ('COSTO', 'Costo'),
        ('ORDEN_DEUDOR', 'Orden Deudor'),
        ('ORDEN_ACREEDOR', 'Orden Acreedor'),
    ]

    NATURALEZA_CHOICES = [
        ('DEBITO', 'Débito'),
        ('CREDITO', 'Crédito'),
    ]

    code = models.CharField(max_length=20, unique=True, db_index=True, verbose_name="Código")
    name = models.CharField(max_length=255, db_index=True, verbose_name="Nombre")
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CUENTA_CHOICES,
        default='ACTIVO',
        db_index=True,
        verbose_name="Tipo"
    )
    naturaleza = models.CharField(
        max_length=10,
        choices=NATURALEZA_CHOICES,
        blank=True,
        null=True,
        verbose_name="Naturaleza"
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name="Cuenta padre"
    )
    level = models.IntegerField(default=1, db_index=True, verbose_name="Nivel")
    is_group = models.BooleanField(default=False, verbose_name="Es grupo")
    is_active = models.BooleanField(default=True, db_index=True, verbose_name="Activo")
    description = models.TextField(blank=True, null=True, verbose_name="Descripción")

    class Meta:
        verbose_name = "Cuenta Contable"
        verbose_name_plural = "Cuentas Contables"
        ordering = ['code']
        indexes = [
            models.Index(fields=['code', 'tipo']),
            models.Index(fields=['tipo', 'is_active']),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"

    @property
    def full_name(self):
        """Nombre completo con código"""
        return f"{self.code} - {self.name}"

    def detectar_tipo_automatico(self):
        """Detectar tipo automáticamente por código PUC colombiano"""
        if not self.code:
            return 'ACTIVO'

        first_digit = self.code[0]
        tipo_map = {
            '1': 'ACTIVO',
            '2': 'PASIVO',
            '3': 'PATRIMONIO',
            '4': 'INGRESO',
            '5': 'GASTO',
            '6': 'COSTO',
            '7': 'COSTO',  # Cuentas de orden / costo de producción
            '8': 'ORDEN_DEUDOR',
            '9': 'ORDEN_ACREEDOR',
        }
        return tipo_map.get(first_digit, 'ACTIVO')

    def detectar_naturaleza_automatica(self):
        """Detectar naturaleza automáticamente según tipo de cuenta"""
        # Activos, Gastos y Costos son de naturaleza débito
        if self.tipo in ['ACTIVO', 'GASTO', 'COSTO', 'ORDEN_DEUDOR']:
            return 'DEBITO'
        # Pasivos, Patrimonio e Ingresos son de naturaleza crédito
        return 'CREDITO'

    def save(self, *args, **kwargs):
        # Si no tiene tipo, detectar automáticamente
        if not self.tipo:
            self.tipo = self.detectar_tipo_automatico()

        # Si no tiene naturaleza, detectar automáticamente
        if not self.naturaleza:
            self.naturaleza = self.detectar_naturaleza_automatica()

        # Calcular nivel basado en longitud del código
        if self.code:
            self.level = len(self.code)

        super().save(*args, **kwargs)

    def get_balance(self):
        """Calcula el saldo actual de la cuenta"""
        from django.db.models import Sum
        totals = self.movement_set.aggregate(
            total_debit=Sum('debit'),
            total_credit=Sum('credit')
        )
        debit = totals['total_debit'] or Decimal('0')
        credit = totals['total_credit'] or Decimal('0')

        if self.naturaleza == 'DEBITO':
            return debit - credit
        return credit - debit


class Transaction(TimestampMixin, SoftDeleteMixin, models.Model):
    """Transacción/Comprobante contable (cabecera del asiento)"""
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='transactions',
        verbose_name="Empresa"
    )
    date = models.DateField(db_index=True, verbose_name="Fecha")
    concept = models.CharField(max_length=255, db_index=True, verbose_name="Concepto")
    additional_description = models.TextField(blank=True, null=True, verbose_name="Descripción adicional")
    number = models.CharField(max_length=20, unique=True, db_index=True, verbose_name="Número de comprobante")

    # Campos de auditoría
    created_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_transactions',
        verbose_name="Creado por"
    )

    class Meta:
        verbose_name = "Transacción"
        verbose_name_plural = "Transacciones"
        ordering = ['-date', '-id']
        indexes = [
            models.Index(fields=['company', 'date']),
            models.Index(fields=['company', '-date', '-id']),
            models.Index(fields=['date', 'is_deleted']),
        ]

    def __str__(self):
        return f"Comp #{self.number} - {self.date} - {self.concept}"

    def clean(self):
        """Validación automática débito = crédito + lógica contable"""
        if self.pk:  # Solo validar si ya existe (tiene movimientos)
            self._validate_balance()

    def _validate_balance(self):
        """Valida que el asiento esté balanceado"""
        movements = self.movements.all()
        if movements.exists():
            total_debit = sum(m.debit for m in movements)
            total_credit = sum(m.credit for m in movements)

            if abs(total_debit - total_credit) > Decimal('0.01'):
                raise ValidationError(
                    f"EL ASIENTO NO CUADRA: Débito ${total_debit} ≠ Crédito ${total_credit}"
                )

    def save(self, *args, **kwargs):
        if not self.number:
            self.number = self.company.get_next_transaction_number()
        super().save(*args, **kwargs)

    def validar_logica_contable(self):
        """Validación inteligente de movimientos contables"""
        alertas = []
        sugerencias = []

        # Cuentas especiales que tienen comportamiento invertido
        CUENTAS_ESPECIALES_DEBITO = ['4175']  # Devoluciones en ventas
        CUENTAS_ESPECIALES_CREDITO = ['5905']  # Gastos recuperados

        for movimiento in self.movements.all():
            cuenta = movimiento.account
            tipo_cuenta = cuenta.tipo
            codigo_cuenta = cuenta.code

            # Solo alertar para cuentas de resultado (no activos ni pasivos)
            if tipo_cuenta in ['ACTIVO', 'PASIVO']:
                continue

            if movimiento.debit > 0:
                if tipo_cuenta in ['PATRIMONIO', 'INGRESO'] and codigo_cuenta not in CUENTAS_ESPECIALES_DEBITO:
                    alertas.append(f"⚠️ DÉBITO a {cuenta.code} - {cuenta.name} ({tipo_cuenta})")
                    sugerencias.append(f"Los {tipo_cuenta.lower()}s normalmente aumentan con CRÉDITO")

            elif movimiento.credit > 0:
                if tipo_cuenta == 'GASTO' and codigo_cuenta not in CUENTAS_ESPECIALES_CREDITO:
                    alertas.append(f"⚠️ CRÉDITO a {cuenta.code} - {cuenta.name} ({tipo_cuenta})")
                    sugerencias.append(f"Los gastos normalmente aumentan con DÉBITO")

        return alertas, sugerencias

    @property
    def total_debit(self):
        """Total de débitos del asiento"""
        return sum(m.debit for m in self.movements.all())

    @property
    def total_credit(self):
        """Total de créditos del asiento"""
        return sum(m.credit for m in self.movements.all())

    @property
    def is_balanced(self):
        """Verifica si el asiento está balanceado"""
        return abs(self.total_debit - self.total_credit) < Decimal('0.01')


class Movement(TimestampMixin, models.Model):
    """Movimiento contable (línea del asiento - partida doble)"""
    transaction = models.ForeignKey(
        Transaction,
        on_delete=models.CASCADE,
        related_name='movements',
        verbose_name="Transacción"
    )
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        verbose_name="Cuenta"
    )
    third_party = models.ForeignKey(
        ThirdParty,
        on_delete=models.CASCADE,
        verbose_name="Tercero"
    )
    debit = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0'),
        verbose_name="Débito"
    )
    credit = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0'),
        verbose_name="Crédito"
    )
    description = models.TextField(blank=True, null=True, verbose_name="Descripción")

    class Meta:
        verbose_name = "Movimiento"
        verbose_name_plural = "Movimientos"
        ordering = ['-debit', 'account__code']
        indexes = [
            models.Index(fields=['transaction', 'account']),
            models.Index(fields=['account', 'third_party']),
        ]

    def __str__(self):
        return f"Mov: {self.account.code} - D:${self.debit} C:${self.credit}"

    def clean(self):
        """Validaciones del movimiento"""
        if self.debit < 0:
            raise ValidationError("El débito no puede ser negativo")
        if self.credit < 0:
            raise ValidationError("El crédito no puede ser negativo")
        if self.debit > 0 and self.credit > 0:
            raise ValidationError("Un movimiento no puede tener débito y crédito simultáneamente")
        if self.debit == 0 and self.credit == 0:
            raise ValidationError("El movimiento debe tener al menos un valor en débito o crédito")

    @property
    def amount(self):
        """Monto del movimiento (débito o crédito)"""
        return self.debit if self.debit > 0 else self.credit

    @property
    def is_debit(self):
        """Indica si es un movimiento débito"""
        return self.debit > 0


class RecurringTransaction(TimestampMixin, models.Model):
    """Plantilla para transacciones recurrentes"""
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='recurring_transactions',
        verbose_name="Empresa"
    )
    concept = models.CharField(max_length=255, verbose_name="Concepto")
    additional_description = models.TextField(blank=True, null=True, verbose_name="Descripción")
    day_of_month = models.IntegerField(verbose_name="Día del mes")
    is_active = models.BooleanField(default=True, db_index=True, verbose_name="Activo")
    last_generated = models.DateField(null=True, blank=True, verbose_name="Última generación")

    class Meta:
        verbose_name = "Transacción Recurrente"
        verbose_name_plural = "Transacciones Recurrentes"
        ordering = ['day_of_month', 'concept']

    def __str__(self):
        return f"Recurrente: {self.concept} (día {self.day_of_month})"


class RecurringMovementTemplate(models.Model):
    """Plantilla de movimiento para transacciones recurrentes"""
    recurring_transaction = models.ForeignKey(
        RecurringTransaction,
        on_delete=models.CASCADE,
        related_name='movement_templates',
        verbose_name="Transacción recurrente"
    )
    account = models.ForeignKey(Account, on_delete=models.CASCADE, verbose_name="Cuenta")
    third_party = models.ForeignKey(ThirdParty, on_delete=models.CASCADE, verbose_name="Tercero")
    debit = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0'), verbose_name="Débito")
    credit = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0'), verbose_name="Crédito")
    description = models.TextField(blank=True, null=True, verbose_name="Descripción")

    class Meta:
        verbose_name = "Movimiento Plantilla"
        verbose_name_plural = "Movimientos Plantilla"


class License(TimestampMixin, models.Model):
    """Licencia de usuario para control de acceso"""
    user = models.OneToOneField('auth.User', on_delete=models.CASCADE, verbose_name="Usuario")
    expiration_date = models.DateField(verbose_name="Fecha de expiración")
    is_active = models.BooleanField(default=True, db_index=True, verbose_name="Activo")
    license_type = models.CharField(
        max_length=20,
        choices=[
            ('TRIAL', 'Prueba'),
            ('BASIC', 'Básica'),
            ('PRO', 'Profesional'),
            ('ENTERPRISE', 'Empresarial'),
        ],
        default='TRIAL',
        verbose_name="Tipo de licencia"
    )
    max_companies = models.IntegerField(default=1, verbose_name="Máximo de empresas")

    class Meta:
        verbose_name = "Licencia"
        verbose_name_plural = "Licencias"

    def __str__(self):
        return f"Licencia de {self.user.username} ({self.license_type})"

    @property
    def is_valid(self):
        """Verifica si la licencia es válida"""
        from datetime import date
        return self.is_active and self.expiration_date >= date.today()

    @property
    def days_remaining(self):
        """Días restantes de la licencia"""
        from datetime import date
        if not self.is_active:
            return 0
        delta = self.expiration_date - date.today()
        return max(0, delta.days)


class AccountingRule(TimestampMixin, models.Model):
    """
    Reglas de clasificación automática por empresa.
    Aprende automáticamente cuando el usuario edita transacciones.
    """
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='accounting_rules',
        verbose_name="Empresa"
    )
    third_party_nit = models.CharField(max_length=20, db_index=True, verbose_name="NIT del tercero")
    third_party_name = models.CharField(max_length=200, blank=True, verbose_name="Nombre del tercero")
    account = models.ForeignKey(Account, on_delete=models.CASCADE, verbose_name="Cuenta")

    # Aprendizaje automático
    confidence_score = models.IntegerField(
        default=1,
        help_text="Cuántas veces se ha confirmado esta regla",
        verbose_name="Puntuación de confianza"
    )
    last_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Último monto"
    )
    average_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Monto promedio"
    )
    min_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Monto mínimo"
    )
    max_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Monto máximo"
    )

    # Metadatos
    created_by_user = models.BooleanField(
        default=False,
        help_text="True si la creó el usuario, False si la aprendió el sistema",
        verbose_name="Creado por usuario"
    )

    class Meta:
        unique_together = ['company', 'third_party_nit']
        ordering = ['-confidence_score', '-updated_at']
        verbose_name = "Regla de Clasificación"
        verbose_name_plural = "Reglas de Clasificación"
        indexes = [
            models.Index(fields=['company', 'third_party_nit']),
            models.Index(fields=['company', '-confidence_score']),
        ]

    def __str__(self):
        return f"{self.company.name} - NIT {self.third_party_nit} → {self.account.code}"

    def update_statistics(self, new_amount):
        """Actualiza estadísticas de montos para detección de anomalías"""
        new_amount = Decimal(str(new_amount))

        if self.average_amount is None:
            self.average_amount = new_amount
            self.min_amount = new_amount
            self.max_amount = new_amount
        else:
            # Media móvil exponencial (EMA)
            alpha = Decimal('0.3')
            self.average_amount = (self.average_amount * (1 - alpha)) + (new_amount * alpha)

            # Actualizar min/max
            if self.min_amount is None or new_amount < self.min_amount:
                self.min_amount = new_amount
            if self.max_amount is None or new_amount > self.max_amount:
                self.max_amount = new_amount

        self.last_amount = new_amount
        self.confidence_score += 1
        self.save()

    def is_amount_anomaly(self, amount, threshold=0.5):
        """
        Detecta si un monto es anómalo (muy diferente al promedio).
        threshold: 0.5 = 50% de diferencia
        """
        if not self.average_amount or self.average_amount == 0:
            return False

        amount = Decimal(str(amount))
        difference = abs(amount - self.average_amount) / self.average_amount
        return difference > Decimal(str(threshold))

    def get_expected_range(self, tolerance=0.3):
        """Devuelve el rango esperado de montos"""
        if not self.average_amount:
            return None, None

        tolerance = Decimal(str(tolerance))
        min_expected = self.average_amount * (1 - tolerance)
        max_expected = self.average_amount * (1 + tolerance)
        return min_expected, max_expected


class AuditLog(models.Model):
    """Log de auditoría para cambios importantes"""
    ACTION_CHOICES = [
        ('CREATE', 'Creación'),
        ('UPDATE', 'Actualización'),
        ('DELETE', 'Eliminación'),
        ('CANCEL', 'Anulación'),
        ('RESTORE', 'Restauración'),
    ]

    user = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Usuario"
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, verbose_name="Acción")
    model_name = models.CharField(max_length=100, verbose_name="Modelo")
    object_id = models.IntegerField(verbose_name="ID del objeto")
    object_repr = models.CharField(max_length=255, verbose_name="Representación")
    changes = models.JSONField(null=True, blank=True, verbose_name="Cambios")
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP")
    user_agent = models.TextField(null=True, blank=True, verbose_name="User Agent")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Fecha/Hora")

    class Meta:
        verbose_name = "Log de Auditoría"
        verbose_name_plural = "Logs de Auditoría"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['model_name', 'object_id']),
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['-timestamp']),
        ]

    def __str__(self):
        return f"{self.action} - {self.model_name} #{self.object_id} por {self.user}"
