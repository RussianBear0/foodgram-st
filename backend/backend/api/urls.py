from django.urls import include, path
from rest_framework import routers
from .views import (
    TagViewSet,
    IngredientViewSet,
    RecipeViewSet,
    SubscriptionViewSet,
    using_favorites,
    get_users,
    using_shopping_cart,
    user_profile,
    using_avatar,
    set_password,
    follow,
    get_user_by_id,
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
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),

    path('recipes/<int:pk>/favorite/', using_favorites, name='using_favorites'),
    path('recipes/<int:pk>/shopping_cart/', using_shopping_cart, name='using_shopping_cart'),
    path('r/<str:short_code>/', redirect_short_link, name='redirect_short_link'),
    path('recipes/<int:pk>/get-link/', get_link, name='get-recipe-link'),

    path('users/me/', user_profile, name='user-profile'),
    path('users/<int:user_id>/', get_user_by_id, name='user-detail'),
    path('users/set_password/', set_password, name='set_password'),
    path('users/', get_users, name='get_users'),
    path('users/me/avatar/', using_avatar, name='using_avatar'),

    path('users/<int:user_id>/subscribe/', follow, name='subscribe-user'),

]
