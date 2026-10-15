from rest_framework import serializers

from .models import Category, MenuItem, DiscoveryTag, Review


# ============================================================
# DISCOVERY TAG SERIALIZER
# ============================================================

class DiscoveryTagSerializer(serializers.ModelSerializer):

    class Meta:
        model = DiscoveryTag

        fields = [
            "id",
            "type",
            "name",
            "code",
        ]


# ============================================================
# MENU ITEM SERIALIZER
# ============================================================

class MenuItemSerializer(serializers.ModelSerializer):

    category_name = serializers.CharField(
        source="category.name",
        read_only=True
    )

    discovery_tags = DiscoveryTagSerializer(
        many=True,
        read_only=True
    )

    class Meta:
        model = MenuItem

        fields = [
            "id",
            "category",
            "category_name",
            "name",
            "slug",
            "description",
            "price",
            "image",
            "country",
            "rating",
            "is_available",
            "is_featured",
            "is_popular",
            "is_spicy",
            "preparation_time",
            "display_order",
            "discovery_tags",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "slug",
            "discovery_tags",
            "created_at",
            "updated_at",
        ]


# ============================================================
# CATEGORY SERIALIZER
# ============================================================

class CategorySerializer(serializers.ModelSerializer):

    items = MenuItemSerializer(
        many=True,
        read_only=True
    )

    class Meta:
        model = Category

        fields = [
            "id",
            "name",
            "slug",
            "description",
            "image",
            "is_active",
            "display_order",
            "items",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "slug",
            "created_at",
            "updated_at",
        ]

# ============================================================
# REVIEW SERIALIZER
# ============================================================

class ReviewSerializer(serializers.ModelSerializer):

    username = serializers.CharField(
        source="user.username",
        read_only=True
    )

    class Meta:
        model = Review

        fields = [
            "id",
            "user",
            "username",
            "menu_item",
            "rating",
            "comment",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "user",
            "username",
            "menu_item",
            "created_at",
        ]

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError(
                "Rating must be between 1 and 5."
            )
        return value