from rest_framework import serializers

from .models import Payout, Transaction, Wallet


class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = ["id", "balance_amount", "currency"]


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = [
            "id",
            "direction",
            "amount",
            "reason",
            "reference_type",
            "reference_id",
            "created_at",
        ]


class PayoutSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payout
        fields = [
            "id",
            "period_start",
            "period_end",
            "amount_gross",
            "amount_net",
            "status",
            "paid_at",
            "created_at",
        ]
