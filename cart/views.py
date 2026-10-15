from django.shortcuts import render
from django.shortcuts import get_object_or_404

from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from menu.models import MenuItem

from .models import Cart, CartItem
from .serializers import CartSerializer
# Create your views here.

# ============================================================
# GET CART
# ============================================================

class CartView(APIView):

    permission_classes = [
        permissions.IsAuthenticated
    ]

    def get_cart(self, user):

        cart, created = Cart.objects.get_or_create(
            user=user
        )

        return cart

    def get(self, request):

        cart = self.get_cart(request.user)

        serializer = CartSerializer(cart)

        return Response(
            serializer.data
        )


# ============================================================
# ADD ITEM TO CART
# ============================================================

class AddToCartView(APIView):

    permission_classes = [
        permissions.IsAuthenticated
    ]

    def post(self, request):

        menu_item_id = request.data.get(
            "menu_item_id"
        )

        quantity = request.data.get(
            "quantity",
            1
        )

        if not menu_item_id:
            return Response(
                {
                    "error": "menu_item_id is required."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            quantity = int(quantity)
        except (TypeError, ValueError):

            return Response(
                {
                    "error": "Quantity must be a number."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        if quantity < 1:

            return Response(
                {
                    "error": "Quantity must be at least 1."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        menu_item = get_object_or_404(
            MenuItem,
            id=menu_item_id
        )

        if not menu_item.is_available:

            return Response(
                {
                    "error": "This item is currently unavailable."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        cart, created = Cart.objects.get_or_create(
            user=request.user
        )

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            menu_item=menu_item
        )

        if created:
            cart_item.quantity = quantity
        else:
            cart_item.quantity += quantity

        cart_item.save()

        serializer = CartSerializer(cart)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )


# ============================================================
# UPDATE CART ITEM
# ============================================================

class UpdateCartItemView(APIView):

    permission_classes = [
        permissions.IsAuthenticated
    ]

    def patch(self, request, item_id):

        cart = get_object_or_404(
            Cart,
            user=request.user
        )

        cart_item = get_object_or_404(
            CartItem,
            id=item_id,
            cart=cart
        )

        quantity = request.data.get(
            "quantity"
        )

        if quantity is None:

            return Response(
                {
                    "error": "quantity is required."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            quantity = int(quantity)
        except (TypeError, ValueError):

            return Response(
                {
                    "error": "Quantity must be a number."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        if quantity < 1:

            return Response(
                {
                    "error": "Quantity must be at least 1."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        cart_item.quantity = quantity
        cart_item.save()

        serializer = CartSerializer(cart)

        return Response(
            serializer.data
        )


# ============================================================
# REMOVE ITEM FROM CART
# ============================================================

class RemoveFromCartView(APIView):

    permission_classes = [
        permissions.IsAuthenticated
    ]

    def delete(self, request, item_id):

        cart = get_object_or_404(
            Cart,
            user=request.user
        )

        cart_item = get_object_or_404(
            CartItem,
            id=item_id,
            cart=cart
        )

        cart_item.delete()

        serializer = CartSerializer(cart)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )


# ============================================================
# CLEAR CART
# ============================================================

class ClearCartView(APIView):

    permission_classes = [
        permissions.IsAuthenticated
    ]

    def delete(self, request):

        cart = get_object_or_404(
            Cart,
            user=request.user
        )

        cart.items.all().delete()

        serializer = CartSerializer(cart)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )