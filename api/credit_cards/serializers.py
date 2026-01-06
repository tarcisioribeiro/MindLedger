from rest_framework import serializers
from credit_cards.models import CreditCard, CreditCardBill, CreditCardExpense


class CreditCardSerializer(serializers.ModelSerializer):
    security_code = serializers.CharField(
        max_length=4,
        min_length=3,
        write_only=True,
        help_text="CVV do cartão (3 ou 4 dígitos)"
    )
    card_number = serializers.CharField(
        max_length=19,
        write_only=True,
        required=False,
        allow_blank=True,
        help_text="Número do cartão (será criptografado)"
    )
    card_number_masked = serializers.SerializerMethodField(
        read_only=True,
        help_text="Número do cartão mascarado"
    )
    associated_account_name = serializers.CharField(
        source='associated_account.account_name',
        read_only=True,
        help_text="Nome da conta associada"
    )

    class Meta:
        model = CreditCard
        exclude = ['_security_code', '_card_number']

    def get_card_number_masked(self, obj):
        """
        Retorna o número do cartão mascarado usando a propriedade do model.
        """
        return obj.card_number_masked

    def validate_security_code(self, value):
        """
        Validação customizada para o CVV.
        """
        if not value.isdigit():
            raise serializers.ValidationError("CVV deve conter apenas dígitos")
        if len(value) not in [3, 4]:
            raise serializers.ValidationError("CVV deve ter 3 ou 4 dígitos")
        return value

    def validate_validation_date(self, value):
        """
        Validação customizada para data de validade.
        """
        from datetime import date
        if value <= date.today():
            raise serializers.ValidationError(
                "Data de validade deve ser posterior à data atual"
            )
        return value

    def create(self, validated_data):
        """
        Override do create para lidar com os campos criptografados.
        """
        security_code = validated_data.pop('security_code', None)
        card_number = validated_data.pop('card_number', None)

        # Criar a instância sem salvar
        instance = CreditCard(**validated_data)

        # Definir o security_code via property (que criptografa e define _security_code)
        if security_code:
            instance.security_code = security_code

        # Definir o card_number via property (que criptografa e define _card_number)
        if card_number:
            instance.card_number = card_number

        # Agora salvar a instância com campos criptografados já definidos
        instance.save()
        return instance

    def update(self, instance, validated_data):
        """
        Override do update para lidar com os campos criptografados.
        """
        security_code = validated_data.pop('security_code', None)
        card_number = validated_data.pop('card_number', None)

        # Atualizar os campos do validated_data
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Definir o security_code via property se fornecido
        if security_code:
            instance.security_code = security_code

        # Definir o card_number via property se fornecido
        if card_number:
            instance.card_number = card_number

        # Salvar a instância
        instance.save()
        return instance


class CreditCardBillsSerializer(serializers.ModelSerializer):
    credit_card_on_card_name = serializers.CharField(
        source='credit_card.on_card_name',
        read_only=True,
        help_text="Nome impresso no cartão"
    )
    credit_card_number_masked = serializers.SerializerMethodField(
        read_only=True,
        help_text="Últimos 4 dígitos do cartão"
    )
    credit_card_flag = serializers.CharField(
        source='credit_card.flag',
        read_only=True,
        help_text="Bandeira do cartão"
    )
    credit_card_associated_account_name = serializers.CharField(
        source='credit_card.associated_account.account_name',
        read_only=True,
        help_text="Nome da conta associada ao cartão"
    )

    class Meta:
        model = CreditCardBill
        fields = '__all__'

    def get_credit_card_number_masked(self, obj):
        """
        Retorna os últimos 4 dígitos do cartão mascarado.
        """
        if obj.credit_card and obj.credit_card.card_number_masked:
            masked = obj.credit_card.card_number_masked
            # Se já está mascarado, pega os últimos 4
            if len(masked) >= 4:
                return masked[-4:]
        return "****"


class CreditCardExpensesSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreditCardExpense
        fields = '__all__'
