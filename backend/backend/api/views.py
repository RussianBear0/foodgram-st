from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponse
from django.db.models import Count, Sum
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import status, viewsets, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.urls import reverse
from rest_framework.decorators import action
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
                          AvatarSerializer,
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

    def create(self, request, *args, **kwargs):
        return Response({"detail": "Метод не разрешен."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def update(self, request, *args, **kwargs):
        return Response({"detail": "Метод не разрешен."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def partial_update(self, request, *args, **kwargs):
        return Response({"detail": "Метод не разрешен."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def destroy(self, request, *args, **kwargs):
        return Response({"detail": "Метод не разрешен."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


class RecipeViewSet(viewsets.ModelViewSet):
    serializer_class = RecipeGETSerializer
    queryset = Recipe.objects.all()
    permission_classes = (IsAuthorOrReadOnly,)
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter)
    filterset_fields = ['author']
    pagination_class = Pagination
    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return RecipePOSTSerializer
        return RecipeGETSerializer
    def perform_create(self, serializer):
        recipe = serializer.save(author=self.request.user)
        return Response(RecipeGETSerializer(recipe).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def add_to_shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        obj, created = ShoppingCart.objects.get_or_create(user=request.user, recipe=recipe)
        if not created:
            return Response(
                {'detail': 'Рецепт уже в корзине'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = RecipePOSTSerializer(recipe, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['delete'], permission_classes=[IsAuthenticated])
    def remove_from_shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        deleted, _ = ShoppingCart.objects.filter(user=request.user, recipe=recipe).delete()
        if not deleted:
            return Response(
                {'detail': 'Рецепт не найден в корзине'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        user_cart = ShoppingCart.objects.filter(user=request.user)
        recipe_ids = [item.recipe.id for item in user_cart]
        ingredients = IngredientRecipes.objects.filter(
            recipe_id__in=recipe_ids
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(
            total=Sum('amount')
        ).order_by('ingredient__name')
        file_content = "Ваша корзина\n\n"
        if not ingredients.exists():
            file_content += "Корзина пуста.\n"
        for item in ingredients:
            file_content += (
                f"• {item['ingredient__name']}: "
                f"{item['total']} {item['ingredient__measurement_unit']}\n"
            )
        response = HttpResponse(
            file_content,
            content_type='text/plain; charset=utf-8'
        )
        response['Content-Disposition'] = 'attachment; filename="shopping_list.txt"'
        return response

class SubscriptionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Subscription.objects.filter(user=self.request.user)


@api_view(['POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def using_favorites(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk)
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
    recipe = recipe = get_object_or_404(Recipe, pk=pk)
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
        serializer = AvatarSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    else:
        if user.avatar:
            user.avatar.delete(save=True)  # Удаляем файл аватара
            user.avatar = None  # Удаляем ссылку на аватар в модели
            user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({'detail': 'Аватар не установлен.'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_users(request):
    users = User.objects.all()  
    paginator = Pagination() 
    page = paginator.paginate_queryset(users, request)
    serializer = CustomUserSerializer(page, many=True, context={'request': request})

    return paginator.get_paginated_response(serializer.data)


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
