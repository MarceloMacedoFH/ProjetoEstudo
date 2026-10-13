from django.urls import path
from . import views

urlpatterns = [
    #Cargos
    path("cargos/", views.lista_cargos , name="lista_cargos"),
    path('cargos/criar/', views.criar_cargo, name='criar_cargo'),
    path('cargos/editar/<int:pk>/', views.editar_cargo, name='editar_cargo'),
    path('cargos/excluir/<int:pk>/', views.excluir_cargo, name='excluir_cargo'),
    
    #Funcionarios
    path('funcionarios/', views.lista_funcionarios, name='lista_funcionarios'),
    path('funcionarios/criar/', views.criar_funcionario, name='criar_funcionario'),
    path('funcionarios/editar/<int:pk>/', views.editar_funcionario, name='editar_funcionario'),
    path('funcionarios/excluir/<int:pk>/', views.excluir_funcionario, name='excluir_funcionario'),

]