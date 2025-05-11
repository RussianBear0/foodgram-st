FROM python:3.9

WORKDIR /app

RUN pip install gunicorn==20.1.0

COPY requirements.txt .
RUN pip install -r requirements.txt --no-cache-dir

COPY . .
COPY data/ingredients.csv /app/data/ingredients.csv

RUN mkdir -p /app/static /app/media

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "foodgram.wsgi"]