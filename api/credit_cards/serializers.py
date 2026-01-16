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
            # Verifica se o cartão tem número válido (não é apenas asteriscos)
            if masked and masked != "****" and len(masked) >= 4:
                # Remove os asteriscos e pega apenas os últimos 4 dígitos numéricos
                digits_only = ''.join(c for c in masked if c.isdigit())
                if len(digits_only) >= 4:
                    return digits_only[-4:]
        return "****"

    def create(self, validated_data):
        """
        Override do create para inicializar valores padrão.
        Ao criar uma fatura:
        - total_amount = 0
        - minimum_payment = 0
        - paid_amount = 0
        - status = 'open'
        - closed = False
        - due_date = calculado automaticamente se não fornecido
        """
        from datetime import date
        import calendar

        validated_data['total_amount'] = 0
        validated_data['minimum_payment'] = 0
        validated_data['paid_amount'] = 0
        validated_data['status'] = 'open'
        validated_data['closed'] = False

        # Calcular due_date automaticamente se não fornecido
        if not validated_data.get('due_date'):
            credit_card = validated_data.get('credit_card')
            if credit_card and hasattr(credit_card, 'due_day') and credit_card.due_day:
                year_str = validated_data.get('year', str(date.today().year))
                month_str = validated_data.get('month', 'Jan')
                month_map = {
                    'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4,
                    'May': 5, 'Jun': 6, 'Jul': 7, 'Aug': 8,
                    'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
                }
                year = int(year_str)
                month = month_map.get(month_str, 1)

                # Vencimento é no mês seguinte ao da fatura
                due_month = month + 1 if month < 12 else 1
                due_year = year if month < 12 else year + 1

                # Ajustar dia se exceder dias do mês
                due_day = credit_card.due_day
                max_day = calendar.monthrange(due_year, due_month)[1]
                if due_day > max_day:
                    due_day = max_day

                validated_data['due_date'] = date(due_year, due_month, due_day)

        return super().create(validated_data)


class CreditCardExpensesSerializer(serializers.ModelSerializer):
    value = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        coerce_to_string=False
    )

    class Meta:
        model = CreditCardExpense
        fields = '__all__'
