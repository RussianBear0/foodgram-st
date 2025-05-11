from django.urls import path

from recipes.views import link

urlpatterns = [
    path(
        's/<str:short_code>/',
        link,
        name='link',
    ),
]