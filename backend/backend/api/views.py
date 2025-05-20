from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.db.models import Count, Sum
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from recipes.models import (Ingredient,
                            Recipe,
                            Tag,
                            IngredientRecipes,
                            Favorite,
                            ShoppingCart,
                            Subscription)
from .serializers import (TagSerializer,
                          IngredientSerializer,
                          FollowSerializer,
                          RecipePOSTSerializer,
                          CustomUserSerializer,
                          RecipeGETSerializer,
                          SubscriptionSerializer)
from .pagination import Pagination
from .permissions import IsAuthorOrReadOnly
from .filters import IngredientFilter
from django.contrib.auth import get_user_model


User = get_user_model()


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend]
    filterset_class = IngredientFilter


class RecipeViewSet(viewsets.ModelViewSet):
    serializer_class = RecipeGETSerializer
    queryset = Recipe.objects.all()
    permission_classes = (IsAuthorOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    pagination_class = Pagination


class SubscriptionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Subscription.objects.filter(user=self.request.user)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_to_favorites(request, pk):
    recipe = Recipe.objects.get(pk=pk)
    obj, created = Favorite.objects.get_or_create(user=request.user, recipe=recipe)
    if not created:
        return Response(
            {'detail': 'Рецепт уже сохранён.'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    serializer = RecipePOSTSerializer(recipe, context={'request': request})
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_to_shopping_cart(request, pk):
    recipe = Recipe.objects.get(pk=pk)
    obj, created = ShoppingCart.objects.get_or_create(user=request.user, recipe=recipe)
    if not created:
        return Response(
            {'detail': 'Рецепт уже в корзине'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    serializer = RecipePOSTSerializer(recipe, context={'request': request})
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def remove_from_favorites(request, pk):
    recipe = Recipe.objects.get(pk=pk)
    deleted, _ = Favorite.objects.filter(user=request.user, recipe=recipe).delete()
    if not deleted:
        return Response(
            {'detail': 'Рецепт удалён'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    return Response(status=204)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def remove_from_shopping_cart(request, pk):
    recipe = Recipe.objects.get(pk=pk)
    deleted, _ = ShoppingCart.objects.filter(user=request.user, recipe=recipe).delete()
    if not deleted:
        return Response(
            {'detail': 'Рецепт удалён'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    return Response(status=204)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_avatar(request):
    user = request.user
    if not user.avatar:
        return Response(
            {'detail': 'Аватар не установлен.'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    User.avatar.delete(save=True)
    return Response(status=204)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def download_shopping_cart(request):
    shopping_cart = ShoppingCart.objects.filter(user=request.user)
    recipes = [item.recipe.id for item in shopping_cart]
    buy_list = IngredientRecipes.objects.filter(recipe__in=recipes).values('ingredient').annotate(amount=Sum('amount'))
    basket = 'Корзина\n'
    for item in buy_list:
        ingredient = Ingredient.objects.get(pk=item['ingredient'])
        amount = item['amount']
        basket += (
            f'{ingredient.name}, {amount} '
            f'{ingredient.measure}\n'
        )
    response = HttpResponse(basket, content_type="text/plain")
    response['Content-Disposition'] = (
        'attachment; filename=Корзина.txt'
    )
    return Response(status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    serializer = CustomUserSerializer(request.user, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_followers(request):
    queryset = User.objects.filter(followers__user=request.user).annotate(recipes_count=Count('recipes'))
    paginator = Pagination()
    page = paginator.paginate_queryset(queryset, request)
    serializer = FollowSerializer(page, many=True, context={'request': request})
    return paginator.get_paginated_response(serializer.data)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def avatar(request):
    user = request.user
    serializer = CustomUserSerializer(user, data=request.data, context={'request': request})
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def follow(request, user_id):
    user = request.user
    author = get_object_or_404(User, id=user_id)
    if author == user:
        return Response(
            {'detail': 'Нельзя подписаться на себя.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    follow, created = Subscription.objects.get_or_create(
            user=user,
            author=author,
        )
    if not created:
        return Response(
            {'detail': 'Вы уже подписаны на этого пользователя.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    serializer = FollowSerializer(
        data={'following': author.id},
        context={'request': request}
    )
    serializer.is_valid(raise_exception=True)
    serializer.save(user=request.user)
    return Response(serializer.data, status=status.HTTP_201_CREATED)
