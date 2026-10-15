from decimal import Decimal
import uuid
import requests

from django.conf import settings
from django.db import transaction

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Order, OrderItem
from .serializers import OrderSerializer

from cart.models import Cart
from wallet.models import Wallet, WalletTransaction


class OrderListView(generics.ListAPIView):

    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(
            user=self.request.user
        ).prefetch_related("items").order_by("-created_at")


class OrderDetailView(generics.RetrieveAPIView):

    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(
            user=self.request.user
        ).prefetch_related("items")


class CreateOrderView(generics.CreateAPIView):

    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def create(self, request, *args, **kwargs):

        user = request.user

        delivery_address = request.data.get(
            "delivery_address",
            ""
        )

        phone = request.data.get(
            "phone",
            ""
        )

        notes = request.data.get(
            "notes",
            ""
        )

        payment_method = request.data.get(
            "payment_method",
            ""
        )

        delivery_fee = Decimal(
            str(
                request.data.get(
                    "delivery_fee",
                    "0"
                )
            )
        )

        # -----------------------------------------
        # CHECK PAYMENT METHOD
        # -----------------------------------------

        if payment_method not in ["wallet", "paystack"]:
            return Response(
                {
                    "error": "Please select a valid payment method."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # -----------------------------------------
        # GET CART
        # -----------------------------------------

        try:
            cart = Cart.objects.get(
                user=user
            )
        except Cart.DoesNotExist:

            return Response(
                {
                    "error": "Your cart is empty."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        cart_items = cart.items.select_related(
            "menu_item"
        ).all()

        if not cart_items.exists():

            return Response(
                {
                    "error": "Your cart is empty."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # -----------------------------------------
        # CALCULATE TOTAL
        # -----------------------------------------

        subtotal = Decimal("0.00")

        for cart_item in cart_items:

            subtotal += (
                cart_item.menu_item.price
                * cart_item.quantity
            )

        total_amount = subtotal + delivery_fee

        # -----------------------------------------
        # CREATE ORDER
        # -----------------------------------------

        order = Order.objects.create(
            user=user,
            delivery_address=delivery_address,
            phone=phone,
            notes=notes,
            subtotal=subtotal,
            delivery_fee=delivery_fee,
            total_amount=total_amount,
            payment_status="pending",
            status="pending",
        )

        # -----------------------------------------
        # COPY CART ITEMS INTO ORDER
        # -----------------------------------------

        for cart_item in cart_items:

            menu_item = cart_item.menu_item

            OrderItem.objects.create(
                order=order,
                menu_item=menu_item,
                item_name=menu_item.name,
                item_price=menu_item.price,
                quantity=cart_item.quantity,
                total_price=(
                    menu_item.price
                    * cart_item.quantity
                ),
            )

        # =================================================
        # WALLET PAYMENT
        # =================================================

        if payment_method == "wallet":

            wallet, created = Wallet.objects.select_for_update().get_or_create(
                user=user
            )

            if wallet.balance < total_amount:

                return Response(
                    {
                        "error": "Insufficient wallet balance.",
                        "balance": wallet.balance,
                        "required": total_amount,
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Deduct money from wallet
            wallet.balance -= total_amount
            wallet.save()

            # Create wallet transaction
            WalletTransaction.objects.create(
                wallet=wallet,
                transaction_type="debit",
                amount=total_amount,
                status="successful",
                reference=f"ORDER-{uuid.uuid4().hex.upper()}",
                description=f"Payment for order {order.order_number}",
            )

            # Mark order as paid
            order.payment_status = "paid"
            order.status = "confirmed"
            order.payment_reference = (
                f"WALLET-{uuid.uuid4().hex.upper()}"
            )
            order.save()

            # Clear cart ONLY after successful wallet payment
            cart_items.delete()

            serializer = self.get_serializer(order)

            return Response(
                {
                    "message": "Order paid successfully with wallet.",
                    "payment_method": "wallet",
                    "order": serializer.data,
                    "wallet_balance": wallet.balance,
                },
                status=status.HTTP_201_CREATED
            )

        # =================================================
        # PAYSTACK PAYMENT
        # =================================================

        if payment_method == "paystack":

            reference = f"ORDER-{uuid.uuid4().hex.upper()}"

            amount_in_kobo = int(
                total_amount * Decimal("100")
            )

            headers = {
                "Authorization": (
                    f"Bearer {settings.PAYSTACK_SECRET_KEY}"
                ),
                "Content-Type": "application/json",
            }

            data = {
                "email": user.email,
                "amount": amount_in_kobo,
                "reference": reference,
                "currency": "NGN",
                "metadata": {
                    "type": "order_payment",
                    "order_id": order.id,
                    "user_id": user.id,
                },
            }

            try:

                response = requests.post(
                    "https://api.paystack.co/transaction/initialize",
                    headers=headers,
                    json=data,
                    timeout=30,
                )

                response_data = response.json()

            except requests.RequestException:

                return Response(
                    {
                        "error": "Unable to connect to Paystack."
                    },
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )

            if not response_data.get("status"):

                return Response(
                    {
                        "error": (
                            "Paystack could not initialize "
                            "the payment."
                        ),
                        "details": response_data.get(
                            "message"
                        ),
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Save Paystack reference
            order.payment_reference = reference
            order.payment_status = "pending"
            order.save()

            serializer = self.get_serializer(order)

            return Response(
                {
                    "message": "Paystack payment initialized.",
                    "payment_method": "paystack",
                    "order": serializer.data,
                    "authorization_url": (
                        response_data["data"]
                        ["authorization_url"]
                    ),
                    "access_code": (
                        response_data["data"]
                        ["access_code"]
                    ),
                    "reference": reference,
                },
                status=status.HTTP_201_CREATED
            )


# =====================================================
# VERIFY PAYSTACK ORDER PAYMENT
# =====================================================

class VerifyOrderPaymentView(APIView):

    permission_classes = [
        permissions.IsAuthenticated
    ]

    @transaction.atomic
    def get(self, request, reference):

        user = request.user

        try:

            order = Order.objects.select_for_update().get(
                payment_reference=reference,
                user=user
            )

        except Order.DoesNotExist:

            return Response(
                {
                    "error": "Order payment not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        # -----------------------------------------
        # ALREADY PAID
        # -----------------------------------------

        if order.payment_status == "paid":

            return Response(
                {
                    "message": "Order payment already verified.",
                    "order": OrderSerializer(order).data,
                },
                status=status.HTTP_200_OK
            )

        # -----------------------------------------
        # VERIFY WITH PAYSTACK
        # -----------------------------------------

        headers = {
            "Authorization": (
                f"Bearer {settings.PAYSTACK_SECRET_KEY}"
            )
        }

        try:

            response = requests.get(
                (
                    "https://api.paystack.co/transaction/"
                    f"verify/{reference}"
                ),
                headers=headers,
                timeout=30,
            )

            response_data = response.json()

        except requests.RequestException:

            return Response(
                {
                    "error": "Unable to connect to Paystack."
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        if not response_data.get("status"):

            return Response(
                {
                    "error": "Payment verification failed."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        payment_data = response_data.get(
            "data",
            {}
        )

        # -----------------------------------------
        # PAYMENT NOT SUCCESSFUL
        # -----------------------------------------

        if payment_data.get("status") != "success":

            return Response(
                {
                    "error": "Payment was not successful."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # -----------------------------------------
        # CHECK PAYMENT AMOUNT
        # -----------------------------------------

        paid_amount = (
            Decimal(
                str(
                    payment_data.get(
                        "amount",
                        0
                    )
                )
            )
            / Decimal("100")
        )

        if paid_amount != order.total_amount:

            return Response(
                {
                    "error": "Payment amount does not match the order."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # -----------------------------------------
        # MARK ORDER AS PAID
        # -----------------------------------------

        order.payment_status = "paid"
        order.status = "confirmed"
        order.save()

        # -----------------------------------------
        # CLEAR CART
        # -----------------------------------------

        try:

            cart = Cart.objects.get(
                user=user
            )

            cart.items.all().delete()

        except Cart.DoesNotExist:

            pass

        return Response(
            {
                "message": "Payment verified successfully.",
                "order": OrderSerializer(order).data,
            },
            status=status.HTTP_200_OK
        )