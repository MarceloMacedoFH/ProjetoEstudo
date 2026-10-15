from datetime import datetime

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from locacoes.models import Locacao


class Command(BaseCommand):
    help = (
        "Marca como 'Atrasada' as locações retiradas cuja devolução prevista já passou "
        "e que ainda têm peças não devolvidas. Rode uma vez por dia (agendador de tarefas)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--data",
            help="Data de referência no formato AAAA-MM-DD (padrão: hoje). Útil para testes.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Só lista as locações que seriam marcadas, sem alterar nada.",
        )

    def handle(self, *args, **options):
        if options["data"]:
            try:
                hoje = datetime.strptime(options["data"], "%Y-%m-%d").date()
            except ValueError:
                raise CommandError("Data inválida. Use o formato AAAA-MM-DD.")
        else:
            hoje = timezone.localdate()

        candidatas = list(
            Locacao.objects.filter(
                status=Locacao.STATUS_RETIRADA,
                data_devolucao_prevista__lt=hoje,
                itens__data_devolucao_real_item__isnull=True,
            )
            .select_related("cliente")
            .distinct()
        )

        for locacao in candidatas:
            if options["dry_run"]:
                self.stdout.write(
                    f"[simulação] Locação #{locacao.pk} ({locacao.cliente}) "
                    f"venceu em {locacao.data_devolucao_prevista:%d/%m/%Y}"
                )
            else:
                locacao.atualizar_status_por_atraso(hoje)

        verbo = "seriam marcadas" if options["dry_run"] else "marcadas"
        self.stdout.write(
            self.style.SUCCESS(f"{len(candidatas)} locação(ões) {verbo} como atrasada(s) em {hoje:%d/%m/%Y}.")
        )
