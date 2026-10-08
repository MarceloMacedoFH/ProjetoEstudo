import re
from datetime import datetime

from django.contrib import messages
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Q, Value
from django.db.models.functions import Replace
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from clientes.models import Cliente
from estoque.models import Produto

from .forms import ItemLocacaoFormSet, LocacaoForm, _formatar_cliente_com_cpf
from .models import ItemLocacao, Locacao


# ---------------------------------------------------------------------------
# Listagem
# ---------------------------------------------------------------------------
def lista_locacoes(request):
    query = request.GET.get('q')
    locacoes_list = Locacao.objects.select_related('cliente').order_by('-data_fechamento')

    if query:
        locacoes_list = locacoes_list.filter(
            Q(cliente__nome__icontains=query) | Q(cliente__cpf__icontains=query)
        )

    paginator = Paginator(locacoes_list, 50)
    page = request.GET.get('page')
    try:
        locacoes = paginator.page(page)
    except PageNotAnInteger:
        locacoes = paginator.page(1)
    except EmptyPage:
        locacoes = paginator.page(paginator.num_pages)

    context = {'locacoes': locacoes, 'query': query}
    return render(request, 'locacoes/lista_locacoes.html', context)


# ---------------------------------------------------------------------------
# Criação
# ---------------------------------------------------------------------------
def criar_locacao(request):
    if request.method == 'POST':
        form = LocacaoForm(request.POST)
        formset = ItemLocacaoFormSet(request.POST, instance=Locacao())

        if form.is_valid() and formset.is_valid():
            locacao = form.save(commit=False)
            locacao.calcular_datas()

            conflitos = _checar_conflitos_formset(formset, locacao)
            if conflitos:
                messages.error(
                    request,
                    'As seguintes peças não estão disponíveis para o período '
                    f'escolhido: {", ".join(conflitos)}.'
                )
            else:
                locacao.save()
                formset.instance = locacao
                formset.save()
                messages.success(request, 'Locação criada com sucesso.')
                return redirect('editar_locacao', pk=locacao.pk)
    else:
        form = LocacaoForm()
        formset = ItemLocacaoFormSet(instance=Locacao())

    return render(request, 'locacoes/criar_locacao.html', {
        'form': form,
        'formset': formset,
    })


# ---------------------------------------------------------------------------
# Edição
# ---------------------------------------------------------------------------
def editar_locacao(request, pk):
    locacao = get_object_or_404(Locacao, pk=pk)

    if request.method == 'POST':
        form = LocacaoForm(request.POST, instance=locacao)
        formset = ItemLocacaoFormSet(request.POST, instance=locacao)

        if form.is_valid() and formset.is_valid():
            locacao_editada = form.save(commit=False)
            locacao_editada.calcular_datas()

            conflitos = _checar_conflitos_formset(
                formset, locacao_editada, ignorar_locacao=locacao
            )
            if conflitos:
                messages.error(
                    request,
                    'As seguintes peças não estão disponíveis para o período '
                    f'escolhido: {", ".join(conflitos)}.'
                )
            else:
                locacao_editada.save()
                formset.save()
                messages.success(request, 'Locação atualizada com sucesso.')
                return redirect('editar_locacao', pk=locacao.pk)
    else:
        form = LocacaoForm(instance=locacao)
        formset = ItemLocacaoFormSet(instance=locacao)

    return render(request, 'locacoes/editar_locacao.html', {
        'form': form,
        'formset': formset,
        'locacao': locacao,
    })


def _checar_conflitos_formset(formset, locacao, ignorar_locacao=None):
    """Retorna a lista de descrições de produtos em conflito de data."""
    conflitos = []
    for item_form in formset:
        if item_form.cleaned_data.get('DELETE'):
            continue
        produto = item_form.cleaned_data.get('produto')
        if not produto:
            continue

        qs = ItemLocacao.objects.filter(
            produto=produto,
            locacao__status__in=Locacao.STATUS_ABERTOS,
            locacao__data_retirada__lte=locacao.data_devolucao_prevista,
            locacao__data_devolucao_prevista__gte=locacao.data_retirada,
        )
        if ignorar_locacao is not None:
            qs = qs.exclude(locacao=ignorar_locacao)

        if qs.exists():
            conflitos.append(str(produto))
    return conflitos


# ---------------------------------------------------------------------------
# Cancelamento (não é exclusão — muda status e trava o sinal pago)
# ---------------------------------------------------------------------------
def cancelar_locacao(request, pk):
    locacao = get_object_or_404(Locacao, pk=pk)
    if request.method == 'POST':
        try:
            locacao.cancelar()
            messages.success(request, 'Locação cancelada.')
        except Exception as exc:
            messages.error(request, str(exc))
        return redirect('lista_locacoes')

    return render(request, 'locacoes/confirmar_cancelamento.html', {'locacao': locacao})


# ---------------------------------------------------------------------------
# Transições manuais de status
# ---------------------------------------------------------------------------
def marcar_prova_agendada(request, pk):
    locacao = get_object_or_404(Locacao, pk=pk)
    if request.method == 'POST' and locacao.status == Locacao.STATUS_RESERVADA:
        locacao.status = Locacao.STATUS_PROVA_AGENDADA
        locacao.save(update_fields=['status'])
        messages.success(request, 'Prova marcada como agendada.')
    return redirect('editar_locacao', pk=pk)


def marcar_retirada(request, pk):
    locacao = get_object_or_404(Locacao, pk=pk)
    if request.method == 'POST' and locacao.status in (
        Locacao.STATUS_RESERVADA, Locacao.STATUS_PROVA_AGENDADA
    ):
        locacao.status = Locacao.STATUS_RETIRADA
        locacao.save(update_fields=['status'])
        messages.success(request, 'Retirada confirmada.')
    return redirect('editar_locacao', pk=pk)


# ---------------------------------------------------------------------------
# Devolução por item (feita dentro da própria tela de editar a locação)
# ---------------------------------------------------------------------------
def marcar_devolvido_item(request, item_pk):
    item = get_object_or_404(ItemLocacao, pk=item_pk)
    if request.method == 'POST':
        data_str = request.POST.get('data_devolucao_real_item')
        if data_str:
            item.data_devolucao_real_item = datetime.strptime(data_str, '%Y-%m-%d').date()
        else:
            item.data_devolucao_real_item = timezone.localdate()
        item.save()
        item.locacao.verificar_conclusao()
        messages.success(request, f'Devolução de "{item.produto}" registrada.')
    return redirect('editar_locacao', pk=item.locacao_id)


# ---------------------------------------------------------------------------
# AJAX: checagem instantânea de disponibilidade (conveniência visual)
# ---------------------------------------------------------------------------
def verificar_disponibilidade(request):
    produto_id = request.GET.get('produto_id')
    data_retirada_str = request.GET.get('data_retirada')
    locacao_atual_id = request.GET.get('locacao_id')  # ignora a própria locação, na edição

    if not produto_id or not data_retirada_str:
        return JsonResponse({'erro': 'Parâmetros incompletos.'}, status=400)

    try:
        produto = Produto.objects.get(pk=produto_id)
        data_retirada = datetime.strptime(data_retirada_str, '%Y-%m-%d').date()
    except (Produto.DoesNotExist, ValueError):
        return JsonResponse({'erro': 'Dados inválidos.'}, status=400)

    locacao_temp = Locacao(data_retirada=data_retirada)
    locacao_temp.calcular_datas()

    qs = ItemLocacao.objects.filter(
        produto=produto,
        locacao__status__in=Locacao.STATUS_ABERTOS,
        locacao__data_retirada__lte=locacao_temp.data_devolucao_prevista,
        locacao__data_devolucao_prevista__gte=locacao_temp.data_retirada,
    )
    if locacao_atual_id:
        qs = qs.exclude(locacao_id=locacao_atual_id)

    disponivel = not qs.exists()

    return JsonResponse({
        'disponivel': disponivel,
        'data_devolucao_prevista': locacao_temp.data_devolucao_prevista.strftime('%d/%m/%Y'),
    })


# ---------------------------------------------------------------------------
# Autocomplete de produtos (usado na busca da tela de consulta de disponibilidade)
# ---------------------------------------------------------------------------
def autocomplete_produtos(request):
    termo = request.GET.get('termo', '').strip()
    produtos = []
    if len(termo) >= 2:
        produtos = list(
            Produto.objects.filter(
                Q(codigo__icontains=termo) | Q(descricao__icontains=termo)
            ).order_by('codigo')[:10].values('codigo', 'descricao')
        )
    return JsonResponse({'produtos': produtos})


# ---------------------------------------------------------------------------
# Tela de consulta de disponibilidade por código de produto
# ---------------------------------------------------------------------------
def consulta_disponibilidade(request):
    produto = None
    reservas = []
    codigo = request.GET.get('codigo', '').strip()

    if codigo:
        produto = Produto.objects.filter(codigo__iexact=codigo).first()
        if produto:
            reservas = ItemLocacao.datas_reservadas(produto)
        else:
            messages.error(request, 'Nenhum produto encontrado com esse código.')

    return render(request, 'locacoes/consulta_disponibilidade.html', {
        'produto': produto,
        'reservas': reservas,
        'codigo': codigo,
    })


# ---------------------------------------------------------------------------
# Autocomplete de clientes (campo de busca por nome ou CPF no formulário de locação)
# ---------------------------------------------------------------------------
def autocomplete_clientes(request):
    termo = request.GET.get('termo', '').strip()
    clientes = []

    if len(termo) >= 2:
        filtro = Q(nome__icontains=termo)

        # Se o termo parece um CPF (só números, pontos, traços ou espaços), busca também
        # pelo CPF ignorando a pontuação, não importa como ele foi gravado no banco.
        if re.fullmatch(r'[\d.\-\s]+', termo):
            digitos = re.sub(r'\D', '', termo)
            if digitos:
                filtro |= Q(cpf_limpo__icontains=digitos)

        cpf_limpo = Replace(
            Replace(Replace('cpf', Value('.'), Value('')), Value('-'), Value('')),
            Value(' '), Value(''),
        )
        queryset = (
            Cliente.objects
            .annotate(cpf_limpo=cpf_limpo)
            .filter(filtro)
            .order_by('nome')[:10]
        )
        clientes = [
            {'id': c.pk, 'nome': c.nome, 'label': _formatar_cliente_com_cpf(c)}
            for c in queryset
        ]

    return JsonResponse({'clientes': clientes})