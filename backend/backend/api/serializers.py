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
import re
from djoser.serializers import SetPasswordSerializer

User = get_user_model()


class CustomSetPasswordSerializer(SetPasswordSerializer):
    class Meta:
        model = User
        fields = ('new_password', 'current_password')


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class CustomUserSerializer(serializers.ModelSerializer):

    avatar = Base64ImageField(required=False)
    is_subscribed = serializers.SerializerMethodField()
    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'avatar',
            'is_subscribed',
            'password',
        )
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def validate(self, data):
        if 'first_name' not in data or not data['first_name']:
            raise serializers.ValidationError({"first_name": "Поле 'first_name' обязательно для заполнения."})
        if 'last_name' not in data or not data['last_name']:
            raise serializers.ValidationError({"last_name": "Поле 'last_name' обязательно для заполнения."})
        return data

    def validate_email(self, value):
        if len(value) > 254:
            raise serializers.ValidationError("Максимальная длина email 254 символа.")
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Пользователь с таким email уже существует.")
        return value

    def validate_username(self, value):
        if len(value) > 150:
            raise serializers.ValidationError("Максимальная длина имени пользователя 150 символов.")
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Пользователь с таким именем уже существует.")
        if not re.match(r'^[\w.@+-]+$', value):
            raise serializers.ValidationError("Имя пользователя может содержать только буквы, цифры и символы: . @ + - _")
        return value

    def validate_first_name(self, value):
        if len(value) > 150:
            raise serializers.ValidationError("Максимальная длина имени 150 символов.")
        return value

    def validate_last_name(self, value):
        if len(value) > 150:
            raise serializers.ValidationError("Максимальная длина фамилии 150 символов.")
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        user = request.user if request is not None else None
        if user is None or not user.is_authenticated:
            return False
        return Follow.objects.filter(user=user, following=obj).exists()


class AvatarSerializer(serializers.ModelSerializer):

    avatar = Base64ImageField(required=True)

    class Meta:
        model = User
        fields = ('avatar',)

    def validate(self, data):
        if 'avatar' not in data:
            raise serializers.ValidationError({"avatar": "Поле 'avatar' обязательно для заполнения."})
        return data

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
        fields = ('id', 'name', 'measurement_unit')


class SubscriptionSerializer(CustomUserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name',
            'avatar', 'is_subscribed', 'recipes', 'recipes_count'
        )

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.query_params.get('recipes_limit', None)
        queryset = obj.recipes.all()
        if limit:
            queryset = queryset[:int(limit)]
        return SmallRecipeSerializer(queryset, many=True).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_is_subscribed(self, obj):
        return True

    def get_avatar(self, obj):
        if obj.avatar:
            return obj.avatar.url
        return None


class SmallRecipeSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')

    def get_image(self, obj):
        if obj.image:
            return obj.image.url
        return None


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(source='ingredient.measurement_unit')

    class Meta:
        model = IngredientRecipes
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeGETSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientSerializer(
        many=True,
        source='ingredients.all'
    )
    author = CustomUserSerializer()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'name', 'author',
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
            return obj.shopping_cart.filter(user=request.user).exists()
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


class RecipeResponseSerializer(serializers.ModelSerializer):
    author = CustomUserSerializer()
    ingredients = RecipeIngredientSerializer(many=True, source='ingredients.all')
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'name', 'author', 'ingredients', 
            'is_favorited', 'is_in_shopping_cart',
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
            return obj.shopping_cart.filter(user=request.user).exists()
        return False

    def get_image(self, obj):
        return obj.image.url if obj.image else None


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
        required=False 
    )
    image = Base64ImageField(required=True)
    author = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id', 'name', 'tags', 'ingredients',
            'image', 'cooking_time', 'text', 'author'
        )
        extra_kwargs = {
            'text': {'required': True},
            'cooking_time': {'required': True}
        }

    def validate(self, data):
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
        tags = validated_data.pop('tags', [])  
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
        return RecipeResponseSerializer(instance, context=context).data

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
