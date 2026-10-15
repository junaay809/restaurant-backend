from django.urls import path

from .views import (
    CategoryListView,
    CategoryDetailView,
    MenuItemListView,
    MenuItemDetailView,
    DiscoverRecommendationView,
    ReviewListCreateView,
)


urlpatterns = [
    path("categories/", CategoryListView.as_view(), name="category-list"),
    path("categories/<slug:slug>/", CategoryDetailView.as_view(), name="category-detail"),

    path(
        "discover/",
        DiscoverRecommendationView.as_view(),
        name="discover-recommendation",
    ),

    path("", MenuItemListView.as_view(), name="menu-list"),
    path("<slug:slug>/", MenuItemDetailView.as_view(), name="menu-detail"),
    path(
    "items/<int:menu_item_id>/reviews/",
    ReviewListCreateView.as_view(),
    name="menu-item-reviews",
),
]