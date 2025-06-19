from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponse
from django.db.models import Count, Sum
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import status, viewsets, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly
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
                          SmallRecipeSerializer,
                          RecipePOSTSerializer,
                          CustomUserSerializer,
                          RecipeGETSerializer,
                          SubscriptionSerializer)
from .pagination import Pagination
from .permissions import IsAuthorOrReadOnly
from .filters import IngredientFilter
from django.contrib.auth import get_user_model
from djoser.views import UserViewSet
from .serializers import CustomSetPasswordSerializer
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
import io


User = get_user_model()


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class CustomUserViewSet(UserViewSet):
    def get_serializer_class(self):
        if self.action == "set_password":
            return CustomSetPasswordSerializer
        return super().get_serializer_class()


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
    permission_classes = (IsAuthorOrReadOnly, IsAuthenticatedOrReadOnly)
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter)
    filterset_fields = ['author']
    pagination_class = Pagination

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return RecipePOSTSerializer
        return RecipeGETSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_queryset(self):
        queryset = super().get_queryset()
        request = self.request

        if request.query_params.get('is_favorited') == '1':
            if request.user.is_authenticated:
                queryset = queryset.filter(favorite_recipes__user=request.user).distinct()
            else:
                queryset = queryset.none()

        if request.query_params.get('is_in_shopping_cart') == '1':
            if request.user.is_authenticated:
                queryset = queryset.filter(shopping_cart__user=request.user).distinct()
            else:
                queryset = queryset.none()

        return queryset

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def add_to_shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        obj, created = ShoppingCart.objects.get_or_create(user=request.user, recipe=recipe)
        if not created:
            return Response(
                {'detail': 'Рецепт уже в корзине'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = SmallRecipeSerializer(recipe)
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

        file_format = request.GET.get('format', 'txt').lower()
        if file_format == 'pdf':
            buffer = io.BytesIO()

            try:
                pdfmetrics.registerFont(TTFont('DejaVuSerif', 'DejaVuSerif.ttf'))
            except:
                font_name = 'Helvetica'
            else:
                font_name = 'DejaVuSerif'

            p = canvas.Canvas(buffer, pagesize=A4)
            width, height = A4

            p.setFont(font_name, 16)
            p.drawString(2*cm, height - 2*cm, "Ваша корзина покупок")

            if not ingredients:
                p.setFont(font_name, 12)
                p.drawString(2*cm, height - 4*cm, "Корзина пуста.")
            else:
                data = [['Ингредиент', 'Количество', 'Ед. измерения']]
                for item in ingredients:
                    data.append([
                        item['ingredient__name'],
                        str(item['total']),
                        item['ingredient__measurement_unit']
                    ])

                table = Table(data, repeatRows=1)
                table.setStyle(TableStyle([
                    ('FONT', (0,0), (-1,-1), font_name, 10),
                    ('FONTSIZE', (0,0), (-1,0), 12),
                    ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
                    ('GRID', (0,0), (-1,-1), 1, colors.black),
                    ('ALIGN', (1,1), (1,-1), 'RIGHT'),
                ]))    
                table.wrapOn(p, width - 4*cm, height)
                table.drawOn(p, 2*cm, height - 4*cm - len(data)*0.6*cm)

            p.showPage()
            p.save()

            buffer.seek(0)
            response = HttpResponse(buffer, content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="shopping_list.pdf"'
            return response

        file_content = "Ваша корзина покупок\n\n"
        if not ingredients:
            file_content += "Корзина пуста.\n"
        else:
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
    pagination_class = Pagination

    def get_queryset(self):
        return User.objects.filter(
            following__user=self.request.user
        ).annotate(recipes_count=Count('recipes'))

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        recipes_limit = request.query_params.get('recipes_limit')
        context = self.get_serializer_context()
        context['recipes_limit'] = recipes_limit

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True, context=context)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True, context=context)
        return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def set_password(request):
    serializer = CustomSetPasswordSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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
        serializer = SmallRecipeSerializer(recipe, context={'request': request})
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
    recipe = get_object_or_404(Recipe, pk=pk)
    if request.method == 'POST':
        obj, created = ShoppingCart.objects.get_or_create(user=request.user, recipe=recipe)
        if not created:
            return Response(
                {'detail': 'Рецепт уже в корзине'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = SmallRecipeSerializer(recipe, context={'request': request})
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
@permission_classes([AllowAny])
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
    if not request.user.is_authenticated:
        return Response({'detail': 'Учетные данные не были предоставлены.'}, status=status.HTTP_401_UNAUTHORIZED)
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
            user.avatar.delete(save=True)
            user.avatar = None
            user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({'detail': 'Аватар не установлен.'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_user_by_id(request, user_id):
    user = get_object_or_404(User, id=user_id)
    serializer = CustomUserSerializer(user, context={'request': request})
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST', 'GET'])
@permission_classes([AllowAny])
def get_users(request):

    if request.method == 'POST':
        serializer = CustomUserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                'id': user.id,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    else:
        users = User.objects.all()
        paginator = Pagination()
        page = paginator.paginate_queryset(users, request)
        serializer = CustomUserSerializer(page, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)


@api_view(['POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def follow(request, user_id):
    user = request.user
    author = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        if author == user:
            return Response(
                {'detail': 'Нельзя подписаться на себя.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if Subscription.objects.filter(user=user, author=author).exists():
            return Response(
                {'detail': 'Вы уже подписаны на этого пользователя.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        Subscription.objects.create(user=user, author=author)
        author = User.objects.annotate(recipes_count=Count('recipes')).get(id=author.id)

        serializer = SubscriptionSerializer(author, context={
            'request': request,
            'recipes_limit': request.query_params.get('recipes_limit')
        })
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    else:
        subscription = Subscription.objects.filter(user=user, author=author).first()
        if not subscription:
            return Response(
                {'detail': 'Вы не подписаны на этого пользователя.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
