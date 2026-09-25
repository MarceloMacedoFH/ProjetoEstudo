from urllib.parse import urlencode

from django.db import IntegrityError
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import F, Q, ProtectedError
from django.db.models.functions import Coalesce
from django.contrib import messages
from django.urls import reverse
from .models import Categoria, Status, Conservacao, Cor, Produto, Tecido
from .forms import CategoriaForm, StatusForm, ConservacaoForm, CorForm, ProdutoForm, TecidoForm


def _url_lista(nome_url, query=None):
    """Monta a URL da lista, já com a busca codificada (acentos, espaços, &, etc.)."""
    url = reverse(nome_url)
    if query:
        url = f'{url}?{urlencode({"q": query})}'
    return url


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
            try:
                categoria = form.save()
            except IntegrityError:
                # Rede de segurança: o form já barra duplicados, mas isso cobre
                # o caso de dois cadastros simultâneos com o mesmo nome.
                form.add_error(None, 'Já existe uma categoria com este nome neste nível.')
            else:
                if categoria.categoria_pai:
                    return redirect(_url_lista('lista_categorias', categoria.categoria_pai.descricao))
                return redirect(_url_lista('lista_categorias', categoria.descricao))
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
            categoria = form.save()
            if categoria.categoria_pai:
                return redirect(_url_lista('lista_categorias', categoria.categoria_pai.descricao))
            return redirect(_url_lista('lista_categorias', categoria.descricao))
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
        try:
            categoria.delete()
        except ProtectedError:
            # O editar_categoria.html exibe as mensagens, então voltamos para ele.
            messages.error(
                request,
                f'Não é possível excluir a categoria "{categoria.descricao}" porque ela possui '
                f'subcategorias ou está em uso por produtos.'
            )
            return redirect('editar_categorias', pk=categoria.pk)
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
            try:
                produto = form.save()
            except IntegrityError:
                # Rede de segurança para cadastros simultâneos com o mesmo código.
                form.add_error('codigo', 'Já existe um produto cadastrado com este código.')
            else:
                return redirect(_url_lista('lista_produto', produto.codigo))
    else:
        form = ProdutoForm()
    
    return render(request, 'estoque/produto/criar_produto.html', {'form': form})

def editar_produto(request, pk):
    produto = get_object_or_404(Produto, pk=pk)
    if request.method == 'POST':
        form = ProdutoForm(request.POST, instance=produto)
        if form.is_valid():
            produto = form.save()
            return redirect(_url_lista('lista_produto', produto.codigo))
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
        try:
            produto.delete()
        except ProtectedError:
            # O editar_produto.html exibe as mensagens, então voltamos para ele.
            messages.error(
                request,
                f'Não é possível excluir o produto "{produto.codigo}" porque ele está vinculado '
                f'a outros registros. Inative o produto em vez de excluir.'
            )
            return redirect('editar_produto', pk=produto.pk)
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
            try:
                status = form.save()
            except IntegrityError:
                # Rede de segurança para cadastros simultâneos com a mesma descrição.
                form.add_error('descricao', 'Já existe um status cadastrado com esta descrição.')
            else:
                return redirect(_url_lista('lista_status', status.descricao))
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
            status = form.save()
            return redirect(_url_lista('lista_status', status.descricao))
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
        try:
            status.delete()
        except ProtectedError:
            # O editar_status.html exibe as mensagens, então voltamos para ele.
            messages.error(
                request,
                f'Não é possível excluir o status "{status.descricao}" porque ele está em uso '
                f'por produtos. Inative o status em vez de excluir.'
            )
            return redirect('editar_status', pk=status.pk)
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
            try:
                conser = form.save()
            except IntegrityError:
                # Rede de segurança para cadastros simultâneos com a mesma descrição.
                form.add_error('descricao', 'Já existe uma conservação cadastrada com esta descrição.')
            else:
                return redirect(_url_lista('lista_conservacao', conser.descricao))
    else:
        form = ConservacaoForm()
    return render(request, 'estoque/conservacao/criar_conservacao.html', {'form': form})

def editar_conservacao(request, pk):
    conservacao = get_object_or_404(Conservacao, pk=pk)
    if request.method == 'POST':
        form = ConservacaoForm(request.POST, instance=conservacao)
        if form.is_valid():
            conser = form.save()
            return redirect(_url_lista('lista_conservacao', conser.descricao))
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
        try:
            conservacao.delete()
        except ProtectedError:
            # O editar_conservacao.html exibe as mensagens, então voltamos para ele.
            messages.error(
                request,
                f'Não é possível excluir a conservação "{conservacao.descricao}" porque ela está '
                f'em uso por produtos. Inative a conservação em vez de excluir.'
            )
            return redirect('editar_conservacao', pk=conservacao.pk)
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
            try:
                cor = form.save()
            except IntegrityError:
                # Rede de segurança para cadastros simultâneos com o mesmo nome.
                form.add_error('descricao', 'Já existe uma cor cadastrada com este nome.')
            else:
                return redirect(_url_lista('lista_cor', cor.descricao))
    else:
        form = CorForm()
    return render(request, 'estoque/cor/criar_cor.html', {'form': form})

def editar_cor(request, pk):
    cor = get_object_or_404(Cor, pk=pk)
    if request.method == 'POST':
        form = CorForm(request.POST, instance=cor)
        if form.is_valid():
            cor = form.save()
            return redirect(_url_lista('lista_cor', cor.descricao))
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
        try:
            cor.delete()
        except ProtectedError:
            # O editar_cor.html exibe as mensagens, então voltamos para ele.
            messages.error(
                request,
                f'Não é possível excluir a cor "{cor.descricao}" porque ela está em uso '
                f'por produtos. Inative a cor em vez de excluir.'
            )
            return redirect('editar_cor', pk=cor.pk)
        return redirect('lista_cor')
    return render(request, 'estoque/cor/confirmar_exclusao.html', {'cor': cor})


#Metodos Tecido
def lista_tecido(request):
    query = request.GET.get('q')
    tecidos = Tecido.objects.all().order_by('descricao')
 
    if query:
        tecidos = tecidos.filter(descricao__icontains=query)
 
    context = {
        'tecidos': tecidos,
        'query': query,
    }
    return render(request, 'estoque/tecido/lista_tecido.html', context)
 
 
def criar_tecido(request):
    if request.method == 'POST':
        form = TecidoForm(request.POST)
        if form.is_valid():
            try:
                tecido = form.save()
            except IntegrityError:
                # Rede de segurança: o form já barra duplicados, mas isso cobre
                # o caso de dois cadastros simultâneos com o mesmo nome.
                form.add_error('descricao', 'Já existe um tecido cadastrado com este nome.')
            else:
                return redirect(_url_lista('lista_tecido', tecido.descricao))
    else:
        form = TecidoForm()
 
    context = {
        'form': form,
    }
    return render(request, 'estoque/tecido/criar_tecido.html', context)
 
 
def editar_tecido(request, pk):
    tecido = get_object_or_404(Tecido, pk=pk)
    if request.method == 'POST':
        form = TecidoForm(request.POST, instance=tecido)
        if form.is_valid():
            tecido = form.save()
            return redirect(_url_lista('lista_tecido', tecido.descricao))
    else:
        form = TecidoForm(instance=tecido)
 
    context = {
        'form': form,
        'tecido': tecido,
    }
    return render(request, 'estoque/tecido/editar_tecido.html', context)
 
 
def excluir_tecido(request, pk):
    tecido = get_object_or_404(Tecido, pk=pk)
    if request.method == 'POST':
        try:
            tecido.delete()
        except ProtectedError:
            # O editar_tecido.html já exibe as mensagens, então voltamos para ele.
            messages.error(
                request,
                f'Não é possível excluir o tecido "{tecido.descricao}" porque ele está em uso '
                f'por produtos. Inative o tecido em vez de excluir.'
            )
            return redirect('editar_tecido', pk=tecido.pk)
        return redirect('lista_tecido')
 
    context = {
        'tecido': tecido,
    }
    return render(request, 'estoque/tecido/confirmar_exclusao.html', context)