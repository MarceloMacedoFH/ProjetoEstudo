from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.factories import criar_locacao, criar_produto, criar_usuario, fixar_datas
from locacoes.models import ItemLocacao, Locacao

R = Locacao.STATUS_RESERVADA
P = Locacao.STATUS_PROVA_AGENDADA
RET = Locacao.STATUS_RETIRADA
ATR = Locacao.STATUS_ATRASADA
CAN = Locacao.STATUS_CANCELADA


class CardsDaHomeTests(TestCase):
    def setUp(self):
        self.hoje = timezone.localdate()
        self.ontem = self.hoje - timedelta(days=1)
        self.amanha = self.hoje + timedelta(days=1)
        self.client.force_login(criar_usuario(superusuario=True))

    def cards(self):
        contexto = self.client.get(reverse("home")).context
        return {
            nome: contexto[nome]
            for nome in ("total_provas", "total_retiradas", "total_devolucoes",
                         "total_atrasos", "total_alugados")
        }

    def locacao(self, status=R, itens=1, **datas):
        loc = criar_locacao(status=status, produtos=[criar_produto() for _ in range(itens)])
        return fixar_datas(loc, **datas) if datas else loc

    def test_tudo_zerado_sem_locacoes(self):
        self.assertEqual(set(self.cards().values()), {0})

    def test_provas_de_hoje_so_antes_da_retirada(self):
        self.locacao(R, data_prova=self.hoje)
        self.locacao(P, data_prova=self.hoje)
        self.locacao(RET, data_prova=self.hoje)       # já retirada: não conta
        self.locacao(CAN, data_prova=self.hoje)       # cancelada: não conta
        self.locacao(R, data_prova=self.amanha)       # outro dia: não conta
        self.assertEqual(self.cards()["total_provas"], 2)

    def test_alugueis_efetuados_hoje_sem_canceladas(self):
        self.locacao(R, data_fechamento=self.hoje)
        self.locacao(RET, data_fechamento=self.hoje)
        self.locacao(CAN, data_fechamento=self.hoje)
        self.locacao(R, data_fechamento=self.ontem)
        self.assertEqual(self.cards()["total_alugados"], 2)

    def test_pecas_para_retirar_hoje(self):
        self.locacao(R, itens=2, data_retirada=self.hoje)
        self.locacao(P, itens=1, data_retirada=self.hoje)
        self.locacao(RET, itens=1, data_retirada=self.hoje)   # já saiu: não conta
        self.locacao(R, itens=1, data_retirada=self.amanha)   # outro dia: não conta
        self.assertEqual(self.cards()["total_retiradas"], 3)

    def test_devolucoes_esperadas_hoje_ignoram_pecas_ja_devolvidas(self):
        loc = self.locacao(RET, itens=2, data_devolucao_prevista=self.hoje)
        primeiro = loc.itens.order_by("pk").first()
        ItemLocacao.objects.filter(pk=primeiro.pk).update(data_devolucao_real_item=self.hoje)
        self.locacao(R, itens=1, data_devolucao_prevista=self.hoje)  # não retirada: não conta
        self.assertEqual(self.cards()["total_devolucoes"], 1)

    def test_pecas_atrasadas_contam_pela_data_mesmo_sem_o_comando(self):
        self.locacao(RET, itens=1, data_devolucao_prevista=self.ontem)   # vencida, status ainda "retirada"
        self.locacao(ATR, itens=2, data_devolucao_prevista=self.hoje - timedelta(days=5))
        self.locacao(RET, itens=1, data_devolucao_prevista=self.hoje)    # vence hoje: ainda não é atraso
        self.locacao(R, itens=1, data_devolucao_prevista=self.ontem)     # nem retirada: não conta
        self.assertEqual(self.cards()["total_atrasos"], 3)

    def test_usuario_sem_permissao_ve_cards_zerados(self):
        self.locacao(RET, itens=1, data_devolucao_prevista=self.ontem)
        self.locacao(R, data_prova=self.hoje)
        self.client.force_login(criar_usuario("sem_permissao"))
        self.assertEqual(set(self.cards().values()), {0})

    def test_permissao_de_locacoes_libera_os_cards(self):
        self.locacao(RET, itens=1, data_devolucao_prevista=self.ontem)
        self.client.force_login(criar_usuario("gerente", ["locacoes.view_locacao"]))
        self.assertEqual(self.cards()["total_atrasos"], 1)
