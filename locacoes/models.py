from datetime import timedelta

from django.db import models
from django.db.models import F
from django.core.exceptions import ValidationError

from clientes.models import Cliente
from estoque.models import Produto


# ---------------------------------------------------------------------------
# ParametroSistema
# ---------------------------------------------------------------------------
class ParametroSistema(models.Model):
    """
    Tabela genérica de configurações do sistema, editável sem precisar
    alterar código. Hoje usada para o valor do desconto de indicação,
    mas pensada para acomodar outros parâmetros no futuro.
    """
    chave = models.CharField(max_length=100, unique=True)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    descricao = models.CharField(max_length=255, blank=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Parâmetro do Sistema"
        verbose_name_plural = "Parâmetros do Sistema"

    def __str__(self):
        return f"{self.chave} = {self.valor}"

    @classmethod
    def obter_valor(cls, chave, default=0):
        """Busca o valor de um parâmetro ativo pela chave; retorna default se não existir."""
        parametro = cls.objects.filter(chave=chave, ativo=True).first()
        return parametro.valor if parametro else default


# ---------------------------------------------------------------------------
# Locacao
# ---------------------------------------------------------------------------
class Locacao(models.Model):
    STATUS_RESERVADA = "reservada"
    STATUS_PROVA_AGENDADA = "prova_agendada"
    STATUS_RETIRADA = "retirada"
    STATUS_DEVOLVIDA = "devolvida"
    STATUS_ATRASADA = "atrasada"
    STATUS_CANCELADA = "cancelada"

    STATUS_CHOICES = [
        (STATUS_RESERVADA, "Reservada"),
        (STATUS_PROVA_AGENDADA, "Prova Agendada"),
        (STATUS_RETIRADA, "Retirada"),
        (STATUS_DEVOLVIDA, "Devolvida"),
        (STATUS_ATRASADA, "Atrasada"),
        (STATUS_CANCELADA, "Cancelada"),
    ]

    # Status considerados "em aberto" para fins de checagem de disponibilidade
    STATUS_ABERTOS = [
        STATUS_RESERVADA,
        STATUS_PROVA_AGENDADA,
        STATUS_RETIRADA,
        STATUS_ATRASADA,
    ]

    cliente = models.ForeignKey(
        Cliente, on_delete=models.PROTECT, related_name="locacoes"
    )
    data_fechamento = models.DateField(auto_now_add=True)
    data_retirada = models.DateField()

    # Calculadas automaticamente em save() — não editáveis manualmente
    data_prova = models.DateField(editable=False)
    data_devolucao_prevista = models.DateField(editable=False)

    data_devolucao_real = models.DateField(null=True, blank=True)

    sinal_pago = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    desconto = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Travado no momento em que uma locação indicada por esta é fechada.
    # Nunca recalculado a partir do estado atual das indicações.
    desconto_indicacao_acumulado = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, editable=False
    )

    indicado_por = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="indicacoes",
        verbose_name="Indicado por (locação de quem indicou)",
    )

    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_RESERVADA
    )

    class Meta:
        verbose_name = "Locação"
        verbose_name_plural = "Locações"
        indexes = [
            models.Index(fields=["status", "data_retirada"]),
            models.Index(fields=["status", "data_devolucao_prevista"]),
        ]

    def __str__(self):
        return f"Locação #{self.pk} - {self.cliente} ({self.get_status_display()})"

    # -- Cálculo automático de datas -------------------------------------
    def calcular_datas(self):
        prova = self.data_retirada - timedelta(days=3)
        # Se a prova cair num domingo, antecipa para sábado
        if prova.weekday() == 6:  # 0=segunda ... 6=domingo
            prova -= timedelta(days=1)
        self.data_prova = prova
        self.data_devolucao_prevista = self.data_retirada + timedelta(days=3)

    def save(self, *args, **kwargs):
        eh_nova = self._state.adding
        self.calcular_datas()
        super().save(*args, **kwargs)

        # Crédito de indicação: só na criação, e só uma vez.
        if eh_nova and self.indicado_por_id:
            self._creditar_desconto_indicacao()

    def _creditar_desconto_indicacao(self):
        valor_desconto = ParametroSistema.obter_valor("desconto_indicacao", default=0)
        if valor_desconto:
            Locacao.objects.filter(pk=self.indicado_por_id).update(
                desconto_indicacao_acumulado=F("desconto_indicacao_acumulado")
                + valor_desconto
            )

    # -- Valores ------------------------------------------------------------
    @property
    def valor_total(self):
        return sum((item.valor_aplicado for item in self.itens.all()), start=0)

    @property
    def saldo(self):
        return (
            self.valor_total
            - self.sinal_pago
            - self.desconto_ajuste
            - self.desconto_indicacao_acumulado
        )

    @property
    def multa_total(self):
        """Soma informativa das multas de todos os itens (não é campo do banco)."""
        return sum((item.multa_calculada for item in self.itens.all()), start=0)

    # -- Regras de status/ações ----------------------------------------
    def cancelar(self):
        if self.status not in (self.STATUS_RESERVADA, self.STATUS_PROVA_AGENDADA):
            raise ValidationError(
                "Só é possível cancelar até o dia da prova final."
            )
        self.status = self.STATUS_CANCELADA
        self.save()

    def atualizar_status_por_atraso(self, hoje):
        """
        Chamar periodicamente (ex: via management command diário) para
        marcar como Atrasada qualquer locação com item vencido e não devolvido.
        """
        if self.status in (self.STATUS_CANCELADA, self.STATUS_DEVOLVIDA):
            return
        tem_item_atrasado = self.itens.filter(
            data_devolucao_real_item__isnull=True,
        ).exists() and hoje > self.data_devolucao_prevista
        if tem_item_atrasado and self.status != self.STATUS_ATRASADA:
            self.status = self.STATUS_ATRASADA
            self.save(update_fields=["status"])

    def verificar_conclusao(self):
        """Chamar depois de registrar a devolução de um item."""
        todos_devolvidos = not self.itens.filter(
            data_devolucao_real_item__isnull=True
        ).exists()
        if todos_devolvidos:
            self.status = self.STATUS_DEVOLVIDA
            self.data_devolucao_real = self.itens.aggregate(
                models.Max("data_devolucao_real_item")
            )["data_devolucao_real_item__max"]
            self.save(update_fields=["status", "data_devolucao_real"])


# ---------------------------------------------------------------------------
# ItemLocacao
# ---------------------------------------------------------------------------
class ItemLocacao(models.Model):
    locacao = models.ForeignKey(
        Locacao, on_delete=models.CASCADE, related_name="itens"
    )
    produto = models.ForeignKey(
        Produto, on_delete=models.PROTECT, related_name="itens_locacao"
    )
    valor_aplicado = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Se deixado em branco, é preenchido com o preço padrão do produto.",
    )
    data_devolucao_real_item = models.DateField(null=True, blank=True)
    retornou_lavanderia = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Item da Locação"
        verbose_name_plural = "Itens da Locação"
        indexes = [
            # Suporta a checagem de disponibilidade: filtra rápido por produto
            # e depois junta com Locacao (que já tem índice em status+datas).
            models.Index(fields=["produto"]),
        ]

    def __str__(self):
        return f"{self.produto} (Locação #{self.locacao_id})"

    def save(self, *args, **kwargs):
        eh_novo = self._state.adding
        # Se nenhum valor manual/desconto foi aplicado, usa o preço padrão do produto.
        if self.valor_aplicado is None:
            self.valor_aplicado = self.produto.preco_aluguel_padrao
        super().save(*args, **kwargs)

        if eh_novo:
            Produto.objects.filter(pk=self.produto_id).update(
                total_locacoes=F("total_locacoes") + 1
            )

    @property
    def dias_atraso(self):
        if (
            self.data_devolucao_real_item
            and self.data_devolucao_real_item > self.locacao.data_devolucao_prevista
        ):
            return (
                self.data_devolucao_real_item - self.locacao.data_devolucao_prevista
            ).days
        return 0

    @property
    def multa_calculada(self):
        return self.dias_atraso * self.produto.multa_atraso_diaria

    # -- Disponibilidade -------------------------------------------------
    @classmethod
    def esta_disponivel(cls, produto, data_retirada, data_devolucao_prevista):
        """
        Verifica se um produto está livre para o período informado,
        considerando apenas locações em status 'aberto' (não Cancelada,
        não Devolvida). Locações atrasadas contam como conflito porque a
        peça ainda não voltou fisicamente.
        """
        conflito = cls.objects.filter(
            produto=produto,
            locacao__status__in=Locacao.STATUS_ABERTOS,
            locacao__data_retirada__lte=data_devolucao_prevista,
            locacao__data_devolucao_prevista__gte=data_retirada,
        ).exists()
        return not conflito

    @classmethod
    def datas_reservadas(cls, produto):
        """
        Usado pela tela de consulta de disponibilidade: retorna a lista de
        locações em aberto de um produto, com retirada e devolução prevista.
        Locações atrasadas ficam de fora (a peça só entra em circulação de
        novo quando já está fisicamente de volta na loja).
        """
        status_sem_atrasada = [
            s for s in Locacao.STATUS_ABERTOS if s != Locacao.STATUS_ATRASADA
        ]
        return (
            cls.objects.filter(
                produto=produto,
                locacao__status__in=status_sem_atrasada,
            )
            .select_related("locacao")
            .order_by("locacao__data_retirada")
        )