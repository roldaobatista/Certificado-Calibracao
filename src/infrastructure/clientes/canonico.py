"""Identidade canônica de Cliente (INV-CLI-001 / T-CLI-103).

Implementa AC-CLI-002-5 + AC-CLI-005-3 da spec do Marco 1: dado um
`cliente_id` que pode ter sido mesclado (perdedor → vencedor → vencedor...),
resolve qual cliente VIVO representa esse identificador hoje.

Estratégia:

- `Cliente.cliente_canonico_id` aponta o vencedor IMEDIATO da última
  mesclagem (default = próprio `id` quando nunca mesclado).
- `resolver_cliente_canonico` percorre `cliente_canonico_id` seguindo a
  cadeia até encontrar um cliente vivo (`deletado_em IS NULL`).
- Cap = 10 hops; ciclo ou cadeia maior dispara
  `IdentidadeCanonicaCircular` (fail-loud + alerta P1 — corretora §A
  P-CLI-S2; defesa em profundidade contra bug que poderia mascarar perda
  de rastreabilidade ISO 17025 §8.4).
- Materialização preguiçosa (path compression): se hops > 1, o registro
  consultado tem seu `cliente_canonico_id` atualizado direto pro vencedor
  final na mesma transação — próxima leitura é O(1). Decidido com
  tech-lead em P2 (P-CLI-T1 AJUSTADO).

Premissas:

- Função opera no contexto de tenant ativo (RLS já filtra). Cliente
  resolvido pertence ao mesmo tenant que o consultado.
- `Cliente.objects` usa `ClienteAtivosManager` (filtra deletados);
  `Cliente.all_objects` enxerga deletados — necessário para seguir cadeia
  via perdedor soft-deleted.
"""

from __future__ import annotations

from uuid import UUID

from django.db import transaction

CAP_HOPS = 10


class IdentidadeCanonicaCircular(RuntimeError):
    """Cadeia canônica supera CAP_HOPS ou contém ciclo — bug de mesclagem."""


def resolver_cliente_canonico(cliente_id: UUID, *, cap: int = CAP_HOPS) -> UUID:
    """Resolve o cliente vivo que representa `cliente_id` hoje.

    - Retorna o próprio `cliente_id` se nunca mesclado.
    - Segue `cliente_canonico_id` até achar um cliente vivo
      (`deletado_em IS NULL`). Path compression aplicada se hops > 1.
    - `IdentidadeCanonicaCircular` se cap excedido ou ciclo (mesmo id
      visto duas vezes).

    Esta função NÃO valida que o resultado pertence ao tenant ativo —
    RLS faz isso ao consultar `Cliente.all_objects`. Se o id consultado
    pertencer a outro tenant, RLS retorna 0 linhas e levanta
    `Cliente.DoesNotExist`.
    """
    # importacao local evita ciclo de import no app loading
    from .models import Cliente

    visitados: set[UUID] = set()
    cliente_atual_id = cliente_id
    inicio = cliente_id

    for _ in range(cap):
        if cliente_atual_id in visitados:
            raise IdentidadeCanonicaCircular(
                f"Ciclo na cadeia canonica iniciando em {inicio}: revisitou {cliente_atual_id}"
            )
        visitados.add(cliente_atual_id)

        cliente = Cliente.all_objects.only("id", "cliente_canonico_id", "deletado_em").get(
            id=cliente_atual_id
        )

        # Caso base: cliente vivo apontando pra si mesmo = canonico.
        if cliente.cliente_canonico_id == cliente.id and cliente.deletado_em is None:
            # path compression: se cap > 1 hops, atualiza o id original
            if cliente_atual_id != inicio:
                _comprimir_cadeia(inicio_id=inicio, vencedor_final_id=cliente.id)
            return cliente.id

        # Soft-deleted apontando pra si mesmo (não deveria acontecer fora
        # de bug, mas tratamos): considera órfão, retorna vencedor parcial.
        if cliente.cliente_canonico_id == cliente.id and cliente.deletado_em is not None:
            return cliente.id

        # Caminha
        cliente_atual_id = cliente.cliente_canonico_id

    raise IdentidadeCanonicaCircular(
        f"Cadeia canonica > {cap} hops iniciando em {inicio} — alerta P1"
    )


def _comprimir_cadeia(*, inicio_id: UUID, vencedor_final_id: UUID) -> None:
    """Path compression: aponta `inicio_id.cliente_canonico_id` direto pro
    vencedor final, na mesma transação. Idempotente (UPDATE só efetua se
    o valor mudou).
    """
    from .models import Cliente

    with transaction.atomic():
        Cliente.all_objects.filter(id=inicio_id).exclude(
            cliente_canonico_id=vencedor_final_id
        ).update(cliente_canonico_id=vencedor_final_id)
