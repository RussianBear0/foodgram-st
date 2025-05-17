from django.urls import include, path
from rest_framework import routers
from .views import (
    TagViewSet,
    IngredientViewSet,
    RecipeViewSet,
    FollowViewSet,
    add_to_favorites,
    remove_from_favorites,
    add_to_shopping_cart,
    remove_from_shopping_cart,
    download_shopping_cart,
    user_profile,
    update_avatar,
    delete_avatar,
    user_followers,
    follow
)

router = routers.DefaultRouter()
router.register('tags', TagViewSet, basename='tags')
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('recipes', RecipeViewSet, basename='recipes')

urlpatterns = [
    
    path('', include(router.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
    path('recipes/<int:pk>/favorite/', add_to_favorites, name='add-to-favorites'),
    path('recipes/<int:pk>/favorite/remove/', remove_from_favorites, name='remove-from-favorites'),
    path('recipes/<int:pk>/shopping_cart/', add_to_shopping_cart, name='add-to-shopping-cart'),
    path('recipes/<int:pk>/shopping_cart/remove/', remove_from_shopping_cart, name='remove-from-shopping-cart'),
    path('recipes/download_shopping_cart/', download_shopping_cart, name='download-shopping-cart'),
    path('users/me/', user_profile, name='user-profile'),
    path('users/me/avatar/', update_avatar, name='update-avatar'),
    path('users/me/avatar/delete/', delete_avatar, name='delete-avatar'),
    path('users/subscriptions/', user_followers, name='user-subscriptions'),
    path('users/<int:user_id>/subscribe/', follow, name='subscribe-user'),
]