from rest_framework import serializers

from .models import Wallet, WalletTransaction


class WalletSerializer(serializers.ModelSerializer):

    class Meta:
        model = Wallet
        fields = [
            "id",
            "balance",
            "created_at",
            "updated_at",
        ]

        read_only_fields = fields


class WalletTransactionSerializer(serializers.ModelSerializer):

    class Meta:
        model = WalletTransaction

        fields = [
            "id",
            "transaction_type",
            "amount",
            "status",
            "reference",
            "description",
            "created_at",
        ]

        read_only_fields = fields