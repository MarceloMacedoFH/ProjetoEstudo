from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse

from clientes.models import Cliente
from core.factories import criar_cliente, criar_locacao, criar_usuario


class ClienteModelTests(TestCase):
    def test_textos_sao_gravados_em_maiusculo_e_email_em_minusculo(self):
        cliente = criar_cliente(nome="maria da silva", bairro="centro", email="Maria@Email.COM")
        cliente.refresh_from_db()
        self.assertEqual(cliente.nome, "MARIA DA SILVA")
        self.assertEqual(cliente.bairro, "CENTRO")
        self.assertEqual(cliente.email, "maria@email.com")


class ExclusaoDeClienteTests(TestCase):
    def setUp(self):
        self.client.force_login(criar_usuario(superusuario=True))

    def test_cliente_sem_locacao_e_excluido(self):
        cliente = criar_cliente()
        resposta = self.client.post(reverse("excluir_cliente", args=[cliente.pk]))
        self.assertRedirects(resposta, reverse("lista_clientes"))
        self.assertFalse(Cliente.objects.filter(pk=cliente.pk).exists())

    def test_cliente_com_locacao_nao_e_excluido_e_nao_gera_erro_500(self):
        cliente = criar_cliente()
        criar_locacao(cliente=cliente)
        resposta = self.client.post(reverse("excluir_cliente", args=[cliente.pk]))
        self.assertRedirects(resposta, reverse("editar_cliente", args=[cliente.pk]))
        self.assertTrue(Cliente.objects.filter(pk=cliente.pk).exists())
        textos = [str(m) for m in get_messages(resposta.wsgi_request)]
        self.assertTrue(any("possui locações" in t for t in textos))
