"""
Funções auxiliares para criar dados de teste (usadas pelos tests.py de cada app).
Não são importadas pelo sistema em produção.
"""
from datetime import date
from decimal import Decimal
from itertools import count

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission

from clientes.models import Cliente
from estoque.models import Categoria, Conservacao, Cor, Produto, Status
from locacoes.models import ItemLocacao, Locacao

SENHA = "senha-de-teste-123"
RETIRADA_PADRAO = date(2026, 11, 10)  # terça-feira -> prova 07/11 (sáb), devolução prevista 13/11

_sequencia = count(1)


def _n():
    return next(_sequencia)


def criar_cliente(**extra):
    n = _n()
    dados = dict(
        nome=f"Cliente {n}", cpf=f"{n:011d}", contato="11999990000", cep="09300-000",
        endereco="Rua A", numero="1", bairro="Centro", municipio="Maua", estado="SP",
    )
    dados.update(extra)
    return Cliente.objects.create(**dados)


def criar_produto(**extra):
    n = _n()
    categoria, _ = Categoria.objects.get_or_create(descricao="VESTIDO", categoria_pai=None)
    status, _ = Status.objects.get_or_create(descricao="DISPONIVEL")
    conservacao, _ = Conservacao.objects.get_or_create(descricao="OTIMA")
    cor, _ = Cor.objects.get_or_create(descricao="BRANCO")
    dados = dict(
        descricao=f"Vestido {n}", codigo=f"P{n:04d}", categoria=categoria, origem="NAC",
        tipo="NVA", cor_principal=cor, tamanho_etiqueta="M", genero="F", status=status,
        conservacao=conservacao, preco_aluguel_padrao=Decimal("100.00"),
        multa_atraso_diaria=Decimal("10.00"),
    )
    dados.update(extra)
    return Produto.objects.create(**dados)


def criar_locacao(cliente=None, retirada=RETIRADA_PADRAO, status=Locacao.STATUS_RESERVADA,
                  produtos=(), **extra):
    """Cria a locação e um item para cada produto informado (preço padrão)."""
    locacao = Locacao.objects.create(
        cliente=cliente or criar_cliente(), data_retirada=retirada, status=status, **extra
    )
    for produto in produtos:
        ItemLocacao.objects.create(locacao=locacao, produto=produto)
    return locacao


def fixar_datas(locacao, **campos):
    """
    Força datas calculadas (data_prova, data_devolucao_prevista...) ou automáticas
    (data_fechamento) usando update(), que não passa pelo save() do model.
    """
    Locacao.objects.filter(pk=locacao.pk).update(**campos)
    locacao.refresh_from_db()
    return locacao


def criar_usuario(username="atendente", permissoes=(), superusuario=False):
    """`permissoes`: lista no formato 'app.codename', ex.: 'clientes.view_cliente'."""
    User = get_user_model()
    if superusuario:
        return User.objects.create_superuser(username, f"{username}@teste.com", SENHA)
    usuario = User.objects.create_user(username, f"{username}@teste.com", SENHA)
    for codigo in permissoes:
        app, codename = codigo.split(".", 1)
        usuario.user_permissions.add(
            Permission.objects.get(content_type__app_label=app, codename=codename)
        )
    return usuario
