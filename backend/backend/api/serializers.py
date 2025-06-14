from django.contrib.auth import get_user_model
from rest_framework import serializers
from django.core.files.base import ContentFile
import base64
from recipes.models import (Ingredient,
                            Recipe,
                            Follow,
                            Tag,
                            IngredientRecipes)
from rest_framework.validators import UniqueTogetherValidator
from django.db import IntegrityError

User = get_user_model()


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class CustomUserSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(required=True)
    is_subscribed= serializers.SerializerMethodField(method_name='get_is_subscribed')

    class Meta:
        model = User
        fields = ('id',
                  'email',
                  'password',
                  'username',
                  'first_name',
                  'last_name',
                  'avatar',
                  'is_subscribed')
    
    def validate_email(self, value):
        if len(value) > 254:
            raise serializers.ValidationError("Максимальная длина email 254 символа.")
        return value

    def create(self, validated_data):
        try:
            user = User.objects.create_user(**validated_data)
            return user
        except IntegrityError:
            raise serializers.ValidationError(
                {"detail": "Пользователь с таким email или именем уже существует."}
            )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        user = request.user if request is not None else None
        return (user is not None and user.is_authenticated
                and Follow.objects.filter(
                    user=user, following=obj).exists())



class AvatarSerializer(serializers.ModelSerializer):

    avatar = Base64ImageField(required=True)

    class Meta:
        model = User
        fields = ('avatar',)

    def to_representation(self, instance):
        return {
            'avatar': instance.avatar.url
            if instance.avatar else None
        }


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ('id', 'name',)


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measure')


class SubscriptionSerializer(CustomUserSerializer):
    recipes = serializers.SerializerMethodField(method_name='get_recipes')
    recipes_count = serializers.IntegerField(read_only=True)
    id = serializers.ReadOnlyField(source='author.id')
    username = serializers.ReadOnlyField(source='author.username')

    class Meta(CustomUserSerializer.Meta):
        fields = ('id','username', 'recipes', 'recipes_count')

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.query_params.get('recipes_limit') if request else None
        queryset = obj.author.recipes.all()  # Use obj.author instead of obj
        if limit:
            queryset = queryset[:int(limit)]
        return SmallRecipeSerializer(queryset, many=True).data


class SmallRecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(source='ingredient.measure')

    class Meta:
        model = IngredientRecipes
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeGETSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientSerializer(
        many=True,
        source='ingredients.all'
    )
    tags = TagSerializer(many=True)
    author = CustomUserSerializer()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'name', 'tags', 'author', 'short_code',
            'ingredients', 'is_favorited', 'is_in_shopping_cart',
            'image', 'text', 'cooking_time'
        )

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.favorite_recipes.filter(user=request.user).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.Shopping_cart.filter(user=request.user).exists()
        return False

    def get_image(self, obj):
        return obj.image.url if obj.image else None


class RecipeIngredientWriteSerializer(serializers.Serializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient'
    )
    amount = serializers.IntegerField(min_value=1)
    class Meta:
        model = IngredientRecipes
        fields = ('id', 'amount')


class RecipePOSTSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientWriteSerializer(
        many=True,
        write_only=True,
        required=True
    )
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        write_only=True,
        required=True
    )
    image = Base64ImageField(required=True)
    author = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id', 'name', 'tags', 'ingredients', 'short_code',
            'image', 'cooking_time', 'text', 'author'
        )
        extra_kwargs = {
            'text': {'required': True},
            'cooking_time': {'required': True}
        }

    def validate(self, data):
        if not data.get('tags'):
            raise serializers.ValidationError(
                {"tags": "Необходимо указать хотя бы один тег"}
            )
        if not data.get('ingredients'):
            raise serializers.ValidationError(
                {"ingredients": "Необходимо указать хотя бы один ингредиент"}
            )
        ingredient_ids = [item['ingredient'].id for item in data['ingredients']]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                {"ingredients": "Ингредиенты не должны повторяться"}
            )
        return data

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        validated_data['author'] = self.context['request'].user
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        for ingredient_item in ingredients_data:
            IngredientRecipes.objects.create(
                recipe=recipe,
                ingredient=ingredient_item['ingredient'],
                amount=ingredient_item['amount']
            )

        return recipe

    def to_representation(self, instance):
        request = self.context.get('request')
        context = {'request': request}
        return RecipeGETSerializer(instance, context=context).data

    def update(self, instance, validated_data):
        if 'tags' in validated_data:
            instance.tags.set(validated_data.pop('tags'))
        if 'ingredients' in validated_data:
            ingredients_data = validated_data.pop('ingredients')
            IngredientRecipes.objects.filter(recipe=instance).delete()
            for ingredient_item in ingredients_data:
                IngredientRecipes.objects.create(
                    recipe=instance,
                    ingredient=ingredient_item['ingredient'],
                    amount=ingredient_item['amount']
                )
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class FollowSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True,
        default=serializers.CurrentUserDefault()
    )
    following = serializers.SlugRelatedField(
        slug_field='id',
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
