from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import F, Q
from django.db.models.functions import Coalesce
from .models import Categoria, Status, Conservacao, Cor, Produto
from .forms import CategoriaForm, StatusForm, ConservacaoForm, CorForm, ProdutoForm

#HOME
def home(request):
    # Por enquanto retornamos valores fictícios até que as tabelas de 
    # agendamentos e locações sejam criadas no models.py
    context = {
        'total_provas': 0,
        'total_retiradas': 0,
        'total_devolucoes': 0,
        'total_atrasos': 0,
        'total_alugados': 0,
    }
    return render(request, 'home.html', context)



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
    return render(request, 'estoque/categoria/editar_categoria.html', context)

def excluir_categoria(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    if request.method == 'POST':
        categoria.delete()
        return redirect('lista_categorias')
    return render(request, 'estoque/categoria/confirmar_exclusao.html', {'categoria': categoria})

def lista_categoria(request):
    query = request.GET.get('q')
    categorias = Categoria.objects.annotate(
        sort_group=Coalesce('categoria_pai_id', 'id')
    ).order_by(
        'sort_group', 
        F('categoria_pai_id').asc(nulls_first=True), 
        'descricao'
    ).select_related('categoria_pai')

    if query:
        categorias = categorias.filter(
            Q(descricao__icontains=query) | 
            Q(categoria_pai__descricao__icontains=query) | 
            Q(subcategorias__descricao__icontains=query)
        ).distinct()

    context = {
        'categorias': categorias,
        'query': query,
    }
    return render(request, 'estoque/categoria/lista_categoria.html', context)



#Metodos Produtos 
def lista_produto(request):
    query = request.GET.get('q')
    produtos = Produto.objects.all().select_related(
        'categoria', 'status', 'cor_principal', 'conservacao'
    )

    if query:
        produtos = produtos.filter(
            Q(descricao__icontains=query) |
            Q(codigo__icontains=query) |
            Q(categoria__descricao__icontains=query)
        ).distinct()

    context = {
        'produtos': produtos,
        'query': query,
    }
    return render(request, 'estoque/produto/lista_produto.html', context)

def criar_produto(request):
    if request.method == 'POST':
        form = ProdutoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_produto')
    else:
        form = ProdutoForm()
    
    return render(request, 'estoque/produto/criar_produto.html', {'form': form})

def editar_produto(request, pk):
    produto = get_object_or_404(Produto, pk=pk)
    if request.method == 'POST':
        form = ProdutoForm(request.POST, instance=produto)
        if form.is_valid():
            form.save()
            return redirect('lista_produto')
    else:
        form = ProdutoForm(instance=produto)
    
    context = {
        'form': form,
        'is_edit': True,
        'produto': produto
    }
    return render(request, 'estoque/produto/editar_produto.html', context)

def excluir_produto(request, pk):
    produto = get_object_or_404(Produto, pk=pk)
    if request.method == 'POST':
        produto.delete()
        return redirect('lista_produto')
    
    return render(request, 'estoque/produto/confirmar_exclusao.html', {'produto': produto})



#Metodos Status
def lista_status(request):
    query = request.GET.get('q')
    status = Status.objects.all()
    
    if query:
        status = status.filter(descricao__icontains=query)
    
    context = {
        'status': status,
        'query': query,
    }

    return render(request, 'estoque/status/lista_status.html', context)
    
def criar_status(request):

    if request.method == 'POST':
        form = StatusForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_status')
    else:
        form = StatusForm()
    
    context = {
        'form': form
    }   
    
    return render(request, 'estoque/status/criar_status.html', context)

def editar_status(request, pk):
    status = get_object_or_404(Status, pk=pk)
    if request.method == 'POST':
        form = StatusForm(request.POST, instance=status)
        if form.is_valid():
            form.save()
            return redirect('lista_status')
    else:
        form = StatusForm(instance=status)
    
    context = {
        'form': form,
        'is_edit': True,
    }

    return render(request, 'estoque/status/editar_status.html', context)

def excluir_status(request, pk):
    status = get_object_or_404(Status, pk=pk)

    if request.method == 'POST':
        status.delete()
        return redirect('lista_status')

    return render(request, 'estoque/status/confirmar_exclusao.html', {'status': status})



#Conservação 
def lista_conservacao(request):
    query = request.GET.get('q')
    conservacao = Conservacao.objects.all()

    if query:
        conservacao = conservacao.filter(descricao__icontains=query)

    context = {
        'conservacao': conservacao,
        'query': query,
    }

    return render(request, 'estoque/conservacao/lista_conservacao.html', context)

def criar_conservacao(request):
    if request.method == 'POST':
        form = ConservacaoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_conservacao')
    
    form = ConservacaoForm()
    return render(request, 'estoque/conservacao/criar_conservacao.html', {'form': form})

def editar_conservacao(request, pk):
    conservacao = get_object_or_404(Conservacao, pk=pk)
    if request.method == 'POST':
        form = ConservacaoForm(request.POST, instance=conservacao)
        if form.is_valid():
            form.save()
            return redirect('lista_conservacao')
    else:
        form = ConservacaoForm(instance=conservacao)
    
    context = {
        'form': form,
        'is_edit': True,
    }
    return render(request, 'estoque/conservacao/editar_conservacao.html', context)

def excluir_conservacao(request, pk):
    conservacao = get_object_or_404(Conservacao, pk=pk)
    if request.method == 'POST':
        conservacao.delete()
        return redirect('lista_conservacao')
    
    return render(request, 'estoque/conservacao/confirmar_exclusao.html', {'conservacao': conservacao})



#Cor
def lista_cor(request):
    query = request.GET.get('q')
    cores = Cor.objects.all().order_by('descricao')

    if query:
        cores = cores.filter(descricao__icontains=query)

    context = {
        'cores': cores,
        'query': query,
    }
    return render(request, 'estoque/cor/lista_cor.html', context)

def criar_cor(request):
    if request.method == 'POST':
        form = CorForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_cor')
    else:
        form = CorForm()
    return render(request, 'estoque/cor/criar_cor.html', {'form': form})

def editar_cor(request, pk):
    cor = get_object_or_404(Cor, pk=pk)
    if request.method == 'POST':
        form = CorForm(request.POST, instance=cor)
        if form.is_valid():
            form.save()
            return redirect('lista_cor')
    else:
        form = CorForm(instance=cor)
    
    context = {
        'form': form,
        'is_edit': True,
    }
    return render(request, 'estoque/cor/editar_cor.html', context)

def excluir_cor(request, pk):
    cor = get_object_or_404(Cor, pk=pk)
    if request.method == 'POST':
        cor.delete()
        return redirect('lista_cor')
    return render(request, 'estoque/cor/confirmar_exclusao.html', {'cor': cor})