from django.urls import path

from .views import (
    InitializePaymentView,
    VerifyPaymentView,
    PaymentCallbackView,
)


urlpatterns = [

    path(
        "initialize/",
        InitializePaymentView.as_view(),
        name="payment-initialize"
    ),

    path(
        "verify/<str:reference>/",
        VerifyPaymentView.as_view(),
        name="payment-verify"
    ),

    path(
        "callback/",
        PaymentCallbackView.as_view(),
        name="payment-callback"
    ),

]