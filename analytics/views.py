from django.shortcuts import render
from decimal import Decimal

from django.db.models import Sum
from django.utils import timezone

from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from orders.models import Order
from payments.models import Payment

from .serializers import DashboardSerializer
# Create your views here.

class IsRestaurantOwner(permissions.BasePermission):

    def has_permission(self, request, view):

        return (
            request.user
            and request.user.is_authenticated
            and request.user.is_staff
        )


class DashboardView(APIView):

    permission_classes = [
        IsRestaurantOwner
    ]

    def get(self, request):

        today = timezone.localdate()

        orders = Order.objects.all()

        today_orders = orders.filter(
            created_at__date=today
        )

        paid_orders = orders.filter(
            payment_status="paid"
        )

        completed_orders = orders.filter(
            status="delivered"
        )

        pending_orders = orders.filter(
            status="pending"
        )

        total_revenue = paid_orders.aggregate(
            total=Sum("total_amount")
        )["total"] or Decimal("0.00")

        today_revenue = paid_orders.filter(
            created_at__date=today
        ).aggregate(
            total=Sum("total_amount")
        )["total"] or Decimal("0.00")

        failed_payments = Payment.objects.filter(
            status="failed"
        ).count()

        data = {
            "total_revenue": total_revenue,
            "today_revenue": today_revenue,
            "total_orders": orders.count(),
            "today_orders": today_orders.count(),
            "pending_orders": pending_orders.count(),
            "completed_orders": completed_orders.count(),
            "paid_orders": paid_orders.count(),
            "failed_payments": failed_payments,
        }

        serializer = DashboardSerializer(data)

        return Response(
            serializer.data
        )