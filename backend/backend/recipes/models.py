import shortuuid
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db.models import F, Q
from django.urls import reverse


class User(AbstractUser):
    avatar = models.ImageField(
        upload_to='users/avatars/',
        blank=True,
        null=True,
        verbose_name='Аватар',
    )

    username = models.CharField(
        max_length=150,
        unique=True,
        verbose_name='Имя пользователя'
    )

    email = models.EmailField(
        max_length=254,
        unique=True,
        verbose_name="Email"
    )

    is_subscribed = models.BooleanField(
        'Подписка',
        default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    class Meta:
        verbose_name = 'Пользователь'

    def __str__(self):
        return self.email


class Subscription(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'author')
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        return f'{self.user} подписан на {self.author}'


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

    name = models.CharField(max_length=200,
                            verbose_name="Название")
    measurement_unit = models.CharField(max_length=20,
                                        verbose_name="Единица измерения")

    class Meta:
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"
        ordering = ["name"]

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
        max_length=256,
        verbose_name='Название',
    )

    recipe_ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientRecipes',
        related_name='used_in_recipes',
        verbose_name='Ингредиенты',
    )

    short_code = models.CharField(
        max_length=22,
        unique=True,
        default=shortuuid.ShortUUID().uuid,
        verbose_name='Короткий код',
    )

    image = models.ImageField(
        upload_to='recipes/images/',
        verbose_name='Картинка',
    )

    text = models.TextField(verbose_name='Описание')

    cooking_time = models.PositiveSmallIntegerField(
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

    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Теги',
    )

    class Meta:
        ordering = ['-pub_date', 'author', 'name']
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return f'Рецепт {self.name} от {self.pub_date}. Автор {self.author}'

    def is_favorited_by(self, user):
        return self.favorite_recipes.filter(user=user).exists()

    def is_in_shopping_cart_of(self, user):
        return self.shopping_cart.filter(user=user).exists()

    def get_absolute_url(self):
        return reverse('recipe-detail', kwargs={'pk': self.pk})



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
    amount = models.PositiveSmallIntegerField(
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
        User,
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
        User,
        on_delete=models.CASCADE,
        related_name="shopping_cart",
        verbose_name='Пользователь'
    )

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="shopping_cart",
        verbose_name="Рецепт в корзине"
    )

    class Meta(UserRecipe.Meta):
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'

    def __str__(self):
        return f'У {self.user} Корзина {self.recipe}'


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
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
        User,
        on_delete=models.CASCADE,
        related_name='follows_as_user')
    following = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follows_as_following')

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
