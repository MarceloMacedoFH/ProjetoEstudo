from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import F
from django.db.models.functions import Coalesce
from .models import Categoria
from .forms import CategoriaForm


#Metodos Categorias
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


def editar_categoria(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    if request.method == 'POST':
        form = CategoriaForm(request.POST, instance=categoria)
        if form.is_valid():
            form.save()
            return redirect('lista_categorias')
    else:
        form = CategoriaForm(instance=categoria)
    
    context = {
        'form': form,
        'is_edit': True
    }
    return render(request, 'estoque/categoria/criar_categoria.html', context)


def lista_categoria(request):
    # Ordenação Hierárquica:
    # 1. Agrupamos as categorias pelo ID do pai (ou pelo próprio ID se for pai).
    # 2. Dentro do grupo, garantimos que o Pai (null) venha antes dos filhos.
    # 3. Ordenamos alfabeticamente entre irmãos.
    categorias = Categoria.objects.annotate(
        sort_group=Coalesce('categoria_pai_id', 'id')
    ).order_by(
        'sort_group', 
        F('categoria_pai_id').asc(nulls_first=True), 
        'descricao'
    ).select_related('categoria_pai')

    context = {
        'categorias': categorias
    }

    return render(request, 'estoque/categoria/lista_categoria.html', context)



#Metodos Produtos 
def lista_estoque(request):

    return render(request, 'estoque/produto/lista_produto.html')