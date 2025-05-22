from django.urls import include, path
from rest_framework import routers
from .views import (
    TagViewSet,
    IngredientViewSet,
    RecipeViewSet,
    SubscriptionViewSet,
    using_favorites,
    using_shopping_cart,
    download_shopping_cart,
    user_profile,
    using_avatar,
    follow,
    get_link,
    redirect_short_link
)

router = routers.DefaultRouter()
router.register('tags', TagViewSet, basename='tags')
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('recipes', RecipeViewSet, basename='recipes')
router.register(r'users/subscriptions', SubscriptionViewSet, basename='subscriptions')

urlpatterns = [

    path('', include(router.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),

    path('recipes/<int:pk>/favorite/', using_favorites, name='using_favorites'),
    path('recipes/<int:pk>/shopping_cart/', using_shopping_cart, name='ausing_shopping_cart'),
    path('recipes/download_shopping_cart/', download_shopping_cart, name='download_shopping_cart'),
    path('r/<str:short_code>/', redirect_short_link, name='redirect_short_link'),
    path('recipes/<int:pk>/get-link/', get_link, name='get-recipe-link'),

    path('users/me/', user_profile, name='user-profile'),
    path('users/me/avatar/', using_avatar, name='using_avatar'),

    path('users/<int:user_id>/subscribe/', follow, name='subscribe-user'),
]