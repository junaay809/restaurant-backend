from rest_framework import serializers


class DashboardSerializer(serializers.Serializer):

    total_revenue = serializers.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    today_revenue = serializers.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    total_orders = serializers.IntegerField()

    today_orders = serializers.IntegerField()

    pending_orders = serializers.IntegerField()

    completed_orders = serializers.IntegerField()

    paid_orders = serializers.IntegerField()

    failed_payments = serializers.IntegerField()