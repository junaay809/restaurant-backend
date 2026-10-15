from django.shortcuts import render
import uuid

import requests

from django.conf import settings
from django.shortcuts import get_object_or_404

from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from orders.models import Order

from .models import Payment
from .serializers import PaymentSerializer
# Create your views here.

PAYSTACK_INITIALIZE_URL = (
    "https://api.paystack.co/transaction/initialize"
)

PAYSTACK_VERIFY_URL = (
    "https://api.paystack.co/transaction/verify/"
)


class InitializePaymentView(APIView):

    permission_classes = [
        permissions.IsAuthenticated
    ]

    def post(self, request):

        order_id = request.data.get("order_id")

        if not order_id:

            return Response(
                {
                    "error": "order_id is required."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        order = get_object_or_404(
            Order,
            id=order_id,
            user=request.user
        )

        if order.payment_status == "paid":

            return Response(
                {
                    "error": "This order has already been paid."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        reference = (
            f"DAMMY-{uuid.uuid4().hex}"
        )

        payment = Payment.objects.filter(
            order=order
        ).first()

        if payment and payment.status == "successful":

            return Response(
                {
                    "error": "This order has already been paid."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        if payment:

            payment.reference = reference
            payment.amount = order.total_amount
            payment.status = "pending"
            payment.save()

        else:

            payment = Payment.objects.create(
                user=request.user,
                order=order,
                reference=reference,
                amount=order.total_amount,
                currency="NGN",
                status="pending",
            )

        payload = {
            "email": request.user.email,
            "amount": int(
                order.total_amount * 100
            ),
            "currency": "NGN",
            "reference": payment.reference,

            "callback_url": (
                "https://dammy-spice-backend.onrender.com"
                "api/payments/callback/"
            ),

            "metadata": {
                "order_id": order.id,
                "order_number": order.order_number,
                "user_id": request.user.id,
            },
        }

        headers = {
            "Authorization": (
                f"Bearer {settings.PAYSTACK_SECRET_KEY}"
            ),
            "Content-Type": "application/json",
        }

        try:

            response = requests.post(
                PAYSTACK_INITIALIZE_URL,
                json=payload,
                headers=headers,
                timeout=30,
            )

            data = response.json()

        except requests.RequestException:

            return Response(
                {
                    "error": (
                        "Unable to connect to Paystack."
                    )
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        if not response.ok or not data.get("status"):

            return Response(
                {
                    "error": (
                        "Paystack payment initialization "
                        "failed."
                    ),
                    "details": data,
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {
                "message": (
                    "Payment initialized successfully."
                ),
                "payment": PaymentSerializer(
                    payment
                ).data,
                "authorization_url": (
                    data["data"]["authorization_url"]
                ),
                "access_code": (
                    data["data"]["access_code"]
                ),
                "reference": (
                    data["data"]["reference"]
                ),
            },
            status=status.HTTP_200_OK
        )


class VerifyPaymentView(APIView):

    permission_classes = [
        permissions.IsAuthenticated
    ]

    def get(self, request, reference):

        payment = get_object_or_404(
            Payment,
            reference=reference,
            user=request.user
        )

        headers = {
            "Authorization": (
                f"Bearer {settings.PAYSTACK_SECRET_KEY}"
            ),
            "Content-Type": "application/json",
        }

        try:

            response = requests.get(
                f"{PAYSTACK_VERIFY_URL}{reference}",
                headers=headers,
                timeout=30,
            )

            data = response.json()

        except requests.RequestException:

            return Response(
                {
                    "error": (
                        "Unable to connect to Paystack."
                    )
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        if not response.ok or not data.get("status"):

            return Response(
                {
                    "error": "Payment verification failed.",
                    "details": data,
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        transaction = data.get(
            "data",
            {}
        )

        transaction_status = transaction.get(
            "status"
        )

        transaction_amount = transaction.get(
            "amount",
            0
        )

        transaction_currency = transaction.get(
            "currency"
        )

        expected_amount = int(
            payment.amount * 100
        )

        if (
            transaction_status == "success"
            and transaction_currency == payment.currency
            and int(transaction_amount) == expected_amount
        ):

            payment.status = "successful"

            payment.paystack_transaction_id = str(
                transaction.get("id")
            )

            payment.payment_method = (
                transaction.get(
                    "channel"
                )
            )

            payment.save()

            order = payment.order

            order.payment_status = "paid"
            order.status = "confirmed"
            order.payment_reference = (
                payment.reference
            )

            order.save()

            return Response(
                {
                    "message": "Payment successful.",
                    "order_number": (
                        order.order_number
                    ),
                    "payment_status": "paid",
                    "order_status": "confirmed",
                },
                status=status.HTTP_200_OK
            )

        payment.status = "failed"
        payment.save()

        return Response(
            {
                "message": "Payment was not successful.",
                "payment_status": transaction_status,
            },
            status=status.HTTP_400_BAD_REQUEST
        )


class PaymentCallbackView(APIView):

    permission_classes = [
        permissions.AllowAny
    ]

    def get(self, request):

        reference = request.query_params.get(
            "reference"
        )

        if not reference:

            return Response(
                {
                    "error": "Payment reference is missing."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {
                "message": (
                    "Payment completed. "
                    "Use the reference to verify "
                    "the transaction."
                ),
                "reference": reference,
            }
        )