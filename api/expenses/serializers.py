from rest_framework import serializers
from expenses.models import Expense, FixedExpense


class ExpenseSerializer(serializers.ModelSerializer):
    account_name = serializers.CharField(source='account.account_name', read_only=True)
    current_balance = serializers.DecimalField(
        source='account.current_balance',
        max_digits=15,
        decimal_places=2,
        read_only=True
    )

    class Meta:
        model = Expense
        fields = '__all__'


# Fixed Expense Serializers

class FixedExpenseSerializer(serializers.ModelSerializer):
    """Serializer para leitura de despesas fixas (templates)"""
    account_name = serializers.CharField(source='account.account_name', read_only=True)
    member_name = serializers.CharField(source='member.member_name', read_only=True, allow_null=True)
    total_generated = serializers.IntegerField(read_only=True, required=False)

    class Meta:
        model = FixedExpense
        fields = '__all__'


class FixedExpenseCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer para criação/atualização de despesas fixas"""

    class Meta:
        model = FixedExpense
        exclude = ['last_generated_month', 'uuid', 'created_at', 'updated_at', 'created_by', 'updated_by', 'is_deleted', 'deleted_at']

    def validate_due_day(self, value):
        if not 1 <= value <= 31:
            raise serializers.ValidationError("O dia deve estar entre 1 e 31")
        return value


# Bulk Operations Serializers

class FixedExpenseValueSerializer(serializers.Serializer):
    """Serializer para valores de despesa fixa no bulk generate"""
    fixed_expense_id = serializers.IntegerField()
    value = serializers.DecimalField(max_digits=10, decimal_places=2)


class BulkGenerateRequestSerializer(serializers.Serializer):
    """Request para geração em lote de despesas fixas"""
    month = serializers.CharField(max_length=7, help_text="Formato: YYYY-MM")
    expense_values = serializers.ListField(
        child=FixedExpenseValueSerializer(),
        allow_empty=False
    )

    def validate_month(self, value):
        """Valida formato do mês YYYY-MM"""
        import re
        if not re.match(r'^\d{4}-\d{2}$', value):
            raise serializers.ValidationError("Formato inválido. Use YYYY-MM")

        # Valida se o mês é válido (01-12)
        year, month = value.split('-')
        month_int = int(month)
        if not 1 <= month_int <= 12:
            raise serializers.ValidationError("Mês deve estar entre 01 e 12")

        return value


class BulkGenerateResponseSerializer(serializers.Serializer):
    """Response da geração em lote"""
    success = serializers.BooleanField()
    created_count = serializers.IntegerField()
    month = serializers.CharField()
    expenses = ExpenseSerializer(many=True)


class BulkMarkPaidSerializer(serializers.Serializer):
    """Request para marcar múltiplas despesas como pagas"""
    expense_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False
    )
