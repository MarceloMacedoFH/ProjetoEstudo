from django.urls import path
from . import views

urlpatterns = [
    path('funcionarios/', views.lista_funcionarios, name='lista_funcionarios'),
    path('funcionarios/criar/', views.criar_funcionario, name='criar_funcionario'),
    path('funcionarios/editar/<int:pk>/', views.editar_funcionario, name='editar_funcionario'),
    path('funcionarios/excluir/<int:pk>/', views.excluir_funcionario, name='excluir_funcionario'),
]