from datetime import date

from django.test import TestCase
from django.urls import reverse

from core.factories import criar_usuario
from gestao_pessoal.models import Cargo, Funcionario


def criar_funcionario(**extra):
    dados = dict(
        nome_completo="joao pereira", endereco="Rua B", numero="10", municipio="Maua",
        sexo="M", raca_cor="NA", estado_civil="S", cpf="12345678901", rg="123456789",
        data_rg_emiss=date(2010, 1, 1), uf_rg="SP", org_emissor="SSP",
    )
    dados.update(extra)
    return Funcionario.objects.create(**dados)


class FuncionarioModelTests(TestCase):
    def test_matricula_e_gerada_com_zeros_a_esquerda(self):
        funcionario = criar_funcionario()
        self.assertEqual(funcionario.matricula, str(funcionario.pk).zfill(6))

    def test_str_mostra_matricula_e_nome(self):
        funcionario = criar_funcionario()
        self.assertEqual(str(funcionario), f"{funcionario.matricula} - JOAO PEREIRA")


class CargoViewsTests(TestCase):
    def setUp(self):
        self.client.force_login(criar_usuario(superusuario=True))

    def test_criar_cargo_invalido_reexibe_o_formulario(self):
        resposta = self.client.post(reverse("criar_cargo"), {"descricao": ""})
        self.assertEqual(resposta.status_code, 200)  # antes retornava None (erro 500)
        self.assertEqual(Cargo.objects.count(), 0)

    def test_cargo_em_uso_nao_e_excluido(self):
        cargo = Cargo.objects.create(descricao="vendedor")
        criar_funcionario(cargo=cargo)
        resposta = self.client.post(reverse("excluir_cargo", args=[cargo.pk]))
        self.assertRedirects(resposta, reverse("editar_cargo", args=[cargo.pk]))
        self.assertTrue(Cargo.objects.filter(pk=cargo.pk).exists())

    def test_cargo_sem_uso_e_excluido(self):
        cargo = Cargo.objects.create(descricao="caixa")
        resposta = self.client.post(reverse("excluir_cargo", args=[cargo.pk]))
        self.assertRedirects(resposta, reverse("lista_cargos"))
        self.assertFalse(Cargo.objects.filter(pk=cargo.pk).exists())
