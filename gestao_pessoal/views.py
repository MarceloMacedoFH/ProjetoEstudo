from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from .models import Funcionario
from .forms import FuncionarioForm
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


# Create your views here.
def lista_funcionarios(request):
    query = request.GET.get('q')
    if query:
        funcionario_list = Funcionario.objects.filter(
            Q(nome_completo__icontains=query) | Q(cpf__icontains=query)
        )
    else:
        funcionario_list = Funcionario.objects.all()

    paginator = Paginator(funcionario_list, 50)  # Limite de 50 registros por página
    page = request.GET.get('page')
    try:
        funcionarios = paginator.page(page)
    except PageNotAnInteger:
        funcionarios = paginator.page(1)
    except EmptyPage:
        funcionarios = paginator.page(paginator.num_pages)

    context = {'funcionarios': funcionarios, 'query': query}

    return render(request, 'gestao_pessoal/funcionarios/lista_funcionarios.html', context)

def criar_funcionario(request):
    if request.method == 'POST':
        form = FuncionarioForm(request.POST)
        if form.is_valid():
            funcionario = form.save()
            return redirect(f"{reverse('lista_clientes')}?q={funcionario.cpf}")
    else:
        form = FuncionarioForm()
    return render(request, 'gestao_pessoal/funcionarios/criar_funcionario.html', {'form': form})

def editar_funcionario(request, pk):
    funcionario = get_object_or_404(Funcionario, pk=pk)
    if request.method == 'POST':
        form = FuncionarioForm(request.POST, instance=funcionario)
        if form.is_valid():
            funcionario = form.save()
            return redirect(f"{reverse('lista_funcionarios')}?q={funcionario.cpf}")
    else:
        form = FuncionarioForm(instance=funcionario)
    return render(request, 'gestao_pessoal/funcionarios/editar_funcionario.html', {'form': form, 'funcionario': funcionario})

def excluir_funcionario(request, pk):
    funcionario = get_object_or_404(Funcionario, pk=pk)
    if request.method == 'POST':
        funcionario.delete()
        return redirect('lista_funcionarios')
    return render(request, 'gestao_pessoal/funcionarios/confirmar_exclusao.html', {'funcionario': funcionario})