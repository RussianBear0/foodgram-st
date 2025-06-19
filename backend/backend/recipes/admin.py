from django.contrib import admin
from .models import (
    User, 
    Subscription, 
    Tag, 
    Ingredient, 
    Recipe, 
    IngredientRecipes,
    ShoppingCart,
    Favorite,
    Follow
)

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'email', 'username', 'first_name', 'last_name', 'is_subscribed')
    search_fields = ('username', 'email')
    list_filter = ('is_subscribed',)
    fields = (
        'email', 'username', 'first_name', 'last_name', 
        'is_subscribed', 'avatar', 'password'
    )

@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'author', 'cooking_time', 'favorites_count')
    search_fields = ('name', 'author__username')
    list_filter = ('tags', 'author')
    filter_horizontal = ('tags',)
    readonly_fields = ('favorites_count',)
    
    def favorites_count(self, obj):
        return obj.favorite_recipes.count()
    favorites_count.short_description = 'Добавлений в избранное'

@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('measurement_unit',)

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug')
    search_fields = ('name', 'slug')

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'author', 'created_at')
    search_fields = ('user__username', 'author__username')
    list_filter = ('created_at',)

@admin.register(IngredientRecipes)
class IngredientRecipesAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipe', 'ingredient', 'amount')
    search_fields = ('recipe__name', 'ingredient__name')

@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe')
    search_fields = ('user__username', 'recipe__name')

@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe')
    search_fields = ('user__username', 'recipe__name')

@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'following')
    search_fields = ('user__username', 'following__username')
