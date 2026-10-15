from django.shortcuts import render
from django.shortcuts import get_object_or_404

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Notification
from .serializers import NotificationSerializer
# Create your views here.

class NotificationListView(generics.ListAPIView):

    serializer_class = NotificationSerializer

    permission_classes = [
        permissions.IsAuthenticated
    ]

    def get_queryset(self):

        return Notification.objects.filter(
            user=self.request.user
        )


class NotificationDetailView(generics.RetrieveAPIView):

    serializer_class = NotificationSerializer

    permission_classes = [
        permissions.IsAuthenticated
    ]

    def get_queryset(self):

        return Notification.objects.filter(
            user=self.request.user
        )


class MarkNotificationReadView(APIView):

    permission_classes = [
        permissions.IsAuthenticated
    ]

    def patch(self, request, pk):

        notification = get_object_or_404(
            Notification,
            id=pk,
            user=request.user
        )

        notification.is_read = True
        notification.save()

        return Response(
            {
                "message": "Notification marked as read."
            },
            status=status.HTTP_200_OK
        )


class MarkAllNotificationsReadView(APIView):

    permission_classes = [
        permissions.IsAuthenticated
    ]

    def patch(self, request):

        Notification.objects.filter(
            user=request.user,
            is_read=False
        ).update(
            is_read=True
        )

        return Response(
            {
                "message": (
                    "All notifications marked as read."
                )
            },
            status=status.HTTP_200_OK
        )