from django.urls import path

from .views import (
    OrderListView,
    OrderDetailView,
    CreateOrderView,
    VerifyOrderPaymentView,
)


urlpatterns = [

    path(
        "",
        OrderListView.as_view(),
        name="order-list"
    ),

    path(
        "create/",
        CreateOrderView.as_view(),
        name="order-create"
    ),

    path(
        "verify-payment/<str:reference>/",
        VerifyOrderPaymentView.as_view(),
        name="verify-order-payment"
    ),

    path(
        "<int:pk>/",
        OrderDetailView.as_view(),
        name="order-detail"
    ),

]