from rest_framework import serializers

from .models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):

    class Meta:
        model = OrderItem

        fields = [
            "id",
            "menu_item",
            "item_name",
            "item_price",
            "quantity",
            "total_price",
        ]


class OrderSerializer(serializers.ModelSerializer):

    items = OrderItemSerializer(
        many=True,
        read_only=True
    )

    class Meta:
        model = Order

        fields = [
            "id",
            "order_number",
            "order_type",
            "status",
            "payment_status",
            "payment_reference",
            "delivery_address",
            "phone",
            "notes",
            "subtotal",
            "delivery_fee",
            "total_amount",
            "items",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "order_number",
            "status",
            "payment_status",
            "payment_reference",
            "subtotal",
            "total_amount",
            "items",
            "created_at",
            "updated_at",
        ]