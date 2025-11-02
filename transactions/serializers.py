# transactions/serializers.py
from rest_framework import serializers
from .models import Transaction, Movement, Company, Account, ThirdParty, RecurringTransaction, License
from decimal import Decimal
from datetime import date
from django.core.exceptions import ValidationError
import re
from django.db.models import Sum

# MANTENEMOS LOS SERIALIZERS EXISTENTES PERO ACTUALIZAMOS:

class CompanySerializer(serializers.ModelSerializer):
    transaction_count = serializers.SerializerMethodField()
    total_debits = serializers.SerializerMethodField()
    total_credits = serializers.SerializerMethodField()
    balance = serializers.SerializerMethodField()
    
    class Meta:
        model = Company
        fields = [
            'id', 'name', 'nit', 'transaction_count',
            'total_debits', 'total_credits', 'balance'
        ]
        read_only_fields = ['id', 'transaction_count', 'total_debits', 'total_credits', 'balance']
    
    def get_transaction_count(self, obj):
        return obj.transaction_set.count()
    
    def get_total_debits(self, obj):
        # AHORA calculamos desde los Movement
        total = Movement.objects.filter(transaction__company=obj).aggregate(
            total=Sum('debit')
        )['total']
        return float(total or 0)
    
    def get_total_credits(self, obj):
        total = Movement.objects.filter(transaction__company=obj).aggregate(
            total=Sum('credit')
        )['total']
        return float(total or 0)
    
    def get_balance(self, obj):
        debits = self.get_total_debits(obj)
        credits = self.get_total_credits(obj)
        return debits - credits

class AccountSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    transaction_count = serializers.SerializerMethodField()
    total_movement = serializers.SerializerMethodField()
    parent_name = serializers.CharField(source='parent.name', read_only=True)
    
    class Meta:
        model = Account
        fields = [
            'id', 'code', 'name', 'full_name', 'parent', 'parent_name',
            'level', 'is_group', 'transaction_count', 'total_movement'
        ]
        read_only_fields = ['id', 'full_name', 'transaction_count', 'total_movement']
    
    def get_full_name(self, obj):
        return f"{obj.code} - {obj.name}"
    
    def get_transaction_count(self, obj):
        return obj.movement_set.count()
    
    def get_total_movement(self, obj):
        totals = obj.movement_set.aggregate(
            total_debit=Sum('debit'),
            total_credit=Sum('credit')
        )
        debit = totals['total_debit'] or 0
        credit = totals['total_credit'] or 0
        return float(debit + credit)

class ThirdPartySerializer(serializers.ModelSerializer):
    transaction_count = serializers.SerializerMethodField()
    total_debits = serializers.SerializerMethodField()
    total_credits = serializers.SerializerMethodField()
    balance = serializers.SerializerMethodField()
    
    class Meta:
        model = ThirdParty
        fields = [
            'id', 'name', 'nit', 'alias', 'transaction_count',
            'total_debits', 'total_credits', 'balance'
        ]
        read_only_fields = ['id', 'transaction_count', 'total_debits', 'total_credits', 'balance']
    
    def get_transaction_count(self, obj):
        return obj.movement_set.count()
    
    def get_total_debits(self, obj):
        total = obj.movement_set.aggregate(total=Sum('debit'))['total']
        return float(total or 0)
    
    def get_total_credits(self, obj):
        total = obj.movement_set.aggregate(total=Sum('credit'))['total']
        return float(total or 0)
    
    def get_balance(self, obj):
        return self.get_total_debits(obj) - self.get_total_credits(obj)

# 🔥 NUEVO: Serializer para Movement
class MovementSerializer(serializers.ModelSerializer):
    account_name = serializers.CharField(source='account.name', read_only=True)
    account_code = serializers.CharField(source='account.code', read_only=True)
    third_party_name = serializers.CharField(source='third_party.name', read_only=True)
    transaction_number = serializers.CharField(source='transaction.number', read_only=True)
    
    class Meta:
        model = Movement
        fields = [
            'id', 'transaction', 'transaction_number',  # ← 'transaction' debe ser read_only
            'account', 'account_code', 'account_name',
            'third_party', 'third_party_name',
            'debit', 'credit', 'description'
        ]
        read_only_fields = ['id', 'transaction', 'transaction_number']  # ← AGREGAR 'transaction' AQUÍ

# 🔥 NUEVO: Serializer para Transaction con Movements
class TransactionSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.name', read_only=True)
    movements = MovementSerializer(many=True, read_only=True)
    total_debit = serializers.SerializerMethodField()
    total_credit = serializers.SerializerMethodField()
    is_balanced = serializers.SerializerMethodField()
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'number', 'company', 'company_name', 'date',
            'concept', 'additional_description', 'movements',
            'total_debit', 'total_credit', 'is_balanced'
        ]
        read_only_fields = ['id', 'number', 'company_name', 'movements', 'total_debit', 'total_credit', 'is_balanced']
    
    def get_total_debit(self, obj):
        return sum(m.debit for m in obj.movements.all())
    
    def get_total_credit(self, obj):
        return sum(m.credit for m in obj.movements.all())
    
    def get_is_balanced(self, obj):
        return self.get_total_debit(obj) == self.get_total_credit(obj)
    
    def validate(self, data):
        # La validación débito=crédito ahora se hace en el modelo
        return data

# 🔥 NUEVO: Serializer para CREAR Transaction con Movements
class TransactionCreateSerializer(serializers.ModelSerializer):
    movements = MovementSerializer(many=True)
    
    class Meta:
        model = Transaction
        fields = ['id', 'company', 'date', 'concept', 'additional_description', 'movements']
        read_only_fields = ['id']  # ← AGREGAR ESTA LÍNEA
    
    def create(self, validated_data):
        movements_data = validated_data.pop('movements')
        transaction = Transaction.objects.create(**validated_data)
        
        for movement_data in movements_data:
            # NO incluir 'transaction' en movement_data porque ya está implícito
            Movement.objects.create(transaction=transaction, **movement_data)
        
        # Validar que la transacción esté balanceada
        transaction.clean()
        return transaction

# MANTENEMOS LOS OTROS SERIALIZERS (RecurringTransaction, License, etc.)
# pero actualizamos las referencias a Transaction por Movement donde sea necesario

class RecurringTransactionSerializer(serializers.ModelSerializer):
    # ... (código existente pero actualizando cálculos)
    pass

class LicenseSerializer(serializers.ModelSerializer):
    # ... (código existente)
    pass