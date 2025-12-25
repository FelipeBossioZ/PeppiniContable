# transactions/serializers.py
"""
Serializers para el sistema contable PeppiniContable.
Optimizados para evitar N+1 queries.
"""

from rest_framework import serializers
from django.db.models import Sum, Count
from django.core.exceptions import ValidationError as DjangoValidationError
from decimal import Decimal

from .models import (
    Transaction, Movement, Company, Account, ThirdParty,
    RecurringTransaction, RecurringMovementTemplate, License, AccountingRule, AuditLog
)


# ==============================================================================
# SERIALIZERS BASE
# ==============================================================================

class BaseModelSerializer(serializers.ModelSerializer):
    """Serializer base con campos de auditoría"""
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


# ==============================================================================
# COMPANY SERIALIZER
# ==============================================================================

class CompanySerializer(BaseModelSerializer):
    """Serializer para empresas con estadísticas pre-calculadas"""
    transaction_count = serializers.IntegerField(read_only=True)
    total_debits = serializers.DecimalField(max_digits=18, decimal_places=2, read_only=True)
    total_credits = serializers.DecimalField(max_digits=18, decimal_places=2, read_only=True)
    balance = serializers.SerializerMethodField()
    display_name = serializers.SerializerMethodField()

    class Meta:
        model = Company
        fields = [
            'id', 'name', 'nit', 'transaction_prefix', 'address', 'phone', 'email',
            'is_active', 'transaction_count', 'total_debits', 'total_credits',
            'balance', 'display_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'transaction_count', 'total_debits', 'total_credits', 'balance']

    def get_balance(self, obj):
        """Calcula balance desde campos pre-anotados"""
        debits = getattr(obj, 'total_debits', None) or Decimal('0')
        credits = getattr(obj, 'total_credits', None) or Decimal('0')
        return float(debits - credits)

    def get_display_name(self, obj):
        return f"{obj.name} ({obj.nit})"

    @staticmethod
    def setup_eager_loading(queryset):
        """Configura eager loading para evitar N+1"""
        return queryset.annotate(
            transaction_count=Count('transactions', distinct=True),
            total_debits=Sum('transactions__movements__debit'),
            total_credits=Sum('transactions__movements__credit')
        )


class CompanyMinimalSerializer(serializers.ModelSerializer):
    """Serializer mínimo para listas desplegables"""
    class Meta:
        model = Company
        fields = ['id', 'name', 'nit']


# ==============================================================================
# ACCOUNT SERIALIZER
# ==============================================================================

class AccountSerializer(BaseModelSerializer):
    """Serializer para cuentas contables"""
    full_name = serializers.CharField(source='__str__', read_only=True)
    parent_name = serializers.CharField(source='parent.name', read_only=True)
    parent_code = serializers.CharField(source='parent.code', read_only=True)
    movement_count = serializers.IntegerField(read_only=True)
    total_debit = serializers.DecimalField(max_digits=18, decimal_places=2, read_only=True)
    total_credit = serializers.DecimalField(max_digits=18, decimal_places=2, read_only=True)
    balance = serializers.SerializerMethodField()

    class Meta:
        model = Account
        fields = [
            'id', 'code', 'name', 'full_name', 'tipo', 'naturaleza',
            'parent', 'parent_name', 'parent_code', 'level', 'is_group',
            'is_active', 'description', 'movement_count', 'total_debit',
            'total_credit', 'balance', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'full_name', 'movement_count', 'balance']

    def get_balance(self, obj):
        """Calcula balance según naturaleza de la cuenta"""
        debit = getattr(obj, 'total_debit', None) or Decimal('0')
        credit = getattr(obj, 'total_credit', None) or Decimal('0')

        if obj.naturaleza == 'DEBITO':
            return float(debit - credit)
        return float(credit - debit)

    @staticmethod
    def setup_eager_loading(queryset):
        """Configura eager loading para evitar N+1"""
        return queryset.select_related('parent').annotate(
            movement_count=Count('movement', distinct=True),
            total_debit=Sum('movement__debit'),
            total_credit=Sum('movement__credit')
        )


class AccountMinimalSerializer(serializers.ModelSerializer):
    """Serializer mínimo para búsquedas"""
    class Meta:
        model = Account
        fields = ['id', 'code', 'name', 'tipo']


# ==============================================================================
# THIRD PARTY SERIALIZER
# ==============================================================================

class ThirdPartySerializer(BaseModelSerializer):
    """Serializer para terceros"""
    display_name = serializers.CharField(read_only=True)
    movement_count = serializers.IntegerField(read_only=True)
    total_debits = serializers.DecimalField(max_digits=18, decimal_places=2, read_only=True)
    total_credits = serializers.DecimalField(max_digits=18, decimal_places=2, read_only=True)
    balance = serializers.SerializerMethodField()

    class Meta:
        model = ThirdParty
        fields = [
            'id', 'name', 'nit', 'alias', 'display_name', 'email', 'phone',
            'address', 'contact_name', 'notes', 'is_deleted',
            'movement_count', 'total_debits', 'total_credits', 'balance',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'display_name', 'movement_count', 'balance', 'is_deleted']

    def get_balance(self, obj):
        debits = getattr(obj, 'total_debits', None) or Decimal('0')
        credits = getattr(obj, 'total_credits', None) or Decimal('0')
        return float(debits - credits)

    @staticmethod
    def setup_eager_loading(queryset):
        """Configura eager loading para evitar N+1"""
        return queryset.annotate(
            movement_count=Count('movement', distinct=True),
            total_debits=Sum('movement__debit'),
            total_credits=Sum('movement__credit')
        )


class ThirdPartyMinimalSerializer(serializers.ModelSerializer):
    """Serializer mínimo para búsquedas"""
    class Meta:
        model = ThirdParty
        fields = ['id', 'name', 'nit', 'alias']


# ==============================================================================
# MOVEMENT SERIALIZER
# ==============================================================================

class MovementSerializer(serializers.ModelSerializer):
    """Serializer para movimientos contables"""
    account_name = serializers.CharField(source='account.name', read_only=True)
    account_code = serializers.CharField(source='account.code', read_only=True)
    account_tipo = serializers.CharField(source='account.tipo', read_only=True)
    third_party_name = serializers.CharField(source='third_party.name', read_only=True)
    third_party_nit = serializers.CharField(source='third_party.nit', read_only=True)
    transaction_number = serializers.CharField(source='transaction.number', read_only=True)
    transaction_date = serializers.DateField(source='transaction.date', read_only=True)

    class Meta:
        model = Movement
        fields = [
            'id', 'transaction', 'transaction_number', 'transaction_date',
            'account', 'account_code', 'account_name', 'account_tipo',
            'third_party', 'third_party_name', 'third_party_nit',
            'debit', 'credit', 'description'
        ]
        read_only_fields = ['id', 'transaction', 'transaction_number', 'transaction_date']

    def validate(self, data):
        """Validar que el movimiento tenga débito O crédito, no ambos"""
        debit = data.get('debit', Decimal('0'))
        credit = data.get('credit', Decimal('0'))

        if debit < 0 or credit < 0:
            raise serializers.ValidationError("Los valores no pueden ser negativos")

        if debit > 0 and credit > 0:
            raise serializers.ValidationError(
                "Un movimiento no puede tener débito y crédito simultáneamente"
            )

        if debit == 0 and credit == 0:
            raise serializers.ValidationError(
                "El movimiento debe tener al menos un valor en débito o crédito"
            )

        return data


class MovementCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear movimientos (sin transaction - se asigna después)"""
    class Meta:
        model = Movement
        fields = ['account', 'third_party', 'debit', 'credit', 'description']


# ==============================================================================
# TRANSACTION SERIALIZER
# ==============================================================================

class TransactionSerializer(serializers.ModelSerializer):
    """Serializer para transacciones con movimientos anidados (solo lectura)"""
    company_name = serializers.CharField(source='company.name', read_only=True)
    company_nit = serializers.CharField(source='company.nit', read_only=True)
    movements = MovementSerializer(many=True, read_only=True)
    total_debit = serializers.SerializerMethodField()
    total_credit = serializers.SerializerMethodField()
    is_balanced = serializers.SerializerMethodField()
    movement_count = serializers.SerializerMethodField()
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = Transaction
        fields = [
            'id', 'number', 'company', 'company_name', 'company_nit',
            'date', 'concept', 'additional_description',
            'movements', 'movement_count', 'total_debit', 'total_credit',
            'is_balanced', 'is_deleted', 'deleted_at',
            'created_by', 'created_by_username', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'number', 'company_name', 'movements', 'total_debit',
            'total_credit', 'is_balanced', 'movement_count', 'is_deleted'
        ]

    def get_total_debit(self, obj):
        # Usar prefetch si está disponible
        if hasattr(obj, '_prefetched_objects_cache') and 'movements' in obj._prefetched_objects_cache:
            return float(sum(m.debit for m in obj.movements.all()))
        return float(obj.movements.aggregate(total=Sum('debit'))['total'] or 0)

    def get_total_credit(self, obj):
        if hasattr(obj, '_prefetched_objects_cache') and 'movements' in obj._prefetched_objects_cache:
            return float(sum(m.credit for m in obj.movements.all()))
        return float(obj.movements.aggregate(total=Sum('credit'))['total'] or 0)

    def get_is_balanced(self, obj):
        return abs(self.get_total_debit(obj) - self.get_total_credit(obj)) < 0.01

    def get_movement_count(self, obj):
        if hasattr(obj, '_prefetched_objects_cache') and 'movements' in obj._prefetched_objects_cache:
            return len(obj.movements.all())
        return obj.movements.count()

    @staticmethod
    def setup_eager_loading(queryset):
        """Configura eager loading para evitar N+1"""
        return queryset.select_related(
            'company', 'created_by'
        ).prefetch_related(
            'movements__account',
            'movements__third_party'
        )


class TransactionCreateSerializer(serializers.ModelSerializer):
    """Serializer para CREAR transacciones con movimientos anidados"""
    movements = MovementCreateSerializer(many=True)

    class Meta:
        model = Transaction
        fields = ['id', 'company', 'date', 'concept', 'additional_description', 'movements']
        read_only_fields = ['id']

    def validate_movements(self, movements):
        """Validar que haya al menos 2 movimientos y que el asiento cuadre"""
        if len(movements) < 2:
            raise serializers.ValidationError(
                "Una transacción debe tener al menos 2 movimientos (partida doble)"
            )

        total_debit = sum(Decimal(str(m.get('debit', 0))) for m in movements)
        total_credit = sum(Decimal(str(m.get('credit', 0))) for m in movements)

        if abs(total_debit - total_credit) > Decimal('0.01'):
            raise serializers.ValidationError(
                f"El asiento no cuadra: Débito ${total_debit} ≠ Crédito ${total_credit}"
            )

        return movements

    def create(self, validated_data):
        """Crear transacción con sus movimientos"""
        movements_data = validated_data.pop('movements')
        transaction = Transaction.objects.create(**validated_data)

        for movement_data in movements_data:
            Movement.objects.create(transaction=transaction, **movement_data)

        return transaction

    def update(self, instance, validated_data):
        """Actualizar transacción y sus movimientos"""
        movements_data = validated_data.pop('movements', None)

        # Actualizar campos de la transacción
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Si vienen movimientos, reemplazar todos
        if movements_data is not None:
            instance.movements.all().delete()
            for movement_data in movements_data:
                Movement.objects.create(transaction=instance, **movement_data)

        return instance


class TransactionMinimalSerializer(serializers.ModelSerializer):
    """Serializer mínimo para listas"""
    class Meta:
        model = Transaction
        fields = ['id', 'number', 'date', 'concept']


# ==============================================================================
# RECURRING TRANSACTION SERIALIZERS
# ==============================================================================

class RecurringMovementTemplateSerializer(serializers.ModelSerializer):
    """Serializer para plantillas de movimientos recurrentes"""
    account_name = serializers.CharField(source='account.name', read_only=True)
    third_party_name = serializers.CharField(source='third_party.name', read_only=True)

    class Meta:
        model = RecurringMovementTemplate
        fields = [
            'id', 'account', 'account_name', 'third_party', 'third_party_name',
            'debit', 'credit', 'description'
        ]


class RecurringTransactionSerializer(BaseModelSerializer):
    """Serializer para transacciones recurrentes"""
    company_name = serializers.CharField(source='company.name', read_only=True)
    movement_templates = RecurringMovementTemplateSerializer(many=True, read_only=True)
    total_amount = serializers.SerializerMethodField()

    class Meta:
        model = RecurringTransaction
        fields = [
            'id', 'company', 'company_name', 'concept', 'additional_description',
            'day_of_month', 'is_active', 'last_generated', 'movement_templates',
            'total_amount', 'created_at', 'updated_at'
        ]

    def get_total_amount(self, obj):
        """Total de la transacción recurrente"""
        templates = obj.movement_templates.all()
        return float(sum(t.debit for t in templates))


# ==============================================================================
# LICENSE SERIALIZER
# ==============================================================================

class LicenseSerializer(BaseModelSerializer):
    """Serializer para licencias"""
    username = serializers.CharField(source='user.username', read_only=True)
    is_valid = serializers.BooleanField(read_only=True)
    days_remaining = serializers.IntegerField(read_only=True)

    class Meta:
        model = License
        fields = [
            'id', 'user', 'username', 'expiration_date', 'is_active',
            'license_type', 'max_companies', 'is_valid', 'days_remaining',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'is_valid', 'days_remaining']


# ==============================================================================
# ACCOUNTING RULE SERIALIZER
# ==============================================================================

class AccountingRuleSerializer(BaseModelSerializer):
    """Serializer para reglas de clasificación automática"""
    company_name = serializers.CharField(source='company.name', read_only=True)
    account_code = serializers.CharField(source='account.code', read_only=True)
    account_name = serializers.CharField(source='account.name', read_only=True)
    expected_range = serializers.SerializerMethodField()

    class Meta:
        model = AccountingRule
        fields = [
            'id', 'company', 'company_name', 'third_party_nit', 'third_party_name',
            'account', 'account_code', 'account_name', 'confidence_score',
            'last_amount', 'average_amount', 'min_amount', 'max_amount',
            'expected_range', 'created_by_user', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'confidence_score', 'expected_range']

    def get_expected_range(self, obj):
        min_val, max_val = obj.get_expected_range()
        if min_val is None:
            return None
        return {
            'min': float(min_val),
            'max': float(max_val)
        }

    @staticmethod
    def setup_eager_loading(queryset):
        return queryset.select_related('company', 'account')


# ==============================================================================
# AUDIT LOG SERIALIZER
# ==============================================================================

class AuditLogSerializer(serializers.ModelSerializer):
    """Serializer para logs de auditoría"""
    username = serializers.CharField(source='user.username', read_only=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)

    class Meta:
        model = AuditLog
        fields = [
            'id', 'user', 'username', 'action', 'action_display',
            'model_name', 'object_id', 'object_repr', 'changes',
            'ip_address', 'timestamp'
        ]
        read_only_fields = '__all__'
