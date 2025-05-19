Foodgram — API и веб-приложение для рецептов

Клонируйте репозиторий и перейдите в директорию проекта:

git clone https://github.com/RussianBear0/foodgram-st

Создние и активация виртуального окружения:

python -m venv venv
source venv/bin/activate  # Для Windows: venv\Scripts\activate
Установка зависимостей

python -m pip install --upgrade pip
pip install -r requirements.txt
Применение миграций

Если БАЗАДАННЫХ - PostgreSQL:
В корневой директории создать файл ".env"
DB_HOST=localhost
DB_PORT=5432
POSTGRES_USER=django_user
POSTGRES_PASSWORD=mysecretpassword
POSTGRES_DB=django

Создать в БД пользователя:
sudo -u postgres psql -c "CREATE USER django_user WITH PASSWORD 'mysecretpassword';"
sudo -u postgres psql -c "CREATE DATABASE django OWNER django_user;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE django TO django_user;"

Перезапустить PostgreSQL:
sudo systemctl restart postgresql

Запустить:(Если БД SQLite пропустить предыдущй пункт)

python manage.py migrate
Запуск сервера

python manage.py runserver
Проект  доступен по адресу: http://127.0.0.1:8000/.

API
После запуска проекта документация API доступна по адресу: http://localhost/api/docs/.

Основные эндпоинты:

Регистрация и аутентификация: /api/users/, /api/auth/token/login/.
Рецепты: /api/recipes/, /api/recipes/{id}/favorite/.
Подписки: /api/users/subscriptions/, /api/users/{id}/subscribe/.
Список покупок: /api/recipes/download_shopping_cart/.
Настройка GitHub Actions
Проект использует GitHub Actions для автоматического деплоя. Workflow находится в .github/workflows/main.yml.

Необходимые секреты

DOCKER_USERNAME — имя пользователя DockerHub

DOCKER_PASSWORD — пароль или токен DockerHub

TELEGRAM_TO — ID чата Telegram для уведомлений

TELEGRAM_TOKEN — токен Telegram-бота
