from django.shortcuts import render, redirect, get_object_or_404
from .models import Cliente
from .forms import ClienteForm
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q

def lista_clientes(request):
    query = request.GET.get('q')
    if query:
        clientes_list = Cliente.objects.filter(
            Q(nome__icontains=query) | Q(cpf__icontains=query)
        )
    else:
        clientes_list = Cliente.objects.all()

    paginator = Paginator(clientes_list, 50)  # Limite de 50 registros por página
    page = request.GET.get('page')
    try:
        clientes = paginator.page(page)
    except PageNotAnInteger:
        clientes = paginator.page(1)
    except EmptyPage:
        clientes = paginator.page(paginator.num_pages)

    context = {'clientes': clientes, 'query': query}
    return render(request, 'clientes/lista_clientes.html', context)

def criar_cliente(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_clientes')
    else:
        form = ClienteForm()
    return render(request, 'clientes/criar_cliente.html', {'form': form})

def editar_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            return redirect('lista_clientes')
    else:
        form = ClienteForm(instance=cliente)
    return render(request, 'clientes/editar_cliente.html', {'form': form, 'cliente': cliente})

def excluir_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == 'POST':
        cliente.delete()
        return redirect('lista_clientes')
    return render(request, 'clientes/confirmar_exclusao.html', {'cliente': cliente})
