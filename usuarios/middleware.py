import logging
from urllib.parse import urlparse

from django.contrib.auth.views import redirect_to_login
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme

from .modulos import (
    ALVOS,
    MODULOS,
    PERMISSOES_DISPONIBILIDADE,
    PERMISSOES_POR_URL,
    PREFIXOS,
    SOMENTE_ADMIN,
)

logger = logging.getLogger(__name__)

URLS_LIVRES = {"login", "logout"}

ROTULOS = {
    (app, model): rotulo
    for _grupo, itens in MODULOS
    for rotulo, app, model in itens
}

VERBOS = {
    "view": "acessar",
    "add": "criar registros em",
    "change": "editar registros em",
    "delete": "excluir registros em",
}


class ControleAcessoMiddleware:
    """
    1) Todo o sistema exige login (exceto login/logout e o /admin/, que tem login próprio).
    2) Usuário comum só acessa o que tem permissão (view/add/change/delete).
    3) Superusuário acessa tudo; a tela de usuários é exclusiva dele.

    Sem permissão: o usuário volta para a tela de onde veio e um modal explica o bloqueio.
    Em requisições AJAX/fetch a resposta é um JSON 403 (o base.html abre o modal).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        if request.path.startswith("/admin/"):
            return None

        nome = request.resolver_match.url_name or ""
        if nome in URLS_LIVRES:
            return None

        user = request.user
        if not user.is_authenticated:
            if self._eh_ajax(request):
                return JsonResponse({"erro": "Sessão expirada. Faça login novamente."}, status=401)
            return redirect_to_login(request.get_full_path())

        if user.is_superuser or nome == "home":
            return None

        exigida = self._permissao_exigida(nome)
        if exigida is None:
            logger.warning("URL '%s' sem permissão mapeada (acesso liberado apenas com login).", nome)
            return None
        if not self._tem_acesso(user, exigida):
            return self._negar(request, exigida)
        return None

    @staticmethod
    def _tem_acesso(user, exigida):
        """`exigida` pode ser uma permissão, várias (basta uma) ou SOMENTE_ADMIN."""
        if exigida == SOMENTE_ADMIN:
            return False
        permissoes = (exigida,) if isinstance(exigida, str) else exigida
        return any(user.has_perm(p) for p in permissoes)

    # ---------- negação de acesso ----------

    def _negar(self, request, exigida):
        mensagem = self._mensagem(request.user, exigida)

        if self._eh_ajax(request):
            return JsonResponse({"acesso_negado": True, "erro": mensagem}, status=403)

        # o context processor lê e apaga esta chave na próxima tela exibida
        request.session["acesso_negado"] = mensagem
        return redirect(self._destino(request))

    @staticmethod
    def _mensagem(user, exigida):
        nome = user.get_full_name() or user.username
        if exigida == SOMENTE_ADMIN:
            return f"O usuário {nome} não tem permissão para acessar esta área, restrita ao administrador."

        principal = exigida if isinstance(exigida, str) else exigida[0]
        app, codigo = principal.split(".", 1)
        acao, model = codigo.split("_", 1)
        rotulo = ROTULOS.get((app, model), model)
        return f"O usuário {nome} não tem permissão para {VERBOS.get(acao, 'acessar')} {rotulo}."

    @staticmethod
    def _destino(request):
        """Volta para a página de origem; sem origem válida, vai para a home."""
        origem = request.META.get("HTTP_REFERER", "")
        if origem and url_has_allowed_host_and_scheme(
            origem, allowed_hosts={request.get_host()}, require_https=request.is_secure()
        ):
            if urlparse(origem).path != request.path:
                return origem
        return reverse("home")

    @staticmethod
    def _eh_ajax(request):
        cabecalhos = request.headers
        if cabecalhos.get("x-requested-with") == "XMLHttpRequest":
            return True
        modo = cabecalhos.get("sec-fetch-mode")
        if modo:
            return modo != "navigate"
        aceita = cabecalhos.get("accept", "")
        return "application/json" in aceita and "text/html" not in aceita

    # ---------- mapeamento URL -> permissão ----------

    @staticmethod
    def _permissao_exigida(nome):
        if nome in PERMISSOES_POR_URL:
            return PERMISSOES_POR_URL[nome]

        palavras = nome.split("_")
        if {"usuario", "usuarios"} & set(palavras):
            return SOMENTE_ADMIN

        # consulta_disponibilidade e verificar_disponibilidade: não dependem do módulo Locações
        if "disponibilidade" in palavras:
            return PERMISSOES_DISPONIBILIDADE

        alvo = next((ALVOS[p] for p in palavras if p in ALVOS), None)
        if alvo is None:
            return None

        app, model = alvo
        acao = PREFIXOS.get(palavras[0], "change")
        return f"{app}.{acao}_{model}"