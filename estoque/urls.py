from django.urls import path
from .views import lista_estoque, lista_categoria, criar_categoria, editar_categoria, excluir_categoria




urlpatterns = [
    path('estoque/', lista_estoque, name='lista_estoque'),
    path('categorias/', lista_categoria, name='lista_categorias'),
    path('categorias/criar', criar_categoria, name='criar_categorias'),
    path('categorias/editar/<int:pk>/', editar_categoria, name='editar_categorias'),
    path('categorias/excluir/<int:pk>/', excluir_categoria, name='excluir_categoria'),
]
