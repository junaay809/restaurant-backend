from django.shortcuts import render
import uuid
from decimal import Decimal

import requests

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Wallet, WalletDeposit, WalletTransaction
from .serializers import (
    WalletSerializer,
    WalletTransactionSerializer,
)
# Create your views here.

class WalletView(APIView):

    permission_classes = [
        permissions.IsAuthenticated
    ]

    def get(self, request):

        wallet, created = Wallet.objects.get_or_create(
            user=request.user
        )

        serializer = WalletSerializer(wallet)

        return Response(serializer.data)


class WalletTransactionListView(APIView):

    permission_classes = [
        permissions.IsAuthenticated
    ]

    def get(self, request):

        wallet, created = Wallet.objects.get_or_create(
            user=request.user
        )

        transactions = WalletTransaction.objects.filter(
            wallet=wallet
        )

        serializer = WalletTransactionSerializer(
            transactions,
            many=True
        )

        return Response(serializer.data)


class AddMoneyView(APIView):

    permission_classes = [
        permissions.IsAuthenticated
    ]

    def post(self, request):

        amount = request.data.get("amount")

        if not amount:
            return Response(
                {
                    "error": "Amount is required."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            amount = Decimal(str(amount))
        except Exception:
            return Response(
                {
                    "error": "Invalid amount."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        if amount <= 0:
            return Response(
                {
                    "error": "Amount must be greater than zero."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        wallet, created = Wallet.objects.get_or_create(
            user=request.user
        )

        reference = (
            f"WALLET-{uuid.uuid4().hex.upper()}"
        )

        deposit = WalletDeposit.objects.create(
            wallet=wallet,
            amount=amount,
            reference=reference,
            status="pending"
        )

        amount_in_kobo = int(amount * 100)

        headers = {
            "Authorization": (
                f"Bearer {settings.PAYSTACK_SECRET_KEY}"
            ),
            "Content-Type": "application/json",
        }

        data = {
            "email": request.user.email,
            "amount": amount_in_kobo,
            "reference": reference,
            "currency": "NGN",
            "metadata": {
                "type": "wallet_deposit",
                "user_id": request.user.id,
                "wallet_id": wallet.id,
                "deposit_id": deposit.id,
            },
        }

        try:

            response = requests.post(
                "https://api.paystack.co/transaction/initialize",
                headers=headers,
                json=data,
                timeout=30
            )

            response_data = response.json()

        except requests.RequestException:

            deposit.status = "failed"
            deposit.save()

            return Response(
                {
                    "error": "Unable to connect to Paystack."
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        if not response_data.get("status"):

            deposit.status = "failed"
            deposit.save()

            return Response(
                {
                    "error": "Paystack could not initialize payment.",
                    "details": response_data.get("message")
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {
                "message": "Wallet funding initialized.",
                "reference": reference,
                "authorization_url": (
                    response_data["data"]["authorization_url"]
                ),
                "access_code": (
                    response_data["data"]["access_code"]
                ),
            },
            status=status.HTTP_201_CREATED
        )


class VerifyWalletDepositView(APIView):

    permission_classes = [
        permissions.IsAuthenticated
    ]

    def get(self, request, reference):

        try:
            deposit = WalletDeposit.objects.select_related(
                "wallet",
                "wallet__user"
            ).get(
                reference=reference,
                wallet__user=request.user
            )

        except WalletDeposit.DoesNotExist:

            return Response(
                {
                    "error": "Deposit not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        if deposit.status == "successful":

            return Response(
                {
                    "message": "This deposit has already been processed.",
                    "balance": deposit.wallet.balance,
                }
            )

        headers = {
            "Authorization": (
                f"Bearer {settings.PAYSTACK_SECRET_KEY}"
            ),
        }

        try:

            response = requests.get(
                (
                    "https://api.paystack.co/transaction/verify/"
                    f"{reference}"
                ),
                headers=headers,
                timeout=30
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

            deposit.status = "failed"
            deposit.save()

            return Response(
                {
                    "error": "Payment verification failed."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        payment_data = response_data.get("data", {})

        if payment_data.get("status") != "success":

            deposit.status = "failed"
            deposit.save()

            return Response(
                {
                    "error": "Payment was not successful."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        paid_amount = Decimal(
            payment_data.get("amount", 0)
        ) / Decimal("100")

        if paid_amount != deposit.amount:

            deposit.status = "failed"
            deposit.save()

            return Response(
                {
                    "error": "Payment amount does not match."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():

            deposit = WalletDeposit.objects.select_for_update().get(
                id=deposit.id
            )

            if deposit.status == "successful":

                return Response(
                    {
                        "message": "Deposit already processed."
                    }
                )

            wallet = Wallet.objects.select_for_update().get(
                id=deposit.wallet.id
            )

            wallet.balance += deposit.amount
            wallet.save()

            WalletTransaction.objects.create(
                wallet=wallet,
                transaction_type="credit",
                amount=deposit.amount,
                status="successful",
                reference=deposit.reference,
                description="Wallet funding via Paystack"
            )

            deposit.status = "successful"
            deposit.completed_at = timezone.now()
            deposit.save()

        return Response(
            {
                "message": "Wallet funded successfully.",
                "amount_added": deposit.amount,
                "balance": wallet.balance,
            },
            status=status.HTTP_200_OK
        )