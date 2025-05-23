from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponse
from django.db.models import Count, Sum
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.urls import reverse

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
    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return RecipePOSTSerializer
        return RecipeGETSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class SubscriptionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Subscription.objects.filter(user=self.request.user)


@api_view(['POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def using_favorites(request, pk):
    recipe = Recipe.objects.get(pk=pk)
    if request.method == 'POST':
        obj, created = Favorite.objects.get_or_create(user=request.user, recipe=recipe)
        if not created:
            return Response(
                {'detail': 'Рецепт уже сохранён.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = RecipePOSTSerializer(recipe, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    else:
        deleted, _ = Favorite.objects.filter(user=request.user, recipe=recipe).delete()
        if not deleted:
         return Response(
                {'detail': 'Рецепт удалён'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=204)


@api_view(['POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def using_shopping_cart(request, pk):
    recipe = Recipe.objects.get(pk=pk)
    if request.method == 'POST':
        obj, created = ShoppingCart.objects.get_or_create(user=request.user, recipe=recipe)
        if not created:
            return Response(
                {'detail': 'Рецепт уже в корзине'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = RecipePOSTSerializer(recipe, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    else:
        deleted, _ = ShoppingCart.objects.filter(user=request.user, recipe=recipe).delete()
        if not deleted:
            return Response(
                {'detail': 'Рецепт удалён'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=204)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_link(request, pk=None):
    recipe = get_object_or_404(Recipe, pk=pk)
    short_url = request.build_absolute_uri(
        reverse(
            'redirect_short_link',
            kwargs={'short_code': recipe.short_code},
        )
    )
    return Response(
        {'short-link': short_url},
        status=status.HTTP_200_OK,
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def redirect_short_link(request, short_code):
    recipe = get_object_or_404(Recipe, short_code=short_code)
    return redirect(recipe.get_absolute_url())


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def download_shopping_cart(request):
    user_cart = ShoppingCart.objects.filter(user=request.user)
    if not user_cart.exists():
        return HttpResponse(
            "Ваша корзина пуста",
            content_type='text/plain; charset=utf-8',
            status=200
        )
    recipe_ids = user_cart.values_list('recipe_id', flat=True)
    ingredients = IngredientRecipes.objects.filter(
        recipe_id__in=recipe_ids
    ).values(
        'ingredient__name',
        'ingredient__measure'
    ).annotate(
        total=Sum('amount')
    ).order_by('ingredient__name')

    file_content = "Ваша корзина\n\n"
    for item in ingredients:
        file_content += (
            f"• {item['ingredient__name']}: "
            f"{item['total']} {item['ingredient__measure']}\n"
        )
    response = HttpResponse(
        file_content,
        content_type='text/plain; charset=utf-8'
    )
    response['Content-Disposition'] = 'attachment; filename="shopping_list.txt"'
    return response(status=status.HTTP_200_OK)


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


@api_view(['PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def using_avatar(request):
    user = request.user
    if request.method == 'PUT':
        serializer = CustomUserSerializer(user, data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    else:
        if not user.avatar:
            return Response(
                {'detail': 'Аватар не установлен.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user.avatar.delete(save=True)
        return Response(status=204)


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
