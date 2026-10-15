from django.contrib import messages
from django.db.models import ProtectedError, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from .models import Funcionario, Cargo
from .forms import FuncionarioForm, CargoForm
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


#Cargos
def lista_cargos(request):
    query = request.GET.get('q')
    if query:
        list = Cargo.objects.filter(
            Q(descricao__icontains=query)
        )
    else:
        list = Cargo.objects.all()

    paginator = Paginator(list, 50)  # Limite de 50 registros por página
    page = request.GET.get('page')
    try:
        cargos = paginator.page(page)
    except PageNotAnInteger:
        cargos = paginator.page(1)
    except EmptyPage:
        cargos = paginator.page(paginator.num_pages)

    context = {'cargos': cargos, 'query': query}

    return render(request, 'gestao_pessoal/cargos/lista_cargos.html', context)

def criar_cargo(request):
    if request.method == 'POST':
        form = CargoForm(request.POST)
        if form.is_valid():
            cargo = form.save()
            return redirect(f"{reverse('lista_cargos')}?q={cargo.descricao}")
    else:
        form = CargoForm()
    return render(request, 'gestao_pessoal/cargos/criar_cargo.html', {'form': form})

def editar_cargo(request, pk):
    cargo = get_object_or_404(Cargo, pk=pk)
    if request.method == 'POST':
        form = CargoForm(request.POST, instance=cargo)
        if form.is_valid():
            cargo = form.save()
            return redirect(f"{reverse('lista_cargos')}?q={cargo.descricao}")
    else:
        form = CargoForm(instance=cargo)
    return render(request, 'gestao_pessoal/cargos/editar_cargo.html', {'form': form, 'cargo': cargo})

def excluir_cargo(request, pk):
    cargo = get_object_or_404(Cargo, pk=pk)
    if request.method == 'POST':
        try:
            cargo.delete()
        except ProtectedError:
            messages.error(
                request,
                f'Não é possível excluir o cargo "{cargo.descricao}" porque ele está em uso '
                f'por funcionários. Desmarque o status do cargo em vez de excluir.'
            )
            return redirect('editar_cargo', pk=cargo.pk)
        return redirect('lista_cargos')
    return render(request, 'gestao_pessoal/cargos/confirmar_exclusao.html', {'cargo': cargo})


#Funcionários
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
            return redirect(f"{reverse('lista_funcionarios')}?q={funcionario.cpf}")
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