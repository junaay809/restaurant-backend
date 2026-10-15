from django.contrib.auth import update_session_auth_hash
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Address, User
from .serializers import (
    RegisterSerializer,
    UserSerializer,
    AddressSerializer,
)


# ============================================================
# REGISTER
# ============================================================

class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


# ============================================================
# CURRENT USER / ACCOUNT
# ============================================================

class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


# ============================================================
# UPDATE ACCOUNT / PROFILE
# ============================================================

class UpdateProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request):
        serializer = UserSerializer(
            request.user,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


# ============================================================
# CHANGE PASSWORD
# ============================================================

class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):

        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")

        if not old_password or not new_password:
            return Response(
                {
                    "error": "Both old_password and new_password are required."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        user = request.user

        if not user.check_password(old_password):
            return Response(
                {
                    "error": "Your current password is incorrect."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        if len(new_password) < 8:
            return Response(
                {
                    "error": "Your new password must be at least 8 characters."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(new_password)
        user.save()

        # Keeps the user logged in after changing password
        update_session_auth_hash(request, user)

        return Response(
            {
                "message": "Password changed successfully."
            },
            status=status.HTTP_200_OK
        )


# ============================================================
# DELETE ACCOUNT
# ============================================================

class DeleteAccountView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request):

        user = request.user
        user.delete()

        return Response(
            {
                "message": "Your account has been deleted successfully."
            },
            status=status.HTTP_200_OK
        )


class AddressListCreateView(generics.ListCreateAPIView):

    serializer_class = AddressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Address.objects.filter(
            user=self.request.user
        ).order_by("-is_default", "-created_at")

    def perform_create(self, serializer):

        user = self.request.user

        has_default = Address.objects.filter(
            user=user,
            is_default=True
        ).exists()

        serializer.save(
            user=user,
            is_default=not has_default
        )

# ============================================================

class AddressDetailView(generics.RetrieveUpdateDestroyAPIView):

    serializer_class = AddressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Address.objects.filter(
            user=self.request.user
        )


class SetDefaultAddressView(APIView):

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):

        try:
            address = Address.objects.get(
                pk=pk,
                user=request.user
            )
        except Address.DoesNotExist:
            return Response(
                {"error": "Address not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        Address.objects.filter(
            user=request.user
        ).update(
            is_default=False
        )

        address.is_default = True
        address.save()

        serializer = AddressSerializer(address)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )