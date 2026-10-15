from django.db import models
from django.utils.text import slugify


# ============================================================
# MENU CATEGORY
# ============================================================

class Category(models.Model):

    name = models.CharField(
        max_length=100,
        unique=True
    )

    slug = models.SlugField(
        max_length=120,
        unique=True,
        blank=True
    )

    description = models.TextField(
        blank=True
    )

    image = models.ImageField(
        upload_to="menu/categories/",
        blank=True,
        null=True
    )

    is_active = models.BooleanField(
        default=True
    )

    display_order = models.PositiveIntegerField(
        default=0
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["display_order", "name"]
        verbose_name = "Category"
        verbose_name_plural = "Categories"

    def save(self, *args, **kwargs):

        if not self.slug:
            self.slug = slugify(self.name)

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


# ============================================================
# DISCOVERY TAG
# ============================================================

class DiscoveryTag(models.Model):

    TYPE_CHOICES = [
        ("mood", "Mood"),
        ("craving", "Craving"),
        ("looks", "Looks"),
        ("hunger", "Hunger"),
        ("experience", "Experience"),
    ]

    type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES
    )

    name = models.CharField(
        max_length=100
    )

    code = models.SlugField(
        max_length=100
    )

    class Meta:
        ordering = ["type", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["type", "code"],
                name="unique_discovery_tag_type_code"
            )
        ]

    def __str__(self):
        return f"{self.get_type_display()} - {self.name}"


# ============================================================
# MENU ITEM
# ============================================================

class MenuItem(models.Model):

    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="items"
    )

    name = models.CharField(
        max_length=150
    )

    country = models.CharField(
        max_length=50,
        blank=True
    )

    rating = models.DecimalField(
        max_digits=2,
        decimal_places=1,
        default=0.0
    )

    slug = models.SlugField(
        max_length=180,
        unique=True,
        blank=True
    )

    description = models.TextField(
        blank=True
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    image = models.ImageField(
        upload_to="menu/items/",
        blank=True,
        null=True
    )

    is_available = models.BooleanField(
        default=True
    )

    is_featured = models.BooleanField(
        default=False
    )

    is_popular = models.BooleanField(
        default=False
    )

    is_spicy = models.BooleanField(
        default=False
    )

    preparation_time = models.PositiveIntegerField(
        default=15,
        help_text="Preparation time in minutes"
    )

    display_order = models.PositiveIntegerField(
        default=0
    )

    # ========================================================
    # DISCOVER TAGS
    # ========================================================

    discovery_tags = models.ManyToManyField(
        DiscoveryTag,
        blank=True,
        related_name="menu_items"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["display_order", "name"]

    def save(self, *args, **kwargs):

        if not self.slug:
            self.slug = slugify(self.name)

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


# ============================================================
# CUSTOMER REVIEWS
# ============================================================

class Review(models.Model):

    user = models.ForeignKey(
    "accounts.User",
    on_delete=models.CASCADE,
    related_name="reviews",
    null=True,
    blank=True
)

    menu_item = models.ForeignKey(
        MenuItem,
        on_delete=models.CASCADE,
        related_name="reviews"
    )

    rating = models.PositiveSmallIntegerField()

    comment = models.TextField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} - {self.menu_item.name}"