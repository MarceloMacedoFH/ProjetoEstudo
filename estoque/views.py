from django.shortcuts import render
from .models import Categoria


# Create your views here.
def lista_categoria(request):
    # Buscamos apenas as categorias PAI (principais)
    # prefetch_related carrega todas as subcategorias de uma vez, evitando lentidão
    categorias_pais = Categoria.objects.filter(categoria_pai__isnull=True).prefetch_related('subcategorias')

    context = {
        'categorias_pais': categorias_pais
    }

    return render(request, 'estoque/categoria/lista.html', context)


def lista_estoque(request):

    return render(request, 'estoque/produto/lista.html')