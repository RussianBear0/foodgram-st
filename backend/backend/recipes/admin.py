from django.contrib import admin
from django.db.models import Count
from .models import (User,
                     Ingredient,
                     Recipe,
                     RecipeIngredient,
                     ShoppingCart,
                     Favorite,
                     Follow)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name')
    search_fields = ('username', 'email')
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    fields = (
        'username', 'email', 'first_name', 'last_name', 
        'avatar', 'is_active', 'is_staff', 'is_superuser',
        'groups', 'user_permissions', 'last_login', 'date_joined'
    )
    readonly_fields = ('last_login', 'date_joined')


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('measurement_unit',)


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1
    min_num = 1
    autocomplete_fields = ('ingredient',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'favorite_count')
    search_fields = ('name', 'author__username')
    list_filter = ('cooking_time',)
    autocomplete_fields = ('author', 'ingredients')
    readonly_fields = ('favorite_count', 'short_code')
    inlines = (RecipeIngredientInline,)


    def get_queryset(self, request):
        return super().get_queryset(request).annotate(_favorite_count=Count('favorites'))


    def favorite_count(self, obj):
        return obj._favorite_count
    favorite_count.short_description = 'Добавлений в избранное'
    favorite_count.admin_order_field = '_favorite_count'

@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'ingredient', 'amount')
    autocomplete_fields = ('recipe', 'ingredient')

@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    autocomplete_fields = ('user', 'recipe')

@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    autocomplete_fields = ('user', 'recipe')

@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('follower', 'following')
    autocomplete_fields = ('follower', 'following')
