from django.urls import path

from . import views

urlpatterns = [
    path('locacoes/', views.lista_locacoes, name='lista_locacoes'),
    path('locacoes/criar/', views.criar_locacao, name='criar_locacao'),
    path('locacoes/editar/<int:pk>/', views.editar_locacao, name='editar_locacao'),
    path('locacoes/cancelar/<int:pk>/', views.cancelar_locacao, name='cancelar_locacao'),
    path('locacoes/<int:pk>/marcar-prova/', views.marcar_prova_agendada, name='marcar_prova_agendada'),
    path('locacoes/<int:pk>/marcar-retirada/', views.marcar_retirada, name='marcar_retirada'),
    path('locacoes/item/<int:item_pk>/devolver/', views.marcar_devolvido_item, name='marcar_devolvido_item'),
    path('locacoes/ajax/disponibilidade/', views.verificar_disponibilidade, name='verificar_disponibilidade'),
    path('locacoes/consulta-disponibilidade/', views.consulta_disponibilidade, name='consulta_disponibilidade'),
]