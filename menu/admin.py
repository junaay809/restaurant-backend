from django.contrib import admin

from .models import Category, MenuItem, DiscoveryTag, Review
from .forms import MenuItemAdminForm


# ============================================================
# DISCOVERY TAG ADMIN
# ============================================================

@admin.register(DiscoveryTag)
class DiscoveryTagAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "type",
        "code",
    )

    list_filter = (
        "type",
    )

    search_fields = (
        "name",
        "code",
    )

    ordering = (
        "type",
        "name",
    )


# ============================================================
# CATEGORY ADMIN
# ============================================================

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "slug",
        "is_active",
        "display_order",
        "created_at",
    )

    list_filter = (
        "is_active",
    )

    search_fields = (
        "name",
        "description",
    )

    ordering = (
        "display_order",
        "name",
    )

    prepopulated_fields = {
        "slug": ("name",),
    }


# ============================================================
# MENU ITEM ADMIN
# ============================================================

@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):

    form = MenuItemAdminForm

    list_display = (
        "name",
        "category",
        "country",
        "price",
        "rating",
        "is_available",
        "is_featured",
        "is_popular",
        "is_spicy",
        "display_order",
    )

    list_filter = (
        "category",
        "is_available",
        "is_featured",
        "is_popular",
        "is_spicy",
    )

    search_fields = (
        "name",
        "description",
        "country",
    )

    ordering = (
        "display_order",
        "name",
    )

    prepopulated_fields = {
        "slug": ("name",),
    }

    fieldsets = (
        (
            "Basic Information",
            {
                "fields": (
                    "category",
                    "name",
                    "country",
                    "slug",
                    "description",
                    "image",
                )
            },
        ),

        (
            "Pricing & Rating",
            {
                "fields": (
                    "price",
                    "rating",
                )
            },
        ),

        (
            "Availability & Settings",
            {
                "fields": (
                    "is_available",
                    "is_featured",
                    "is_popular",
                    "is_spicy",
                    "preparation_time",
                    "display_order",
                )
            },
        ),

        (
            "Discover — Mood",
            {
                "fields": (
                    "mood_tags",
                )
            },
        ),

        (
            "Discover — Craving",
            {
                "fields": (
                    "craving_tags",
                )
            },
        ),

        (
            "Discover — Looks",
            {
                "fields": (
                    "looks_tags",
                )
            },
        ),

        (
            "Discover — Hunger",
            {
                "fields": (
                    "hunger_tags",
                )
            },
        ),

        (
            "Discover — Experience",
            {
                "fields": (
                    "experience_tags",
                )
            },
        ),
    )

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)

        item = form.instance

        tag_ids = (
            request.POST.getlist("mood_tags")
            + request.POST.getlist("craving_tags")
            + request.POST.getlist("looks_tags")
            + request.POST.getlist("hunger_tags")
            + request.POST.getlist("experience_tags")
        )

        item.discovery_tags.set(tag_ids)


# ============================================================
# REVIEW ADMIN
# ============================================================

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "menu_item",
        "rating",
        "created_at",
    )

    list_filter = (
        "rating",
        "created_at",
    )

    search_fields = (
        "user__username",
        "menu_item__name",
        "comment",
    )

    ordering = (
        "-created_at",
    )