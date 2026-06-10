from django.urls import path
from .views import lista_estoque, lista_categoria, criar_categoria, editar_categoria, excluir_categoria,lista_status, criar_status,editar_status,excluir_status




urlpatterns = [
    #Estoque 
    path('estoque/', lista_estoque, name='lista_estoque'),

    #Categorias
    path('categorias/', lista_categoria, name='lista_categorias'),
    path('categorias/criar', criar_categoria, name='criar_categorias'),
    path('categorias/editar/<int:pk>/', editar_categoria, name='editar_categorias'),
    path('categorias/excluir/<int:pk>/', excluir_categoria, name='excluir_categoria'),

    #Status
    path('status/', lista_status, name='lista_status'),
    path('status/criar/', criar_status, name='criar_status'),
    path('status/editar/<int:pk>/', editar_status, name='editar_status'),
    path('status/excluir/<int:pk>/', excluir_status, name='excluir_status'),

    
]
