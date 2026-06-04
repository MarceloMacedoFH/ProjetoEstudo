from django.shortcuts import render, redirect
from .models import Cliente
from .forms import ClienteForm

def lista_clientes(request):
    # Buscamos todos os clientes ordenados pelo nome (conforme definido no Meta do Model)
    clientes = Cliente.objects.all()
    context = {'clientes': clientes}
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
