from django.contrib import messages
from django.contrib.auth import get_user_model, update_session_auth_hash
from django.contrib.auth.models import Group, Permission
from django.contrib.auth.views import LoginView
from django.db.models import Q, ProtectedError, RestrictedError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import GrupoForm, LoginForm, UsuarioForm
from .modulos import ACOES, MODULOS, acoes_do_modulo

User = get_user_model()


class LoginUsuarioView(LoginView):
    template_name = "usuarios/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True


# ---------- auxiliares de permissão ----------

def _permissoes_validas():
    return {
        f"{app}.{acao}_{model}"
        for _grupo, itens in MODULOS
        for _rotulo, app, model in itens
        for acao in acoes_do_modulo(app, model)
    }


def _montar_matriz(marcadas):
    grupos = []
    for nome_grupo, itens in MODULOS:
        linhas = []
        for rotulo, app, model in itens:
            celulas = []
            permitidas = acoes_do_modulo(app, model)
            for acao, _nome in ACOES:
                if acao in permitidas:
                    codigo = f"{app}.{acao}_{model}"
                    celulas.append({"codigo": codigo, "acao": acao, "marcada": codigo in marcadas})
                else:
                    celulas.append({"codigo": None, "acao": acao, "marcada": False})
            linhas.append({"nome": rotulo, "celulas": celulas})
        grupos.append({"nome": nome_grupo, "linhas": linhas})
    return grupos


def _permissoes_do_grupo(grupo):
    return {
        f"{p.content_type.app_label}.{p.codename}"
        for p in grupo.permissions.select_related("content_type")
    }


def _aplicar_permissoes_grupo(grupo, selecionadas):
    escolhidas = set(selecionadas) & _permissoes_validas()

    for codigo in list(escolhidas):
        app, cod = codigo.split(".", 1)
        _acao, model = cod.split("_", 1)
        escolhidas.add(f"{app}.view_{model}")

    permissoes = []
    for codigo in escolhidas:
        app, cod = codigo.split(".", 1)
        permissoes.append(Permission.objects.get(content_type__app_label=app, codename=cod))
    grupo.permissions.set(permissoes)


def _contexto_form_grupo(form, marcadas, editando, grupo=None):
    return {
        "form": form,
        "grupos": _montar_matriz(marcadas),
        "acoes": ACOES,
        "editando": editando,
        "grupo_edicao": grupo,
    }


# ---------- gestão de grupos (somente administrador) ----------

def lista_grupos(request):
    query = request.GET.get("q", "").strip()
    grupos = Group.objects.all().order_by("name")
    if query:
        grupos = grupos.filter(name__icontains=query)
    return render(request, "usuarios/lista_grupos.html", {"grupos": grupos, "query": query})


def criar_grupo(request):
    form = GrupoForm(request.POST or None)
    marcadas = set(request.POST.getlist("perms"))

    if request.method == "POST" and form.is_valid():
        grupo = form.save()
        _aplicar_permissoes_grupo(grupo, marcadas)
        messages.success(request, "Grupo de acesso criado com sucesso.")
        return redirect("lista_grupos")

    return render(request, "usuarios/form_grupo.html", _contexto_form_grupo(form, marcadas, False))


def editar_grupo(request, pk):
    grupo = get_object_or_404(Group, pk=pk)
    form = GrupoForm(request.POST or None, instance=grupo)

    if request.method == "POST":
        marcadas = set(request.POST.getlist("perms"))
    else:
        marcadas = _permissoes_do_grupo(grupo)

    if request.method == "POST" and form.is_valid():
        grupo = form.save()
        _aplicar_permissoes_grupo(grupo, marcadas)
        messages.success(request, "Grupo de acesso atualizado com sucesso.")
        return redirect("lista_grupos")

    return render(
        request, "usuarios/form_grupo.html", _contexto_form_grupo(form, marcadas, True, grupo)
    )


@require_POST
def excluir_grupo(request, pk):
    grupo = get_object_or_404(Group, pk=pk)
    nome = grupo.name
    grupo.delete()
    messages.success(request, f"Grupo '{nome}' excluído com sucesso.")
    return redirect("lista_grupos")


# ---------- gestão de usuários (somente administrador) ----------

def lista_usuarios(request):
    query = request.GET.get("q", "").strip()
    usuarios = User.objects.prefetch_related("groups").exclude(username="admin").order_by("username")
    if query:
        usuarios = usuarios.filter(
            Q(username__icontains=query)
            | Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
        )
    return render(request, "usuarios/lista_usuarios.html", {"usuarios": usuarios, "query": query})


def criar_usuario(request):
    form = UsuarioForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        usuario = form.save(commit=False)
        usuario.set_password(form.cleaned_data["password1"])
        usuario.save()

        grupo = form.cleaned_data.get("grupo")
        if grupo:
            usuario.groups.set([grupo])

        messages.success(request, "Usuário cadastrado com sucesso.")
        return redirect("lista_usuarios")

    return render(request, "usuarios/form_usuario.html", {"form": form, "editando": False})


def editar_usuario(request, pk):
    usuario = get_object_or_404(User, pk=pk)
    form = UsuarioForm(request.POST or None, instance=usuario)

    if request.method == "POST" and form.is_valid():
        editando_a_si_mesmo = usuario.pk == request.user.pk
        usuario = form.save(commit=False)

        if editando_a_si_mesmo:
            usuario.is_active = True
            usuario.is_superuser = True

        senha = form.cleaned_data.get("password1")
        if senha:
            usuario.set_password(senha)
        usuario.save()

        grupo = form.cleaned_data.get("grupo")
        if grupo:
            usuario.groups.set([grupo])
        else:
            usuario.groups.clear()

        if senha and editando_a_si_mesmo:
            update_session_auth_hash(request, usuario)

        messages.success(request, "Usuário atualizado com sucesso.")
        return redirect("lista_usuarios")

    return render(
        request, "usuarios/form_usuario.html", {"form": form, "editando": True, "usuario_edicao": usuario}
    )


def excluir_usuario(request, pk):
    usuario = get_object_or_404(User, pk=pk)

    if request.method == "POST":
        if usuario.pk == request.user.pk:
            messages.error(request, "Você não pode excluir o seu próprio usuário.")
            return redirect("lista_usuarios")

        if usuario.is_superuser and not User.objects.filter(is_superuser=True).exclude(pk=usuario.pk).exists():
            messages.error(request, "Não é possível excluir o único administrador do sistema.")
            return redirect("lista_usuarios")

        try:
            nome = usuario.username
            usuario.delete()
            messages.success(request, f"Usuário {nome} excluído com sucesso.")
        except (ProtectedError, RestrictedError):
            messages.error(request, "Este usuário possui registros vinculados e não pode ser excluído. Desmarque 'Usuário ativo' para bloqueá-lo.")
        return redirect("lista_usuarios")
    else:
        return render(request, 'usuarios/confirmar_exclusao.html', {'usuario': usuario})