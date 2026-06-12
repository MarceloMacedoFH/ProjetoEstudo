from django.urls import path
from .views import (
    criar_conservacao, lista_produto, criar_produto, editar_produto, 
    excluir_produto, lista_categoria, criar_categoria, 
    editar_categoria, excluir_categoria, lista_status, criar_status, 
    editar_status, excluir_status, lista_conservacao, lista_cor,
    criar_cor, editar_cor, excluir_cor, editar_conservacao,
    excluir_conservacao
)



urlpatterns = [
    #produto 
    path('produto/', lista_produto, name='lista_produto'),
    path('produto/criar/', criar_produto, name='criar_produto'),
    path('produto/editar/<int:pk>/', editar_produto, name='editar_produto'),
    path('produto/excluir/<int:pk>/', excluir_produto, name='excluir_produto'),

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

    #Conservação
    path('conservacao/', lista_conservacao, name='lista_conservacao'),
    path('conservacao/criar/', criar_conservacao, name='criar_conservacao'),
    path('conservacao/editar/<int:pk>/', editar_conservacao, name='editar_conservacao'),
    path('conservacao/excluir/<int:pk>/', excluir_conservacao, name='excluir_conservacao'),

    #Cor
    path('cor/', lista_cor, name='lista_cor'),
    path('cor/criar/', criar_cor, name='criar_cor'),
    path('cor/editar/<int:pk>/', editar_cor, name='editar_cor'),
    path('cor/excluir/<int:pk>/', excluir_cor, name='excluir_cor'),
]
