from django.urls import path
from . import views

from .views import (
    CartView,
    AddToCartView,
    UpdateCartItemView,
    RemoveFromCartView,
    ClearCartView,
)


urlpatterns = [

    # View current cart
    path(
        "",
        CartView.as_view(),
        name="cart"
    ),

    # Add item
    path(
        "add/",
        AddToCartView.as_view(),
        name="cart-add"
    ),

    # Update quantity
    path(
        "item/<int:item_id>/",
        UpdateCartItemView.as_view(),
        name="cart-update"
    ),

    # Remove item
    path(
        "item/<int:item_id>/remove/",
        RemoveFromCartView.as_view(),
        name="cart-remove"
    ),

    # Clear entire cart
    path(
        "clear/",
        ClearCartView.as_view(),
        name="cart-clear"
    ),
]