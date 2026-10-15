"""
Catálogo dos módulos do sistema e regras de acesso.

Cada módulo corresponde a um model, e o Django já cria 4 permissões para ele:
view (ver), add (criar), change (editar) e delete (excluir).
"""

SOMENTE_ADMIN = "SOMENTE_ADMIN"

ACOES = [
    ("view", "Ver"),
    ("add", "Criar"),
    ("change", "Editar"),
    ("delete", "Excluir"),
]

# (nome do grupo, [(rótulo exibido, app, nome do model em minúsculo)])
MODULOS = [
    ("Cadastro", [
        ("Categorias", "estoque", "categoria"),
        ("Clientes", "clientes", "cliente"),
        ("Conservações", "estoque", "conservacao"),
        ("Cores", "estoque", "cor"),
        ("Produtos", "estoque", "produto"),
        ("Status", "estoque", "status"),
        ("Tecidos", "estoque", "tecido"),
    ]),
    ("Locações", [
        ("Locações", "locacoes", "locacao"),
        ("Consulta de disponibilidade", "locacoes", "itemlocacao"),
    ]),
]

ACOES_RESTRITAS = {
    ("locacoes", "itemlocacao"): ["view"],
}


def acoes_do_modulo(app, model):
    return ACOES_RESTRITAS.get((app, model), [acao for acao, _nome in ACOES])


PERMISSOES_DISPONIBILIDADE = ("locacoes.view_itemlocacao", "locacoes.view_locacao")

ALVOS = {
    "categoria": ("estoque", "categoria"),
    "categorias": ("estoque", "categoria"),
    "cliente": ("clientes", "cliente"),
    "clientes": ("clientes", "cliente"),
    "conservacao": ("estoque", "conservacao"),
    "conservacoes": ("estoque", "conservacao"),
    "cor": ("estoque", "cor"),
    "cores": ("estoque", "cor"),
    "produto": ("estoque", "produto"),
    "produtos": ("estoque", "produto"),
    "status": ("estoque", "status"),
    "tecido": ("estoque", "tecido"),
    "tecidos": ("estoque", "tecido"),
    "locacao": ("locacoes", "locacao"),
    "locacoes": ("locacoes", "locacao"),
}

PREFIXOS = {
    "lista": "view", "listar": "view", "consulta": "view", "consultar": "view",
    "buscar": "view", "busca": "view", "checar": "view", "verificar": "view",
    "detalhe": "view", "detalhes": "view", "ver": "view",
    "criar": "add", "novo": "add", "nova": "add", "cadastrar": "add", "adicionar": "add",
    "editar": "change", "alterar": "change", "atualizar": "change",
    "devolver": "change", "devolucao": "change", "cancelar": "change",
    "excluir": "delete", "deletar": "delete", "remover": "delete", "apagar": "delete",
}

# Áreas administrativas: qualquer URL cujo nome contenha uma destas palavras é exclusiva
# do administrador, o mesmo critério que já esconde esses itens do menu.
#  - cargos/funcionários: dados sensíveis (CPF, RG, salário);
#  - grupos: quem edita um grupo consegue dar permissões a si mesmo (escalada de privilégio).
PALAVRAS_SOMENTE_ADMIN = {"cargo", "cargos", "funcionario", "funcionarios", "grupo", "grupos"}

PERMISSOES_POR_URL = {
    "autocomplete_produtos": PERMISSOES_DISPONIBILIDADE,
    "verificar_disponibilidade": PERMISSOES_DISPONIBILIDADE,
    # Mudanças de status da locação (o nome não contém um módulo reconhecível,
    # então sem estas linhas ficariam liberadas para qualquer usuário logado).
    "marcar_prova_agendada": "locacoes.change_locacao",
    "marcar_retirada": "locacoes.change_locacao",
    "marcar_devolvido_item": "locacoes.change_locacao",
}