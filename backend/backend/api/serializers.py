from django.contrib.auth import get_user_model
from rest_framework import serializers
from django.core.files.base import ContentFile
import base64
from recipes.models import (Ingredient,
                            Recipe,
                            Follow,
                            Tag,
                            Subscription)
from rest_framework.validators import UniqueTogetherValidator


User = get_user_model()


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class UserSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(required=False, allow_null=True)
    is_subscribe= serializers.SerializerMethodField(method_name='get_is_subscribe')

    class Meta:
        model = User
        fields = ('id',
                  'email',
                  'username',
                  'first_name',
                  'last_name',
                  'avatar')

    def get_is_subscribe(self, obj):
        request = self.context.get('request')
        user = request.user if request is not None else None
        return (user is not None and user.is_authenticated
                and Subscription.objects.filter(
                    user=user, author=obj).exists())


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measure')


class SubscriptionSerializer(UserSerializer):
    recipes = serializers.SerializerMethodField(method_name='get_recipes')
    recipes_count = serializers.IntegerField(read_only=True)

    class Meta(UserSerializer.Meta):
        fields = ('username', 'recipes')

    def get_recipes(self, obj):
        author_receipt= Recipe.objects.filter(author=obj)
        request = self.context.get('request')
        limit = (
            request.query_params.get('recipes_limit')
            if request else None
        )
        queryset = obj.recipes.all()
        if limit and author_receipt:
            queryset = queryset[:int(limit)]
        return SmallRecipeSerializer(queryset, many=True).data


class SmallRecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class RecipeGETSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    tags = TagSerializer(many=True)
    ingredients = serializers.IngredientSerializer(many=True, read_only=True)
    is_favorited = serializers.BooleanField(read_only=True, default=False)
    is_basket = serializers.BooleanField(read_only=True, default=False)

    class Meta:
        model = Recipe
        fields = ('id',
                  'name',
                  'author',
                  'tags',
                  'ingredients',
                  'is_favorited',
                  'is_basket',
                  'image',
                  'cooking_time')


class RecipePOSTSerializer(serializers.ModelSerializer):
    ingredients = IngredientSerializer(many=True,
                                       write_only=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        write_only=True,
        allow_empty=False,
        required=True,
    )
    image = Base64ImageField(required=True)

    class Meta:
        model = Recipe
        fields = ('id',
                  'name',
                  'author',
                  'tags',
                  'ingredients',
                  'is_favorited',
                  'is_basket',
                  'image',
                  'cooking_time')

    def validate(self, data):
        if 'ingredients' not in data:
            raise serializers.ValidationError({
                'ingredients': 'Не указаны ингредиенты.'})

        ingredients = data['ingredients']

        list_ingredients = set()
        for item in ingredients:
            ingredient_id = item['ingredient'].id
            if ingredient_id in list_ingredients:
                raise serializers.ValidationError({
                    'ingredients': 'Повторение ингредиентов'})
            list_ingredients.add(ingredient_id)

        return data

    def create(self, validated_data):
        return super().create(validated_data)

    def to_representation(self, instance):
        request = self.context.get('request')
        context = {'request': request}
        return RecipeGETSerializer(instance, context=context).data


class FollowSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True,
        default=serializers.CurrentUserDefault()
    )
    following = serializers.SlugRelatedField(
        slug_field='username',
        queryset=User.objects.all()
    )

    class Meta:
        fields = ('user', 'following')
        model = Follow
        validators = [
            UniqueTogetherValidator(
                queryset=Follow.objects.all(),
                fields=['user', 'following']
            )
        ]

    def validate(self, data):
        if self.context['request'].user == data.get('following'):
            return data
        raise serializers.ValidationError("Самоподписка запрещена")
