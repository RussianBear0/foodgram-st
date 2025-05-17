from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db.models import F, Q



class CustomUser(AbstractUser):
    avatar = models.ImageField(
        upload_to='users/avatars/',
        blank=True,
        null=True,
        verbose_name='Аватар',
    )

    email = models.EmailField(
        max_length=254,
        unique=True,
        verbose_name="Email"
    )

    class Meta:
        verbose_name = 'Пользователь'

    def __str__(self):
        return self.username


class Tag(models.Model):

    name = models.CharField(
        max_length=256,
        unique=True,
        verbose_name='Тег',
    )
    slug = models.SlugField(unique=True,
                            max_length=128,
                            )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):

    name = models.CharField(
        max_length=128,
        verbose_name='Ингредиент',
    )
    measure = models.CharField(
        max_length=128,
        verbose_name='Единица измерения',
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.measure})'


class Recipe(models.Model):

    author = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор',
    )
    name = models.CharField(
        max_length=256,
        verbose_name='Название',
    )

    image = models.ImageField(
        upload_to='recipes/images/',
        verbose_name='Картинка',
    )

    text = models.TextField(verbose_name='Описание')

    cooking_time = models.DecimalField(
        verbose_name='Время приготовления (мин)',
        validators=[
            MinValueValidator(1, message=("Готовить не меньше минуты")),
            MaxValueValidator(480, message=("Готовить больше 480 минут")),
        ],
    )

    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата добавления',
    )

    class Meta:
        ordering = ['-pub_date', 'author', 'name']
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return f'Рецепт {self.name} от {self.pub_date}. Автор {self.author}'


class IngredientRecipes(models.Model):

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='ingredients',
        verbose_name='Рецепт',
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name='Ингредиент',
    )
    amount = models.DecimalField(
        verbose_name='Количество',
        validators=[
            MinValueValidator(0.1, message=("Не меньше 0.1")),
            MaxValueValidator(1000, message=("Не более 1000")),
        ],
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецепте'

    def __str__(self):
        return f'Количество {self.ingredient} в {self.recipe} составляет {self.amount}'


class UserRecipe(models.Model):

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='User_recipe',
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='User_recipe',
        verbose_name='Рецепт',
    )

    class Meta:
        abstract = True
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_%(class)s',
            )
        ]


class ShoppingCart(models.Model):

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="Shopping_cart",
        verbose_name='Пользователь'
    )

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="Shopping_cart",
        verbose_name="Рецепт в корзине"
    )

    class Meta(UserRecipe.Meta):
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'

    def __str__(self):
        return f'У {self.user} Корзина {self.recipe}'


class Favorite(models.Model):
    user = models.ForeignKey(
        CustomUser,
        related_name='favorites',
        on_delete=models.CASCADE,
        verbose_name='Пользователь')

    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Рецепты',
        on_delete=models.CASCADE,
        related_name='favorite_recipes')

    class Meta:
        ordering = ('user', )
        verbose_name = 'Сохранённое'
        verbose_name_plural = 'Сохранённое'

    def __str__(self):
        return f'{self.user.username} - {self.recipe.name}'


class Follow(models.Model):
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='follower')
    following = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='following')

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'following'],
                name='unique_follow'),
            models.CheckConstraint(
                check=~Q(user=F('following')),
                name='user_not_following')
        ]

    def __str__(self):
        return f'Подписки: {self.following.username}'
