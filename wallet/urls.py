from django.urls import path

from .views import (
    WalletView,
    WalletTransactionListView,
    AddMoneyView,
    VerifyWalletDepositView,
)


urlpatterns = [

    path(
        "",
        WalletView.as_view(),
        name="wallet"
    ),

    path(
        "transactions/",
        WalletTransactionListView.as_view(),
        name="wallet-transactions"
    ),

    path(
        "add-money/",
        AddMoneyView.as_view(),
        name="wallet-add-money"
    ),

    path(
        "verify/<str:reference>/",
        VerifyWalletDepositView.as_view(),
        name="wallet-verify"
    ),

]