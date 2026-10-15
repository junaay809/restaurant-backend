from django.urls import path

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from .views import (
    RegisterView,
    MeView,
    UpdateProfileView,
    ChangePasswordView,
    DeleteAccountView,
    AddressListCreateView,
    AddressDetailView,
    SetDefaultAddressView,
)

from .password_reset_views import ForgotPasswordView, ResetPasswordView


urlpatterns = [

    # ============================================================
    # AUTHENTICATION
    # ============================================================

    path(
        "login/",
        TokenObtainPairView.as_view(),
        name="login",
    ),

    path(
        "token/refresh/",
        TokenRefreshView.as_view(),
        name="token-refresh",
    ),


    # ============================================================
    # REGISTRATION
    # ============================================================

    path(
        "register/",
        RegisterView.as_view(),
        name="register",
    ),


    # ============================================================
    # CURRENT ACCOUNT
    # ============================================================

    path(
        "me/",
        MeView.as_view(),
        name="me",
    ),


    # ============================================================
    # UPDATE PROFILE
    # ============================================================

    path(
        "profile/update/",
        UpdateProfileView.as_view(),
        name="profile-update",
    ),


    # ============================================================
    # CHANGE PASSWORD
    # ============================================================

    path(
        "password/change/",
        ChangePasswordView.as_view(),
        name="password-change",
    ),


    # ============================================================
    # DELETE ACCOUNT
    # ============================================================

    path(
        "delete/",
        DeleteAccountView.as_view(),
        name="delete-account",
    ),

    # ============================================================
    path(
        "addresses/",
        AddressListCreateView.as_view(),
        name="address-list-create",
    ),

    path(
        "addresses/<int:pk>/",
        AddressDetailView.as_view(),
        name="address-detail",
    ),

    path(
        "addresses/<int:pk>/default/",
        SetDefaultAddressView.as_view(),
        name="address-default",
    ),

    path("forgot-password/", ForgotPasswordView.as_view(), name="forgot-password"),
path("reset-password/", ResetPasswordView.as_view(), name="reset-password"),
]