import shortuuid
from django.contrib.auth.models import AbstractUser
from django.core.validators import (
    MaxValueValidator,
    MinValueValidator,
)
from django.db import models

from .constants import (
    USER_EMAIL_MAX_LENGTH,
    INGREDIENT_NAME_MAX_LENGTH,
    INGREDIENT_MEASUREMENT_UNIT_MAX_LENGTH,
    RECIPE_NAME_MAX_LENGTH,
    RECIPE_SHORT_CODE_MAX_LENGTH,
    RECIPE_COOKING_TIME_MIN,
    RECIPE_COOKING_TIME_MAX,
    INGREDIENT_AMOUNT_MIN,
    INGREDIENT_AMOUNT_MAX,
)


class User(AbstractUser):
    avatar = models.ImageField(
        upload_to='users/avatars/',
        blank=True,
        null=True,
        verbose_name='Аватар',
    )

    email = models.EmailField(
        max_length=USER_EMAIL_MAX_LENGTH,
        unique=True,
        verbose_name="Email"
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return self.username

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"


class Ingredient(models.Model):

    name = models.CharField(max_length=INGREDIENT_NAME_MAX_LENGTH,
                            verbose_name="Название")
    measurement_unit = models.CharField(max_length=INGREDIENT_MEASUREMENT_UNIT_MAX_LENGTH,
                                        verbose_name="Единица измерения")

    class Meta:
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_ingredient_name_unit'
            )
        ]

    def __str__(self):
        return self.name


class Recipe(models.Model):

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор',
    )
    name = models.CharField(
        max_length=RECIPE_NAME_MAX_LENGTH,
        verbose_name='Название',
    )

    image = models.ImageField(
        upload_to='recipes/images/',
        verbose_name='Картинка',
    )

    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        verbose_name='Ингредиенты',
    )

    short_code = models.CharField(
        max_length=RECIPE_SHORT_CODE_MAX_LENGTH,
        unique=True,
        default=shortuuid.ShortUUID().uuid,
        verbose_name='Короткий код',
    )

    text = models.TextField(verbose_name='Описание')

    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления (мин)',
        validators=[
            MinValueValidator(RECIPE_COOKING_TIME_MIN, message=("Готовить не меньше минуты")),
            MaxValueValidator(RECIPE_COOKING_TIME_MAX, message=("Готовить больше 480 минут")),
        ],
    )

    class Meta:
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"
        ordering = ["-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["author", "name"], name="unique_recipe_author_name"
            )
        ]

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент',
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество',
        validators=[
            MinValueValidator(INGREDIENT_AMOUNT_MIN, message=("Не меньше 1")),
            MaxValueValidator(INGREDIENT_AMOUNT_MAX, message=("Не более 1000")),
        ],
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецепте'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_recipe_ingredient_pair'
            )
        ]

    def __str__(self):
        return f'Количество {self.ingredient} в {self.recipe} составляет {self.amount}'


class ShoppingCart(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="shopping_carts",
        verbose_name='Пользователь'
    )

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="shopping_carts",
        verbose_name="Рецепт в корзине"
    )

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_user_recipe_shoppingcart'
            )
        ]

    def __str__(self):
        return f'У {self.user} Корзина {self.recipe}'


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="favorites",
        verbose_name="Пользователь",
    )
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, verbose_name="Рецепт")

    class Meta:
        verbose_name = "Избранное"
        verbose_name_plural = "Избранное"
        constraints = [
            models.UniqueConstraint(fields=["user", "recipe"], name="unique_favorite")
        ]
        ordering = ["-id"]

    def __str__(self):
        return f"{self.user} добавил {self.recipe} в избранное"


class Follow(models.Model):
    follower = models.ForeignKey(
        User,
        related_name="following",
        on_delete=models.CASCADE,
        verbose_name="Подписчик",
    )
    following = models.ForeignKey(
        User, related_name="followers", on_delete=models.CASCADE, verbose_name="Автор"
    )

    class Meta:
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
        ordering = ["follower"]
        constraints = [
            models.UniqueConstraint(
                fields=["follower", "following"], name="unique_follow"
            ),
            models.CheckConstraint(
                check=~models.Q(follower=models.F("following")),
                name="prevent_self_follow",
            ),
        ]

    def __str__(self):
        return f"{self.follower} follows {self.following}"

    def is_following(self, user1, user2):
        return Follow.objects.filter(follower=user1, following=user2).exists()