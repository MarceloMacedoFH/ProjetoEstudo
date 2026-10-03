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
        # Usa a permissão "ver" que o Django já cria para ItemLocacao (não precisa de migração)
        ("Consulta de disponibilidade", "locacoes", "itemlocacao"),
    ]),
]

# Módulos em que só algumas ações fazem sentido (as demais ficam em branco na tabela)
ACOES_RESTRITAS = {
    ("locacoes", "itemlocacao"): ["view"],
}


def acoes_do_modulo(app, model):
    return ACOES_RESTRITAS.get((app, model), [acao for acao, _nome in ACOES])


# Quem tiver QUALQUER uma destas permissões acessa a consulta/verificação de disponibilidade.
# (quem já tem acesso a Locações continua podendo usar, pois o formulário de locação depende dela)
PERMISSOES_DISPONIBILIDADE = ("locacoes.view_itemlocacao", "locacoes.view_locacao")

# Palavra encontrada no nome da URL -> (app, model)
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

# Primeira palavra do nome da URL -> ação exigida.
# Prefixo desconhecido exige "change" (o mais seguro).
PREFIXOS = {
    "lista": "view", "listar": "view", "consulta": "view", "consultar": "view",
    "buscar": "view", "busca": "view", "checar": "view", "verificar": "view",
    "detalhe": "view", "detalhes": "view", "ver": "view",
    "criar": "add", "novo": "add", "nova": "add", "cadastrar": "add", "adicionar": "add",
    "editar": "change", "alterar": "change", "atualizar": "change",
    "devolver": "change", "devolucao": "change", "cancelar": "change",
    "excluir": "delete", "deletar": "delete", "remover": "delete", "apagar": "delete",
}

# Exceções manuais: nome_da_url -> "app.acao_model" (ou várias, basta uma; ou SOMENTE_ADMIN)
# Exemplo: "buscar_clientes_locacao": "locacoes.add_locacao",
PERMISSOES_POR_URL = {}