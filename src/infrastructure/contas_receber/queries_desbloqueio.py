"""Queries read-only expostas por CR p/ o desbloqueio em `clientes` (Fatia 3c — T-CR-045 / D-CR-11).

CR é dono do `Titulo`; `clientes` é dono do `ClienteBloqueio`. No desbloqueio por
quitação (INV-FIN-REATIV-001 / GATE-CLI-6), o consumer de `clientes` precisa de dois
fatos que só CR conhece — sem que o cliente vaze no payload do evento
`contas_receber.pago` (minimização — D-CR-16/19): qual cliente é dono do título pago
e se ainda resta inadimplência vencida em aberto.

Ambas rodam no contexto de tenant corrente (RLS aplica) + filtro `tenant_id` defensivo
(defesa em profundidade — molde do projeto).
"""

from __future__ import annotations

from datetime import date
from uuid import UUID

from src.domain.contas_receber.enums import EstadoTitulo


def cliente_atual_id_do_titulo(*, tenant_id: UUID, titulo_id: UUID) -> UUID | None:
    """Cliente (UUID atual) dono do título. `None` se anonimizado (LGPD) ou inexistente.

    O título carrega `cliente_atual_id` (zerado na anonimização do cliente — ADR-0032).
    `None` → o consumer de desbloqueio faz no-op (sem bloqueio rastreável ao cliente).
    """
    from src.infrastructure.contas_receber.models import Titulo as TituloModel

    cliente_id: UUID | None = (
        TituloModel.objects.filter(tenant_id=tenant_id, id=titulo_id)
        .values_list("cliente_atual_id", flat=True)
        .first()
    )
    return cliente_id


def tem_outra_vencida_em_aberto(*, tenant_id: UUID, cliente_id: UUID) -> bool:
    """`True` se o cliente ainda tem título VENCIDO em aberto (mantém bloqueio — AC-CR-006-2).

    "Vencida em aberto" = `data_vencimento <= hoje` E estado NÃO terminal de quitação
    (`estado NOT IN {pago, cancelado}`). Inclui `parcialmente_pago` deliberadamente: um
    pagamento parcial de título vencido o tira de `vencido`, mas NÃO encerra a dívida —
    desbloquear nesse caso violaria AC-CR-006-2. Como a query roda DEPOIS do commit da
    baixa, o título recém-quitado já saiu de aberto (se total → `pago`, excluído) e não
    conta; se a baixa foi parcial, ele continua aberto e mantém o bloqueio.

    **Débito (P9):** régua SEM grace — espelha o nome `tem_outra_vencida_em_aberto` da
    spec D-CR-11 (lado conservador: não desbloqueia com pendência vencida). O adapter de
    bloqueio (Fatia 3b) aplica grace por perfil; a assimetria grace-bloqueio ×
    sem-grace-desbloqueio fica rastreada para reconciliação no fechamento (T-CR-060).
    """
    from src.infrastructure.contas_receber.models import Titulo as TituloModel

    return (
        TituloModel.objects.filter(
            tenant_id=tenant_id,
            cliente_atual_id=cliente_id,
            data_vencimento__lte=date.today(),
        )
        .exclude(estado__in=(EstadoTitulo.PAGO.value, EstadoTitulo.CANCELADO.value))
        .exists()
    )
