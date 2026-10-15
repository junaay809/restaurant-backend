from rest_framework import serializers

from .models import Cart, CartItem


# ============================================================
# CART ITEM SERIALIZER
# ============================================================

class CartItemSerializer(serializers.ModelSerializer):

    menu_item_name = serializers.CharField(
        source="menu_item.name",
        read_only=True
    )

    menu_item_image = serializers.ImageField(
        source="menu_item.image",
        read_only=True
    )

    unit_price = serializers.DecimalField(
        source="menu_item.price",
        max_digits=10,
        decimal_places=2,
        read_only=True
    )

    total_price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True
    )

    class Meta:
        model = CartItem

        fields = [
            "id",
            "menu_item",
            "menu_item_name",
            "menu_item_image",
            "unit_price",
            "quantity",
            "total_price",
            "added_at",
        ]

        read_only_fields = [
            "id",
            "menu_item_name",
            "menu_item_image",
            "unit_price",
            "total_price",
            "added_at",
        ]


# ============================================================
# CART SERIALIZER
# ============================================================

class CartSerializer(serializers.ModelSerializer):

    items = CartItemSerializer(
        many=True,
        read_only=True
    )

    total_items = serializers.IntegerField(
        read_only=True
    )

    subtotal = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True
    )

    class Meta:
        model = Cart

        fields = [
            "id",
            "items",
            "total_items",
            "subtotal",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "items",
            "total_items",
            "subtotal",
            "created_at",
            "updated_at",
        ]