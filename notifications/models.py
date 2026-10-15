from django.db import models
from django.conf import settings
# Create your models here.

class Notification(models.Model):

    TYPE_CHOICES = [
        ("order", "Order"),
        ("payment", "Payment"),
        ("delivery", "Delivery"),
        ("system", "System"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications"
    )

    notification_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default="system"
    )

    title = models.CharField(
        max_length=200
    )

    message = models.TextField()

    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.CASCADE,
        related_name="notifications",
        blank=True,
        null=True
    )

    is_read = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title