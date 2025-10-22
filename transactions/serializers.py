from rest_framework import serializers
from .models import Transaction, Company, Account, ThirdParty

class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = '__all__'

class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = '__all__'

class ThirdPartySerializer(serializers.ModelSerializer):
    class Meta:
        model = ThirdParty
        fields = '__all__'

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = '__all__'
