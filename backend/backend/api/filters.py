from django_filters.rest_framework import (AllValuesMultipleFilter,
                                           BooleanFilter, CharFilter,
                                           FilterSet)

from recipes.models import Ingredient, Recipe


class RecipeFilter(FilterSet):

    tags = AllValuesMultipleFilter(field_name='tags__slug')
    is_favorited = BooleanFilter(field_name='is_favorited', method='filter_is_favorited')
    is_in_shopping_cart = BooleanFilter(field_name='is_in_shopping_cart', method='filter_is_in_shopping_cart')

    class Meta:
        model = Recipe
        fields = [
            'tags',
            'author',
            'is_favorited',
            'is_in_shopping_cart',
        ]

    def filter_queryset(self, queryset):
        if not self.request.user.is_authenticated:
            self.form.cleaned_data.pop('is_favorited', None)
            self.form.cleaned_data.pop('is_in_shopping_cart', None)

        return super().filter_queryset(queryset)

    def filter_is_favorited(self, queryset, name, value):
        if value:
            return queryset.filter(favorite_recipes__user=self.request.user).distinct()
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if value:
            return queryset.filter(shopping_cart__user=self.request.user).distinct()
        return queryset


class IngredientFilter(FilterSet):

    name = CharFilter(
        field_name='name',
        lookup_expr='istartswith',
        help_text='Название ингредиента (по начальным буквам)',
    )

    class Meta:
        model = Ingredient
        fields = ['name']
