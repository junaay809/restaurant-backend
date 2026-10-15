from django.urls import path

from .views import (
    NotificationListView,
    NotificationDetailView,
    MarkNotificationReadView,
    MarkAllNotificationsReadView,
)


urlpatterns = [

    path(
        "",
        NotificationListView.as_view(),
        name="notification-list"
    ),

    path(
        "read-all/",
        MarkAllNotificationsReadView.as_view(),
        name="notification-read-all"
    ),

    path(
        "<int:pk>/",
        NotificationDetailView.as_view(),
        name="notification-detail"
    ),

    path(
        "<int:pk>/read/",
        MarkNotificationReadView.as_view(),
        name="notification-read"
    ),
]