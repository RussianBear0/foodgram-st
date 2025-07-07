from django.contrib.auth import update_session_auth_hash
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import status, viewsets, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView

from recipes.models import (User,
                            Ingredient,
                            Recipe,
                            RecipeIngredient,
                            ShoppingCart,
                            Favorite,
                            Follow)
from .filters import IngredientFilter
from .pagination import Pagination
from .permissions import IsAuthorOrReadOnly
from .serializers import (UserSerializer,
                          AvatarSerializer,
                          IngredientSerializer,
                          SmallRecipeSerializer,
                          RecipeIngredientSerializer,
                          RecipeSerializer,
                          FollowSerializer)


class CustomUserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    pagination_class = Pagination
    serializer_class = UserSerializer

    @action(
        detail=False, methods=["get"], permission_classes=[IsAuthenticated]
    )
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(
        detail=True, methods=["post"], permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, pk=None):
        user = request.user
        author = get_object_or_404(User, pk=pk)
        if user == author:
            return Response(
                {"detail": "Нельзя подписаться на себя"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if user.following.filter(following=author).exists():
            return Response(
                {"detail": "Уже подписан"}, status=status.HTTP_400_BAD_REQUEST
            )
        follow = Follow.objects.create(follower=user, following=author)
        serializer = FollowSerializer(follow, context={"request": request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def unsubscribe(self, request, pk=None):
        user = request.user
        author = get_object_or_404(User, pk=pk)
        follow = user.following.filter(following=author).first()
        if not follow:
            return Response(
                {"detail": "Вы не подписаны"}, status=status.HTTP_400_BAD_REQUEST
            )
        follow.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False, methods=["get"], permission_classes=[IsAuthenticated]
    )
    def subscriptions(self, request):
        user = request.user
        follows = user.following.all()
        paginator = Pagination()
        result_page = paginator.paginate_queryset(follows, request)
        serializer = FollowSerializer(
            result_page, many=True, context={"request": request}
        )
        return paginator.get_paginated_response(serializer.data)

    @action(
        detail=False,
        methods=["put", "delete"],
        url_path="me/avatar",
        permission_classes=[IsAuthenticated],
    )
    def update_avatar(self, request):
        user = request.user
        if request.method == "PUT":
            serializer = AvatarSerializer(user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        elif request.method == "DELETE":
            if not user.avatar:
                return Response(
                    {"detail": "Аватар не установлен"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            user.avatar.delete()
            user.avatar = None
            user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False, methods=["post"], permission_classes=[IsAuthenticated]
    )
    def set_password(self, request):
        user = request.user
        current_password = request.data.get("current_password")
        new_password = request.data.get("new_password")

        if not current_password or not new_password:
            return Response(
                {"detail": "Необходимо указать current_password и new_password."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not user.check_password(current_password):
            return Response(
                {"detail": "Неверный текущий пароль."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(new_password)
        user.save()
        update_session_auth_hash(request, user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def create(self, request, *args, **kwargs):

        serializer = self.get_serializer(data=request.data, context={
            'request': request,
            'is_user_creation': True
        })
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


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
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ["name", "author__username"]
    pagination_class = Pagination

    def get_queryset(self):
        queryset = self.queryset.all()
        user = self.request.user
        author_id = self.request.query_params.get("author", None)
        is_favorited = self.request.query_params.get("is_favorited", None)
        is_in_shopping_cart = self.request.query_params.get("is_in_shopping_cart", None)

        if author_id:
            queryset = queryset.filter(author_id=author_id)

        if not user.is_authenticated and (
            is_favorited == "1" or is_in_shopping_cart == "1"
        ):
            return queryset.none()

        if user.is_authenticated:
            if is_favorited == "1":
                favorite_ids = user.favorites.values_list('recipe_id', flat=True)
                queryset = queryset.filter(id__in=favorite_ids)
            if is_in_shopping_cart == "1":
                cart_ids = user.shopping_carts.values_list('recipe_id', flat=True)
                queryset = queryset.filter(id__in=cart_ids)

        return queryset

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        detail=True,
        methods=["post", "delete"],
        permission_classes=[IsAuthenticated],
    )
    def favorite(self, request, pk=None):
        recipe = self.get_object()
        user = request.user
        if request.method == "POST":
            if user.favorites.filter(recipe=recipe).exists():
                return Response(
                    {"detail": "Уже в избранном"}, status=status.HTTP_400_BAD_REQUEST
                )
            Favorite.objects.create(user=user, recipe=recipe)
            serializer = SmallRecipeSerializer(recipe, context={"request": request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        elif request.method == "DELETE":
            favorite = user.favorites.filter(recipe=recipe).first()
            if favorite:
                favorite.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(
                {"detail": "Не в избранном"}, status=status.HTTP_400_BAD_REQUEST
            )

    @action(
        detail=True,
        methods=["post", "delete"],
        permission_classes=[IsAuthenticated],
    )
    def shopping_cart(self, request, pk=None):
        recipe = self.get_object()
        user = request.user

        if request.method == "POST":
            if user.shopping_carts.filter(recipe=recipe).exists():
                return Response(
                    {"detail": "Рецепт уже в корзине"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            ShoppingCart.objects.create(user=user, recipe=recipe)
            serializer = SmallRecipeSerializer(recipe, context={"request": request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == "DELETE":
            shopping_cart = user.shopping_carts.filter(recipe=recipe).first()
            if shopping_cart:
                shopping_cart.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(
                {"detail": "Рецепт не в корзине"}, status=status.HTTP_400_BAD_REQUEST
            )

    @action(
        detail=False, methods=["get"], permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        user = request.user
        shopping_cart = user.shopping_carts.all()
        recipes = [item.recipe for item in shopping_cart]
        ingredients = (
            RecipeIngredient.objects.filter(recipe__in=recipes)
            .values("ingredient__name", "ingredient__measurement_unit")
            .annotate(total_amount=Sum("amount"))
        )

        content = "Список покупок\n"
        for ingredient in ingredients:
            content += f"{ingredient['ingredient__name']} ({ingredient['ingredient__measurement_unit']}) — {ingredient['total_amount']}\n"
        return HttpResponse(
            content,
            content_type="text/plain",
            headers={"Content-Disposition": 'attachment; filename="shopping_list.txt"'},
        )

    @action(detail=True, methods=["get"], url_path="get-link")
    def get_short_link(self, request, pk=None):
        recipe = self.get_object()
        short_link = request.build_absolute_uri(
            reverse("short-link", args=[recipe.short_code])
        )
        return Response({"short-link": short_link})


class ShoppingCartIngredientsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        shopping_cart = user.shopping_carts.all()
        recipes = [item.recipe for item in shopping_cart]
        ingredients = RecipeIngredient.objects.filter(recipe__in=recipes)
        serializer = RecipeIngredientSerializer(ingredients, many=True)
        return Response(serializer.data)


def redirect_short_link(request, slug):
    recipe = get_object_or_404(Recipe, short_code=slug)
    url = reverse("recipes-detail", args=[recipe.id])
    return redirect(url)
