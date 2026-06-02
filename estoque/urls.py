from django.urls import path
from .views import lista_estoque, lista_categoria


urlpatterns = [
    path('', lista_estoque, name='lista_estoque'),
    path('categorias/', lista_categoria, name='lista_categorias'),
]
