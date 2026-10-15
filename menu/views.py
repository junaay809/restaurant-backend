from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Count, Q

from .models import Category, MenuItem, DiscoveryTag, Review
from .serializers import (
    CategorySerializer,
    MenuItemSerializer,
    ReviewSerializer,
)


# ============================================================
# CATEGORY LIST
# ============================================================

class CategoryListView(generics.ListAPIView):

    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):

        return Category.objects.filter(
            is_active=True
        ).prefetch_related("items")


# ============================================================
# CATEGORY DETAIL
# ============================================================

class CategoryDetailView(generics.RetrieveAPIView):

    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]

    queryset = Category.objects.filter(
        is_active=True
    ).prefetch_related("items")

    lookup_field = "slug"


# ============================================================
# MENU LIST
# ============================================================

class MenuItemListView(generics.ListAPIView):

    serializer_class = MenuItemSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):

        queryset = MenuItem.objects.filter(
            is_available=True,
            category__is_active=True
        ).select_related("category")

        category = self.request.query_params.get("category")

        if category:
            queryset = queryset.filter(
                category__slug=category
            )

        featured = self.request.query_params.get("featured")

        if featured == "true":
            queryset = queryset.filter(
                is_featured=True
            )

        popular = self.request.query_params.get("popular")

        if popular == "true":
            queryset = queryset.filter(
                is_popular=True
            )

        return queryset


# ============================================================
# MENU ITEM DETAIL
# ============================================================

class MenuItemDetailView(generics.RetrieveAPIView):

    serializer_class = MenuItemSerializer
    permission_classes = [permissions.AllowAny]

    queryset = MenuItem.objects.filter(
        is_available=True,
        category__is_active=True
    ).select_related("category")

    lookup_field = "slug"


# ============================================================
# DISCOVER RECOMMENDATIONS
# ============================================================

class DiscoverRecommendationView(generics.GenericAPIView):

    permission_classes = [permissions.AllowAny]
    serializer_class = MenuItemSerializer

    def post(self, request, *args, **kwargs):

        discovery_type = request.data.get("type")
        answer = request.data.get("answer")

        # ----------------------------------------------------
        # Validate the request
        # ----------------------------------------------------

        if not discovery_type:
            return Response(
                {
                    "error": "Discovery type is required."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        if not answer:
            return Response(
                {
                    "error": "Discovery answer is required."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # ----------------------------------------------------
        # Internal answer mappings
        #
        # The customer sees the normal question/answer.
        # They do NOT see these internal mappings.
        # ----------------------------------------------------

        answer_mappings = {

            # ---------------- MOOD ----------------

            "mood": {
                "happy": [
                    ("craving", "sweet"),
                    ("looks", "colourful"),
                ],

                "sad": [
                    ("experience", "comfort"),
                ],

                "excited": [
                    ("craving", "spicy"),
                    ("experience", "adventure"),
                ],

                "tired": [
                    ("experience", "comfort"),
                    ("hunger", "medium"),
                ],

                "relaxed": [
                    ("craving", "fresh"),
                    ("looks", "fresh"),
                ],
            },

            # ---------------- CRAVING ----------------

            "craving": {
                "sweet": [
                    ("craving", "sweet"),
                ],

                "salty": [
                    ("craving", "salty"),
                ],

                "savoury": [
                    ("craving", "savoury"),
                ],

                "spicy": [
                    ("craving", "spicy"),
                ],

                "fresh": [
                    ("craving", "fresh"),
                ],
            },

            # ---------------- LOOKS ----------------

            "looks": {
                "colourful": [
                    ("looks", "colourful"),
                ],

                "loaded": [
                    ("looks", "loaded"),
                ],

                "crispy": [
                    ("looks", "crispy"),
                ],

                "fresh": [
                    ("looks", "fresh"),
                ],

                "beautiful": [
                    ("looks", "beautiful"),
                ],
            },

            # ---------------- HUNGER ----------------

            "hunger": {
                "light": [
                    ("hunger", "light"),
                ],

                "medium": [
                    ("hunger", "medium"),
                ],

                "very_hungry": [
                    ("hunger", "very_hungry"),
                ],

                "starving": [
                    ("hunger", "starving"),
                ],
            },

            # ---------------- EXPERIENCE ----------------

            "experience": {
                "comfort": [
                    ("experience", "comfort"),
                ],

                "adventure": [
                    ("experience", "adventure"),
                ],

                "classic": [
                    ("experience", "classic"),
                ],

                "treat": [
                    ("experience", "treat"),
                ],

                "quick": [
                    ("experience", "quick"),
                ],
            },
        }

        # ----------------------------------------------------
        # Find the tags associated with this answer
        # ----------------------------------------------------

        mappings_for_type = answer_mappings.get(
            discovery_type,
            {}
        )

        target_tags = mappings_for_type.get(
            answer,
            []
        )

        if not target_tags:
            return Response(
                {
                    "error": "No discovery mapping found for this answer."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # ----------------------------------------------------
        # Find available menu items
        # ----------------------------------------------------

        menu_items = MenuItem.objects.filter(
            is_available=True,
            category__is_active=True,
            discovery_tags__isnull=False
        ).distinct().prefetch_related(
            "discovery_tags"
        ).select_related(
            "category"
        )

        # ----------------------------------------------------
        # Score each food
        #
        # A food gets one point for every matching tag.
        # This allows foods with multiple relevant tags
        # to appear higher in the results.
        # ----------------------------------------------------

        scored_items = []

        for item in menu_items:

            item_tags = set(
                item.discovery_tags.values_list(
                    "type",
                    "code"
                )
            )

            score = sum(
                1
                for target_tag in target_tags
                if target_tag in item_tags
            )

            if score > 0:
                scored_items.append(
                    (score, item)
                )

        # ----------------------------------------------------
        # Sort by highest match first
        # ----------------------------------------------------

        scored_items.sort(
            key=lambda item: (
                -item[0],
                -float(item[1].rating),
                item[1].display_order,
                item[1].name,
            )
        )

        # ----------------------------------------------------
        # Return the actual food items
        # ----------------------------------------------------

        recommended_items = [
            item
            for score, item in scored_items[:10]
        ]

        serializer = self.get_serializer(
            recommended_items,
            many=True
        )

        return Response(
            {
                "type": discovery_type,
                "answer": answer,
                "count": len(recommended_items),
                "results": serializer.data,
            },
            status=status.HTTP_200_OK
        )

# ============================================================
# DISCOVER RECOMMENDATION
# ============================================================

DISCOVERY_MAPPINGS = {

    "mood": {
        "happy": [("craving", "sweet")],
        "sad": [("experience", "comfort")],
        "excited": [
            ("craving", "spicy"),
            ("experience", "adventure"),
        ],
        "tired": [("experience", "comfort")],
        "relaxed": [("craving", "fresh")],
    },

    "craving": {
        "sweet": [("craving", "sweet")],
        "salty": [("craving", "salty")],
        "savoury": [("craving", "savoury")],
        "spicy": [("craving", "spicy")],
        "fresh": [("craving", "fresh")],
    },

    "looks": {
        "colourful": [("looks", "colourful")],
        "loaded": [("looks", "loaded")],
        "crispy": [("looks", "crispy")],
        "fresh": [("looks", "fresh")],
        "beautiful": [("looks", "beautiful")],
    },

    "hunger": {
        "light": [("hunger", "light")],
        "medium": [("hunger", "medium")],
        "very_hungry": [("hunger", "very_hungry")],
        "starving": [("hunger", "starving")],
    },

    "experience": {
        "comfort": [("experience", "comfort")],
        "adventure": [("experience", "adventure")],
        "classic": [("experience", "classic")],
        "treat": [("experience", "treat")],
        "quick": [("experience", "quick")],
    },
}


class DiscoverRecommendationView(APIView):

    permission_classes = [permissions.AllowAny]

    def get(self, request):

        category = request.query_params.get("category")
        answer = request.query_params.get("answer")

        if not category or not answer:
            return Response(
                {
                    "error": "Both category and answer are required."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        category_mapping = DISCOVERY_MAPPINGS.get(category)

        if not category_mapping:
            return Response(
                {
                    "error": "Invalid discovery category."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        target_pairs = category_mapping.get(answer)

        if not target_pairs:
            return Response(
                {
                    "error": "Invalid discovery answer."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        target_tags = DiscoveryTag.objects.filter(
            type__in=[pair[0] for pair in target_pairs],
            code__in=[pair[1] for pair in target_pairs],
        )

        items = (
            MenuItem.objects.filter(
                is_available=True,
                category__is_active=True,
                discovery_tags__in=target_tags,
            )
            .select_related("category")
            .annotate(
                match_count=Count(
                    "discovery_tags",
                    filter=Q(discovery_tags__in=target_tags),
                    distinct=True,
                )
            )
            .order_by(
                "-match_count",
                "-is_featured",
                "display_order",
                "name",
            )
            .distinct()
        )[:10]

        return Response(
            {
                "category": category,
                "answer": answer,
                "items": MenuItemSerializer(
                    items,
                    many=True,
                    context={"request": request},
                ).data,
            }
        )


# ============================================================
# CUSTOMER REVIEWS
# ============================================================

class ReviewListCreateView(generics.ListCreateAPIView):

    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        menu_item_id = self.kwargs["menu_item_id"]

        return Review.objects.filter(
            menu_item_id=menu_item_id
        ).select_related("user", "menu_item")

    def perform_create(self, serializer):
        menu_item_id = self.kwargs["menu_item_id"]

        menu_item = MenuItem.objects.get(
            id=menu_item_id,
            is_available=True,
            category__is_active=True
        )

        serializer.save(
            user=self.request.user,
            menu_item=menu_item
        )