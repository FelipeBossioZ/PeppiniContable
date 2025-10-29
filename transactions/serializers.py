# transactions/serializers.py
from rest_framework import serializers
from .models import Transaction, Company, Account, ThirdParty, RecurringTransaction, License
from decimal import Decimal
from datetime import date
from django.core.exceptions import ValidationError
import re
from django.db.models import Sum  


class CompanySerializer(serializers.ModelSerializer):
    """
    Serializador para el modelo Company con validaciones mejoradas
    """
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
        """Obtener el número total de transacciones de la empresa"""
        return obj.transaction_set.count()
    
    def get_total_debits(self, obj):
        """Calcular el total de débitos"""
        total = obj.transaction_set.aggregate(
            total=Sum('debit')
        )['total']
        return float(total or 0)
    
    def get_total_credits(self, obj):
        """Calcular el total de créditos"""
        total = obj.transaction_set.aggregate(
            total=Sum('credit')
        )['total']
        return float(total or 0)
    
    def get_balance(self, obj):
        """Calcular el balance general"""
        debits = self.get_total_debits(obj)
        credits = self.get_total_credits(obj)
        return debits - credits
    
    def validate_nit(self, value):
        """Validar formato NIT colombiano"""
        if not value:
            raise serializers.ValidationError("El NIT es obligatorio")
        
        # Limpiar el NIT de caracteres no numéricos excepto el guión
        cleaned_nit = re.sub(r'[^0-9\-]', '', value)
        
        # Validar formato básico (ej: 900123456-1)
        if not re.match(r'^\d{8,10}(-\d)?$', cleaned_nit):
            raise serializers.ValidationError(
                "Formato de NIT inválido. Use el formato: 900123456-1"
            )
        
        return cleaned_nit.upper()
    
    def validate_name(self, value):
        """Validar nombre de empresa"""
        if not value or len(value.strip()) < 3:
            raise serializers.ValidationError(
                "El nombre de la empresa debe tener al menos 3 caracteres"
            )
        return value.strip().upper()


class AccountSerializer(serializers.ModelSerializer):
    """
    Serializador para el modelo Account con información adicional
    """
    full_name = serializers.SerializerMethodField()
    transaction_count = serializers.SerializerMethodField()
    total_movement = serializers.SerializerMethodField()
    
    class Meta:
        model = Account
        fields = [
            'id', 'code', 'name', 'full_name',
            'transaction_count', 'total_movement'
        ]
        read_only_fields = ['id', 'full_name', 'transaction_count', 'total_movement']
    
    def get_full_name(self, obj):
        """Nombre completo de la cuenta con código"""
        return f"{obj.code} - {obj.name}"
    
    def get_transaction_count(self, obj):
        """Número de transacciones en esta cuenta"""
        return obj.transaction_set.count()
    
    def get_total_movement(self, obj):
        """Total de movimiento en la cuenta (débitos + créditos)"""
        totals = obj.transaction_set.aggregate(
            total_debit=Sum('debit'),
            total_credit=Sum('credit')
        )
        debit = totals['total_debit'] or 0
        credit = totals['total_credit'] or 0
        return float(debit + credit)
    
    def validate_code(self, value):
        """Validar código de cuenta PUC"""
        if not value:
            raise serializers.ValidationError("El código de cuenta es obligatorio")
        
        # Limpiar espacios y convertir a mayúsculas
        cleaned_code = value.strip().upper()
        
        # Validar que sea numérico o alfanumérico según tu sistema
        if not re.match(r'^[0-9A-Z\-\.]+$', cleaned_code):
            raise serializers.ValidationError(
                "El código de cuenta solo puede contener números, letras, puntos y guiones"
            )
        
        if len(cleaned_code) < 2:
            raise serializers.ValidationError(
                "El código de cuenta debe tener al menos 2 caracteres"
            )
        
        return cleaned_code
    
    def validate_name(self, value):
        """Validar nombre de cuenta"""
        if not value or len(value.strip()) < 3:
            raise serializers.ValidationError(
                "El nombre de la cuenta debe tener al menos 3 caracteres"
            )
        return value.strip().title()


class ThirdPartySerializer(serializers.ModelSerializer):
    """
    Serializador para terceros (clientes/proveedores) con validaciones
    """
    transaction_count = serializers.SerializerMethodField()
    total_debits = serializers.SerializerMethodField()
    total_credits = serializers.SerializerMethodField()
    balance = serializers.SerializerMethodField()
    
    class Meta:
        model = ThirdParty
        fields = [
            'id', 'name', 'nit', 'transaction_count',
            'total_debits', 'total_credits', 'balance'
        ]
        read_only_fields = ['id', 'transaction_count', 'total_debits', 'total_credits', 'balance']
    
    def get_transaction_count(self, obj):
        """Número de transacciones con este tercero"""
        return obj.transaction_set.count()
    
    def get_total_debits(self, obj):
        """Total de débitos del tercero"""
        total = obj.transaction_set.aggregate(
            total=Sum('debit')
        )['total']
        return float(total or 0)
    
    def get_total_credits(self, obj):
        """Total de créditos del tercero"""
        total = obj.transaction_set.aggregate(
            total=Sum('credit')
        )['total']
        return float(total or 0)
    
    def get_balance(self, obj):
        """Balance del tercero (débitos - créditos)"""
        return self.get_total_debits(obj) - self.get_total_credits(obj)
    
    def validate_nit(self, value):
        """Validar NIT/Cédula del tercero"""
        if not value:
            raise serializers.ValidationError("El NIT/Cédula es obligatorio")
        
        # Limpiar caracteres no válidos
        cleaned_nit = re.sub(r'[^0-9\-]', '', value)
        
        # Validar formato (cédula o NIT)
        if not re.match(r'^\d{6,10}(-\d)?$', cleaned_nit):
            raise serializers.ValidationError(
                "Formato inválido. Use cédula (1234567890) o NIT (900123456-1)"
            )
        
        return cleaned_nit
    
    def validate_name(self, value):
        """Validar nombre del tercero"""
        if not value or len(value.strip()) < 3:
            raise serializers.ValidationError(
                "El nombre debe tener al menos 3 caracteres"
            )
        return value.strip().title()


class TransactionSerializer(serializers.ModelSerializer):
    """
    Serializador principal para transacciones con validaciones neurológicas
    """
    # Campos de solo lectura con información relacionada
    company_name = serializers.CharField(source='company.name', read_only=True)
    company_nit = serializers.CharField(source='company.nit', read_only=True)
    account_name = serializers.CharField(source='account.name', read_only=True)
    account_code = serializers.CharField(source='account.code', read_only=True)
    account_full = serializers.SerializerMethodField()
    third_party_name = serializers.CharField(source='third_party.name', read_only=True)
    third_party_nit = serializers.CharField(source='third_party.nit', read_only=True)
    
    # Campos calculados
    balance = serializers.SerializerMethodField()
    transaction_type = serializers.SerializerMethodField()
    formatted_date = serializers.SerializerMethodField()
    
    class Meta:
        model = Transaction
        fields = [
            'id', 
            'company', 'company_name', 'company_nit',
            'date', 'formatted_date',
            'account', 'account_name', 'account_code', 'account_full',
            'third_party', 'third_party_name', 'third_party_nit',
            'concept', 'additional_description',
            'debit', 'credit', 'balance', 'transaction_type'
        ]
        read_only_fields = [
            'id', 'company_name', 'company_nit', 'account_name', 
            'account_code', 'account_full', 'third_party_name', 
            'third_party_nit', 'balance', 'transaction_type', 'formatted_date'
        ]
    
    def get_account_full(self, obj):
        """Nombre completo de la cuenta"""
        return f"{obj.account.code} - {obj.account.name}"
    
    def get_balance(self, obj):
        """Calcular balance de la transacción"""
        return float(obj.debit - obj.credit)
    
    def get_transaction_type(self, obj):
        """Determinar tipo de transacción"""
        if obj.debit > 0:
            return "DÉBITO"
        elif obj.credit > 0:
            return "CRÉDITO"
        return "SIN MOVIMIENTO"
    
    def get_formatted_date(self, obj):
        """Fecha formateada para mejor legibilidad"""
        return obj.date.strftime('%d/%m/%Y')
    
    def validate_date(self, value):
        """
        Validar fecha de transacción
        Aplicando principios de neurología cognitiva para prevención de errores
        """
        if not value:
            raise serializers.ValidationError("La fecha es obligatoria")
        
        # No permitir fechas futuras (prevención de errores cognitivos)
        if value > date.today():
            raise serializers.ValidationError(
                "No se permiten fechas futuras. Verifique la fecha ingresada."
            )
        
        # Alertar si la fecha es muy antigua (posible error de digitación)
        days_ago = (date.today() - value).days
        if days_ago > 365:
            # No es un error, pero se podría agregar una advertencia en el frontend
            pass
        
        return value
    
    def validate_debit(self, value):
        """Validar monto de débito"""
        if value < 0:
            raise serializers.ValidationError(
                "El débito no puede ser negativo"
            )
        
        # Validar precisión decimal (2 decimales máximo)
        if value and len(str(value).split('.')[-1]) > 2:
            raise serializers.ValidationError(
                "Máximo 2 decimales permitidos"
            )
        
        return value
    
    def validate_credit(self, value):
        """Validar monto de crédito"""
        if value < 0:
            raise serializers.ValidationError(
                "El crédito no puede ser negativo"
            )
        
        # Validar precisión decimal
        if value and len(str(value).split('.')[-1]) > 2:
            raise serializers.ValidationError(
                "Máximo 2 decimales permitidos"
            )
        
        return value
    
    def validate_concept(self, value):
        """Validar concepto de la transacción"""
        if not value or len(value.strip()) < 3:
            raise serializers.ValidationError(
                "El concepto debe tener al menos 3 caracteres"
            )
        
        # Limpiar y formatear
        cleaned = value.strip()
        
        # Detectar posibles errores de digitación (caps lock)
        if cleaned.isupper() and len(cleaned) > 10:
            # Convertir a formato título si parece ser un error de CAPS LOCK
            cleaned = cleaned.title()
        
        return cleaned
    
    def validate(self, data):
        """
        Validaciones a nivel de objeto completo
        Implementando verificaciones cruzadas para integridad de datos
        """
        debit = data.get('debit', 0) or 0
        credit = data.get('credit', 0) or 0
        
        # Regla de negocio: Una transacción debe tener débito O crédito, no ambos
        if debit == 0 and credit == 0:
            raise serializers.ValidationError({
                'debit': "Debe especificar un valor para débito o crédito",
                'credit': "Debe especificar un valor para débito o crédito"
            })
        
        if debit > 0 and credit > 0:
            raise serializers.ValidationError({
                'debit': "Una transacción no puede tener débito Y crédito simultáneamente",
                'credit': "Una transacción no puede tener débito Y crédito simultáneamente"
            })
        
        # Validar montos excesivos (prevención de errores de digitación)
        MAX_AMOUNT = Decimal('999999999.99')
        if debit > MAX_AMOUNT or credit > MAX_AMOUNT:
            raise serializers.ValidationError(
                "El monto excede el límite máximo permitido"
            )
        
        # Validar que el concepto no sea repetitivo
        concept = data.get('concept', '')
        if concept:
            # Detectar conceptos genéricos que requieren más detalle
            generic_concepts = ['pago', 'cobro', 'transacción', 'movimiento', 'ajuste']
            if concept.lower().strip() in generic_concepts and not data.get('additional_description'):
                raise serializers.ValidationError({
                    'additional_description': f"El concepto '{concept}' requiere una descripción adicional"
                })
        
        return data
    
    def create(self, validated_data):
        """
        Crear transacción con logging para auditoría
        """
        transaction = super().create(validated_data)
        
        # Log para auditoría neurológica (tracking de patrones de uso)
        # Esto ayuda a identificar patrones de error comunes
        import logging
        logger = logging.getLogger('transactions.audit')
        logger.info(f"Transacción creada: {transaction.id} - {transaction.concept} - "
                   f"D: {transaction.debit} C: {transaction.credit}")
        
        return transaction


class RecurringTransactionSerializer(serializers.ModelSerializer):
    """
    Serializador para transacciones recurrentes
    """
    company_name = serializers.CharField(source='company.name', read_only=True)
    account_name = serializers.CharField(source='account.name', read_only=True)
    account_code = serializers.CharField(source='account.code', read_only=True)
    third_party_name = serializers.CharField(source='third_party.name', read_only=True)
    next_execution = serializers.SerializerMethodField()
    is_active_today = serializers.SerializerMethodField()
    
    class Meta:
        model = RecurringTransaction
        fields = [
            'id', 
            'company', 'company_name',
            'account', 'account_name', 'account_code',
            'third_party', 'third_party_name',
            'concept', 'additional_description',
            'debit', 'credit',
            'day_of_month', 'next_execution', 'is_active_today'
        ]
        read_only_fields = ['id', 'next_execution', 'is_active_today']
    
    def get_next_execution(self, obj):
        """Calcular próxima fecha de ejecución"""
        today = date.today()
        
        if obj.day_of_month >= today.day:
            # Este mes
            next_date = date(today.year, today.month, obj.day_of_month)
        else:
            # Próximo mes
            if today.month == 12:
                next_date = date(today.year + 1, 1, obj.day_of_month)
            else:
                # Manejar meses con menos días
                from calendar import monthrange
                next_month = today.month + 1
                max_day = monthrange(today.year, next_month)[1]
                day = min(obj.day_of_month, max_day)
                next_date = date(today.year, next_month, day)
        
        return next_date.strftime('%Y-%m-%d')
    
    def get_is_active_today(self, obj):
        """Verificar si debe ejecutarse hoy"""
        return obj.day_of_month == date.today().day
    
    def validate_day_of_month(self, value):
        """Validar día del mes para ejecución"""
        if not (1 <= value <= 31):
            raise serializers.ValidationError(
                "El día debe estar entre 1 y 31"
            )
        
        # Advertencia para días problemáticos
        if value > 28:
            # Solo advertencia, no error
            # Febrero y meses de 30 días ajustarán automáticamente
            pass
        
        return value
    
    def validate(self, data):
        """Validaciones cruzadas para transacciones recurrentes"""
        # Aplicar las mismas validaciones que TransactionSerializer
        debit = data.get('debit', 0) or 0
        credit = data.get('credit', 0) or 0
        
        if debit == 0 and credit == 0:
            raise serializers.ValidationError(
                "Debe especificar un valor para débito o crédito"
            )
        
        if debit > 0 and credit > 0:
            raise serializers.ValidationError(
                "Una transacción no puede tener débito y crédito simultáneamente"
            )
        
        return data


class LicenseSerializer(serializers.ModelSerializer):
    """
    Serializador para el sistema de licencias
    """
    user_name = serializers.CharField(source='user.username', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    days_remaining = serializers.SerializerMethodField()
    is_expired = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    
    class Meta:
        model = License
        fields = [
            'id', 'user', 'user_name', 'user_email',
            'expiration_date', 'is_active',
            'days_remaining', 'is_expired', 'status'
        ]
        read_only_fields = ['id', 'days_remaining', 'is_expired', 'status']
    
    def get_days_remaining(self, obj):
        """Calcular días restantes de licencia"""
        if not obj.is_active:
            return 0
        
        delta = obj.expiration_date - date.today()
        return max(0, delta.days)
    
    def get_is_expired(self, obj):
        """Verificar si la licencia está expirada"""
        return obj.expiration_date < date.today()
    
    def get_status(self, obj):
        """Estado descriptivo de la licencia"""
        if not obj.is_active:
            return "INACTIVA"
        
        days = self.get_days_remaining(obj)
        if days == 0:
            return "EXPIRADA"
        elif days <= 7:
            return "POR EXPIRAR"
        elif days <= 30:
            return "PRÓXIMA A VENCER"
        else:
            return "ACTIVA"
    
    def validate_expiration_date(self, value):
        """Validar fecha de expiración"""
        if value < date.today():
            raise serializers.ValidationError(
                "La fecha de expiración no puede ser en el pasado"
            )
        return value


# Serializador para reportes y estadísticas
class TransactionReportSerializer(serializers.Serializer):
    """
    Serializador para generar reportes de transacciones
    """
    company = serializers.PrimaryKeyRelatedField(queryset=Company.objects.all())
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    account = serializers.PrimaryKeyRelatedField(
        queryset=Account.objects.all(), 
        required=False, 
        allow_null=True
    )
    third_party = serializers.PrimaryKeyRelatedField(
        queryset=ThirdParty.objects.all(), 
        required=False, 
        allow_null=True
    )
    
    def validate(self, data):
        """Validar rangos de fechas"""
        if data['start_date'] > data['end_date']:
            raise serializers.ValidationError(
                "La fecha inicial no puede ser mayor que la fecha final"
            )
        
        # Limitar rango a máximo 1 año
        delta = (data['end_date'] - data['start_date']).days
        if delta > 366:
            raise serializers.ValidationError(
                "El rango de fechas no puede exceder un año"
            )
        
        return data