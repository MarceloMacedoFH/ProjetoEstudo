from django.shortcuts import render, redirect
from .models import Categoria
from .forms import CategoriaForm


def criar_categoria(request):
    if request.method == 'POST':
        form = CategoriaForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_categorias')
    else:
        form = CategoriaForm()
    
    context = {
        'form': form
    }   
    
    return render(request, 'estoque/categoria/criar_categoria.html', context)



def lista_categoria(request):
    # Buscamos apenas as categorias PAI (principais)
    # prefetch_related carrega todas as subcategorias de uma vez, evitando lentidão
    categorias_pais = Categoria.objects.filter(categoria_pai__isnull=True).prefetch_related('subcategorias')

    context = {
        'categorias_pais': categorias_pais
    }

    return render(request, 'estoque/categoria/lista_categoria.html', context)


def lista_estoque(request):

    return render(request, 'estoque/produto/lista_produto.html')