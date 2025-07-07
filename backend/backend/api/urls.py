from django.urls import path, include
from rest_framework.routers import DefaultRouter
from api.views import (
    CustomUserViewSet,
    RecipeViewSet,
    IngredientViewSet,
    ShoppingCartIngredientsView,
    redirect_short_link,
)

router = DefaultRouter()
router.register("users", CustomUserViewSet, basename="users")
router.register("ingredients", IngredientViewSet, basename="ingredients")
router.register("recipes", RecipeViewSet, basename="recipes")


urlpatterns = [

    path("", include(router.urls)),
    path("auth/", include("djoser.urls.authtoken")),

    path(
        "shopping_cart/ingredients/",
        ShoppingCartIngredientsView.as_view(),
        name="shopping_cart_ingredients",
    ),
    path("s/<str:slug>/", redirect_short_link, name="short-link"),
]
