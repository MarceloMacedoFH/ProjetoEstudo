from datetime import date
from decimal import Decimal
from io import StringIO

from django.contrib.messages import get_messages
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.urls import reverse

from core.factories import (
    RETIRADA_PADRAO, SENHA, criar_cliente, criar_locacao, criar_produto,
    criar_usuario, fixar_datas,
)
from locacoes.models import ItemLocacao, Locacao, ParametroSistema


class CalculoDeDatasTests(TestCase):
    def test_prova_tres_dias_antes_e_devolucao_tres_dias_depois(self):
        loc = criar_locacao(retirada=date(2026, 11, 10))
        self.assertEqual(loc.data_prova, date(2026, 11, 7))
        self.assertEqual(loc.data_devolucao_prevista, date(2026, 11, 13))

    def test_prova_que_cairia_no_domingo_vai_para_o_sabado(self):
        # 14/10/2026 é quarta; 3 dias antes é domingo (11/10) -> sábado (10/10)
        loc = criar_locacao(retirada=date(2026, 10, 14))
        self.assertEqual(loc.data_prova, date(2026, 10, 10))
        self.assertEqual(loc.data_devolucao_prevista, date(2026, 10, 17))

    def test_prova_na_segunda_nao_e_alterada(self):
        loc = criar_locacao(retirada=date(2026, 10, 15))  # quinta
        self.assertEqual(loc.data_prova, date(2026, 10, 12))  # segunda


class DisponibilidadeTests(TestCase):
    def setUp(self):
        self.produto = criar_produto()
        # reserva de 10/11 a 13/11
        self.locacao = criar_locacao(produtos=[self.produto])

    def livre(self, inicio, fim, produto=None):
        return ItemLocacao.esta_disponivel(produto or self.produto, inicio, fim)

    def test_periodo_sobreposto_nao_esta_disponivel(self):
        self.assertFalse(self.livre(date(2026, 11, 10), date(2026, 11, 13)))
        self.assertFalse(self.livre(date(2026, 11, 12), date(2026, 11, 15)))

    def test_mesmo_dia_da_devolucao_ou_da_retirada_conta_como_conflito(self):
        self.assertFalse(self.livre(date(2026, 11, 13), date(2026, 11, 16)))
        self.assertFalse(self.livre(date(2026, 11, 7), date(2026, 11, 10)))

    def test_periodos_vizinhos_sem_sobreposicao_estao_livres(self):
        self.assertTrue(self.livre(date(2026, 11, 14), date(2026, 11, 17)))
        self.assertTrue(self.livre(date(2026, 11, 6), date(2026, 11, 9)))

    def test_outro_produto_nao_e_afetado(self):
        outro = criar_produto()
        self.assertTrue(self.livre(date(2026, 11, 10), date(2026, 11, 13), outro))

    def test_locacao_cancelada_ou_devolvida_libera_a_peca(self):
        for status in (Locacao.STATUS_CANCELADA, Locacao.STATUS_DEVOLVIDA):
            Locacao.objects.filter(pk=self.locacao.pk).update(status=status)
            self.assertTrue(self.livre(date(2026, 11, 10), date(2026, 11, 13)), status)

    def test_locacao_atrasada_continua_bloqueando(self):
        Locacao.objects.filter(pk=self.locacao.pk).update(status=Locacao.STATUS_ATRASADA)
        self.assertFalse(self.livre(date(2026, 11, 10), date(2026, 11, 13)))

    def test_datas_reservadas_ignora_atrasadas_e_encerradas(self):
        self.assertEqual(ItemLocacao.datas_reservadas(self.produto).count(), 1)
        for status in (Locacao.STATUS_ATRASADA, Locacao.STATUS_DEVOLVIDA, Locacao.STATUS_CANCELADA):
            Locacao.objects.filter(pk=self.locacao.pk).update(status=status)
            self.assertEqual(ItemLocacao.datas_reservadas(self.produto).count(), 0, status)


class ValoresTests(TestCase):
    def test_item_sem_valor_usa_preco_padrao_do_produto(self):
        produto = criar_produto(preco_aluguel_padrao=Decimal("150.00"))
        item = ItemLocacao.objects.create(locacao=criar_locacao(), produto=produto)
        self.assertEqual(item.valor_aplicado, Decimal("150.00"))

    def test_item_com_valor_manual_mantem_o_valor(self):
        item = ItemLocacao.objects.create(
            locacao=criar_locacao(), produto=criar_produto(), valor_aplicado=Decimal("80.00")
        )
        self.assertEqual(item.valor_aplicado, Decimal("80.00"))

    def test_valor_total_e_saldo(self):
        loc = criar_locacao(sinal_pago=Decimal("50"), desconto=Decimal("10"))
        ItemLocacao.objects.create(locacao=loc, produto=criar_produto())  # 100
        ItemLocacao.objects.create(locacao=loc, produto=criar_produto(), valor_aplicado=Decimal("80"))
        Locacao.objects.filter(pk=loc.pk).update(desconto_indicacao_acumulado=Decimal("20"))
        loc.refresh_from_db()
        self.assertEqual(loc.valor_total, Decimal("180"))
        self.assertEqual(loc.saldo, Decimal("100"))  # 180 - 50 - 10 - 20

    def test_total_locacoes_do_produto_sobe_so_na_criacao_do_item(self):
        produto = criar_produto()
        item = ItemLocacao.objects.create(locacao=criar_locacao(), produto=produto)
        produto.refresh_from_db()
        self.assertEqual(produto.total_locacoes, 1)
        item.retornou_lavanderia = True
        item.save()
        produto.refresh_from_db()
        self.assertEqual(produto.total_locacoes, 1)

    def test_multa_por_dia_de_atraso(self):
        loc = criar_locacao()  # devolução prevista: 13/11
        item = ItemLocacao.objects.create(
            locacao=loc, produto=criar_produto(multa_atraso_diaria=Decimal("10.00"))
        )
        item.data_devolucao_real_item = date(2026, 11, 15)
        self.assertEqual(item.dias_atraso, 2)
        self.assertEqual(item.multa_calculada, Decimal("20.00"))

    def test_devolucao_no_prazo_ou_antes_nao_gera_multa(self):
        loc = criar_locacao()
        item = ItemLocacao.objects.create(locacao=loc, produto=criar_produto())
        for dia in (date(2026, 11, 13), date(2026, 11, 12)):
            item.data_devolucao_real_item = dia
            self.assertEqual(item.dias_atraso, 0)
            self.assertEqual(item.multa_calculada, 0)

    def test_item_nao_devolvido_nao_tem_multa(self):
        item = ItemLocacao.objects.create(locacao=criar_locacao(), produto=criar_produto())
        self.assertEqual(item.dias_atraso, 0)


class DescontoDeIndicacaoTests(TestCase):
    def setUp(self):
        ParametroSistema.objects.update_or_create(
            chave="desconto_indicacao", defaults={"valor": Decimal("50.00"), "ativo": True}
        )
        self.indicadora = criar_locacao()

    def acumulado(self):
        self.indicadora.refresh_from_db()
        return self.indicadora.desconto_indicacao_acumulado

    def test_indicacao_credita_o_desconto_na_locacao_indicadora(self):
        criar_locacao(indicado_por=self.indicadora)
        self.assertEqual(self.acumulado(), Decimal("50.00"))

    def test_salvar_de_novo_nao_credita_outra_vez(self):
        indicada = criar_locacao(indicado_por=self.indicadora)
        indicada.sinal_pago = Decimal("10")
        indicada.save()
        self.assertEqual(self.acumulado(), Decimal("50.00"))

    def test_cada_nova_indicacao_acumula(self):
        criar_locacao(indicado_por=self.indicadora)
        criar_locacao(indicado_por=self.indicadora)
        self.assertEqual(self.acumulado(), Decimal("100.00"))

    def test_sem_parametro_ou_parametro_inativo_nao_credita(self):
        ParametroSistema.objects.filter(chave="desconto_indicacao").update(ativo=False)
        criar_locacao(indicado_por=self.indicadora)
        self.assertEqual(self.acumulado(), 0)
        ParametroSistema.objects.filter(chave="desconto_indicacao").delete()
        criar_locacao(indicado_por=self.indicadora)
        self.assertEqual(self.acumulado(), 0)

    def test_valor_travado_nao_muda_se_o_parametro_for_alterado_depois(self):
        criar_locacao(indicado_por=self.indicadora)
        ParametroSistema.objects.filter(chave="desconto_indicacao").update(valor=Decimal("999"))
        self.assertEqual(self.acumulado(), Decimal("50.00"))


class StatusDaLocacaoTests(TestCase):
    def test_cancelar_so_ate_a_prova(self):
        for status in (Locacao.STATUS_RESERVADA, Locacao.STATUS_PROVA_AGENDADA):
            loc = criar_locacao(status=status)
            loc.cancelar()
            self.assertEqual(loc.status, Locacao.STATUS_CANCELADA)

    def test_nao_cancela_depois_da_retirada(self):
        for status in (Locacao.STATUS_RETIRADA, Locacao.STATUS_ATRASADA, Locacao.STATUS_DEVOLVIDA):
            loc = criar_locacao(status=status)
            with self.assertRaises(ValidationError):
                loc.cancelar()

    def test_devolver_todos_os_itens_conclui_a_locacao(self):
        loc = criar_locacao(status=Locacao.STATUS_RETIRADA, produtos=[criar_produto(), criar_produto()])
        primeiro, segundo = loc.itens.order_by("pk")
        primeiro.data_devolucao_real_item = date(2026, 11, 12)
        primeiro.save()
        loc.verificar_conclusao()
        loc.refresh_from_db()
        self.assertEqual(loc.status, Locacao.STATUS_RETIRADA)  # falta um item

        segundo.data_devolucao_real_item = date(2026, 11, 14)
        segundo.save()
        loc.verificar_conclusao()
        loc.refresh_from_db()
        self.assertEqual(loc.status, Locacao.STATUS_DEVOLVIDA)
        self.assertEqual(loc.data_devolucao_real, date(2026, 11, 14))  # a data mais tardia


class AtrasoTests(TestCase):
    def setUp(self):
        self.locacao = criar_locacao(status=Locacao.STATUS_RETIRADA, produtos=[criar_produto()])
        # devolução prevista: 13/11/2026

    def status(self):
        self.locacao.refresh_from_db()
        return self.locacao.status

    def test_retirada_vencida_e_nao_devolvida_vira_atrasada(self):
        self.locacao.atualizar_status_por_atraso(date(2026, 11, 14))
        self.assertEqual(self.status(), Locacao.STATUS_ATRASADA)

    def test_no_proprio_dia_da_devolucao_ainda_nao_e_atraso(self):
        self.locacao.atualizar_status_por_atraso(date(2026, 11, 13))
        self.assertEqual(self.status(), Locacao.STATUS_RETIRADA)

    def test_locacao_que_nao_foi_retirada_nunca_fica_atrasada(self):
        for status in (Locacao.STATUS_RESERVADA, Locacao.STATUS_PROVA_AGENDADA,
                       Locacao.STATUS_CANCELADA, Locacao.STATUS_DEVOLVIDA):
            Locacao.objects.filter(pk=self.locacao.pk).update(status=status)
            self.locacao.refresh_from_db()
            self.locacao.atualizar_status_por_atraso(date(2026, 12, 1))
            self.assertEqual(self.status(), status)

    def test_itens_todos_devolvidos_nao_ficam_atrasados(self):
        self.locacao.itens.update(data_devolucao_real_item=date(2026, 11, 13))
        self.locacao.atualizar_status_por_atraso(date(2026, 12, 1))
        self.assertEqual(self.status(), Locacao.STATUS_RETIRADA)

    def test_comando_marca_atrasadas(self):
        saida = StringIO()
        call_command("atualizar_atrasos", data="2026-11-14", stdout=saida)
        self.assertEqual(self.status(), Locacao.STATUS_ATRASADA)
        self.assertIn("1 locação", saida.getvalue())

    def test_comando_respeita_a_data_de_referencia(self):
        call_command("atualizar_atrasos", data="2026-11-13", stdout=StringIO())
        self.assertEqual(self.status(), Locacao.STATUS_RETIRADA)

    def test_comando_dry_run_nao_altera_nada(self):
        saida = StringIO()
        call_command("atualizar_atrasos", data="2026-11-14", dry_run=True, stdout=saida)
        self.assertEqual(self.status(), Locacao.STATUS_RETIRADA)
        self.assertIn("simulação", saida.getvalue())

    def test_comando_rejeita_data_invalida(self):
        with self.assertRaises(CommandError):
            call_command("atualizar_atrasos", data="14/11/2026", stdout=StringIO())


class ViewsDeLocacaoTests(TestCase):
    """Fluxos pela interface, logado como administrador (as permissões ficam em usuarios/tests.py)."""

    def setUp(self):
        self.client.force_login(criar_usuario(superusuario=True))
        self.cliente = criar_cliente()
        self.produto = criar_produto()

    def payload(self, produto=None, retirada="2026-11-10"):
        return {
            "cliente": self.cliente.pk, "data_retirada": retirada,
            "sinal_pago": "0", "desconto": "0", "indicado_por": "",
            "itens-TOTAL_FORMS": "1", "itens-INITIAL_FORMS": "0",
            "itens-MIN_NUM_FORMS": "1", "itens-MAX_NUM_FORMS": "1000",
            "itens-0-produto": (produto or self.produto).pk, "itens-0-valor_aplicado": "",
        }

    def test_criar_locacao(self):
        resposta = self.client.post(reverse("criar_locacao"), self.payload())
        self.assertEqual(Locacao.objects.count(), 1)
        locacao = Locacao.objects.get()
        self.assertEqual(locacao.itens.count(), 1)
        self.assertRedirects(resposta, reverse("editar_locacao", args=[locacao.pk]))

    def test_criar_locacao_com_peca_ja_reservada_e_barrado(self):
        criar_locacao(produtos=[self.produto])  # 10/11 a 13/11
        resposta = self.client.post(reverse("criar_locacao"), self.payload(retirada="2026-11-12"))
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(Locacao.objects.count(), 1)
        textos = [str(m) for m in get_messages(resposta.wsgi_request)]
        self.assertTrue(any("não estão disponíveis" in t for t in textos))

    def test_marcar_prova_e_retirada_seguem_a_ordem(self):
        loc = criar_locacao(produtos=[self.produto])
        self.client.post(reverse("marcar_prova_agendada", args=[loc.pk]))
        loc.refresh_from_db()
        self.assertEqual(loc.status, Locacao.STATUS_PROVA_AGENDADA)
        self.client.post(reverse("marcar_retirada", args=[loc.pk]))
        loc.refresh_from_db()
        self.assertEqual(loc.status, Locacao.STATUS_RETIRADA)

    def test_marcar_retirada_por_get_nao_altera(self):
        loc = criar_locacao(produtos=[self.produto])
        self.client.get(reverse("marcar_retirada", args=[loc.pk]))
        loc.refresh_from_db()
        self.assertEqual(loc.status, Locacao.STATUS_RESERVADA)

    def test_devolver_o_ultimo_item_conclui_a_locacao(self):
        loc = criar_locacao(status=Locacao.STATUS_RETIRADA, produtos=[self.produto])
        item = loc.itens.get()
        self.client.post(
            reverse("marcar_devolvido_item", args=[item.pk]),
            {"data_devolucao_real_item": "2026-11-12"},
        )
        item.refresh_from_db()
        loc.refresh_from_db()
        self.assertEqual(item.data_devolucao_real_item, date(2026, 11, 12))
        self.assertEqual(loc.status, Locacao.STATUS_DEVOLVIDA)

    def test_devolucao_com_data_invalida_nao_altera(self):
        loc = criar_locacao(status=Locacao.STATUS_RETIRADA, produtos=[self.produto])
        item = loc.itens.get()
        resposta = self.client.post(
            reverse("marcar_devolvido_item", args=[item.pk]),
            {"data_devolucao_real_item": "12/11/2026"},
        )
        item.refresh_from_db()
        self.assertIsNone(item.data_devolucao_real_item)
        self.assertEqual(resposta.status_code, 302)

    def test_cancelar_locacao(self):
        loc = criar_locacao(produtos=[self.produto])
        self.client.post(reverse("cancelar_locacao", args=[loc.pk]))
        loc.refresh_from_db()
        self.assertEqual(loc.status, Locacao.STATUS_CANCELADA)

    def test_ajax_de_disponibilidade(self):
        criar_locacao(produtos=[self.produto])
        url = reverse("verificar_disponibilidade")
        ocupado = self.client.get(url, {"produto_id": self.produto.pk, "data_retirada": "2026-11-12"})
        self.assertFalse(ocupado.json()["disponivel"])
        self.assertEqual(ocupado.json()["data_devolucao_prevista"], "15/11/2026")
        livre = self.client.get(url, {"produto_id": self.produto.pk, "data_retirada": "2026-12-20"})
        self.assertTrue(livre.json()["disponivel"])
        self.assertEqual(self.client.get(url).status_code, 400)
