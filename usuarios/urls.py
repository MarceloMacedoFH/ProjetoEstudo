from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views

urlpatterns = [
    path("login/", views.LoginUsuarioView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    
    # Gestão de Usuários
    path("usuarios/", views.lista_usuarios, name="lista_usuarios"),
    path("usuarios/novo/", views.criar_usuario, name="criar_usuario"),
    path("usuarios/<int:pk>/editar/", views.editar_usuario, name="editar_usuario"),
    path("usuarios/<int:pk>/excluir/", views.excluir_usuario, name="excluir_usuario"),
    
    # Gestão de Grupos / Perfis
    path("grupos/", views.lista_grupos, name="lista_grupos"),
    path("grupos/novo/", views.criar_grupo, name="criar_grupo"),
    path("grupos/<int:pk>/editar/", views.editar_grupo, name="editar_grupo"),
    path("grupos/<int:pk>/excluir/", views.excluir_grupo, name="excluir_grupo"),
]