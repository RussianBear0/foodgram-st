from django.contrib import admin

from .models import  User, Ingredient, Recipe, IngredientRecipes, UserRecipe, Follow

class RecipeInline(admin.StackedInline):
    model = Post
    extra = 0


class GroupAdmin(admin.ModelAdmin):
    inlines = (
        RecipeInline,
    )


class RecipeAdmin (admin.ModelAdmin):
    model = Recipe
    list_display = ('author',
                    'name',
                    'recipe_ingredients',
                    "short_code",
                    "text",
                    "pub_date",
                    )
    search_fields = ('name',)
    list_filter = ('pub_date',)


class IngredientAdmin (admin.ModelAdmin):
    model = Ingredient
    list_display = ('name',
                    'measure',
                    )
    list_editable = ("name",)
    search_fields = ('name',)
    list_filter = ('name',)


class FollowAdmin (admin.ModelAdmin):
    model = Follow
    list_display = ('user',
                    'following',
                    )
    list_editable = ("following",)
    search_fields = ('user',)

admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Follow, FollowAdmin)
admin.site.register(User) 
admin.site.register(IngredientRecipes)
admin.site.register(UserRecipe) 
