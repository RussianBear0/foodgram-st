## О проекте
Foodgram — это веб-приложение, в котором пользователи могут публиковать рецепты, добавлять рецепты в избранное, список покупок, а также подписываться на других пользователей. Проект позволяет формировать список покупок на основе добавленных рецептов и выгружать его

## Технологии

* Python
* Django 
* PostgreSQL
* Nginx
* Docker / Docker Compose
* GitHub 

## Запуск проекта
### 1. Клонировать репозиторий

git clone https://github.com/RussianBear0/foodgram-st


### 2. Создать файл окружения

    DEBUG=False

    SECRET_KEY=django_secret_key
    ALLOWED_HOSTS=localhost,127.0.0.1
    POSTGRES_USER=django_user
    POSTGRES_PASSWORD=mysecretpassword
    POSTGRES_DB=django
    DB_HOST=db
    DB_PORT=5432

### 3. Запуск проекта
cd infra
docker compose up --build -d

### 4. Выполнить миграции и создать суперпользователя, загрузить ингридиенты в базу
docker compose exec backend python manage.py makemigrations
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py createsuperuser
docker compose exec backend python manage.py load_ingredients

### 5. Собрать статику
docker compose exec backend python manage.py collectstatic --no-input

Проект  доступен по адресу: http://127.0.0.1:8000/.
Админ зона проекта доступна по адресу : http://127.0.0.1:8000/admin/

## API
После запуска проекта документация API доступна по адресу: http://localhost/api/docs/.

## Основные эндпоинты:

Регистрация и аутентификация: /api/users/, /api/auth/token/login/.
Рецепты: /api/recipes/, /api/recipes/{id}/favorite/.
Подписки: /api/users/subscriptions/, /api/users/{id}/subscribe/.
Список покупок: /api/recipes/download_shopping_cart/.
Настройка GitHub Actions
Проект использует GitHub Actions для автоматического деплоя. Workflow находится в .github/workflows/main.yml.

## Секреты
Необходимые секреты

DOCKER_USERNAME — имя пользователя DockerHub

DOCKER_PASSWORD — пароль или токен DockerHub

TELEGRAM_TO — ID чата Telegram для уведомлений

TELEGRAM_TOKEN — токен Telegram-бота


### 6. Остановить отладку
ОСТАНОВИТЬ ПРОЕКТ =  docker-compose down
Отчистить БД =  docker volume rm $(docker volume ls -q)
