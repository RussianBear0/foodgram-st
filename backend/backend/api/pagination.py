from rest_framework.pagination import PageNumberPagination
from recipes.constants import BASIC_PAGE_SIZE

class Pagination(PageNumberPagination):
    page_size = BASIC_PAGE_SIZE
    page_size_query_param = 'limit'
