def acesso_negado(request):
    """Entrega ao template a mensagem de acesso negado e a apaga da sessão (aparece uma vez só)."""
    sessao = getattr(request, "session", None)
    mensagem = sessao.pop("acesso_negado", None) if sessao is not None else None
    return {"acesso_negado_msg": mensagem}