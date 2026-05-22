"""Porta `CertificadoQueryService` — consultas read-only sobre certificados
(stub Marco 2).

ADR-0007 (camada dominio + portas): consumidores que querem saber se
um equipamento tem cert vigente NAO importam Certificado direto. Usam
este service — Wave A pode trocar implementacao (cache, materialized
view, etc) sem quebrar consumidores.

API minima Marco 2:
- `tem_emitido(equipamento_id)` — bool.
- `equipamentos_com_cert_vigente(equipamento_ids)` — set de UUIDs.

Wave A expande com:
- `cert_vigente_de(equipamento_id) -> Certificado | None`
- `historico(equipamento_id) -> list[Certificado]`
"""

from __future__ import annotations

from uuid import UUID

from src.infrastructure.certificados.models import Certificado


def tem_emitido(equipamento_id: UUID) -> bool:
    """True se existe pelo menos 1 certificado vigente (EMITIDO +
    nao revogado) referenciando o equipamento.

    Marco 2 — Wave A pode adicionar cache de 60s se virar hot path.
    Atual: scan no index `ix_cert_eq_status_rev`.
    """
    return Certificado.objects.filter(equipamento_id=equipamento_id).exists()


def equipamentos_com_cert_vigente(equipamento_ids: list[UUID]) -> set[UUID]:
    """Versao batch — uma query SQL pra um conjunto.

    Util pra listagem de equipamentos onde queremos marcar quais sao
    editaveis sem violar INV-025. Wave A pode otimizar com window
    function se >10k equipamentos por listagem.
    """
    return set(
        Certificado.objects.filter(equipamento_id__in=equipamento_ids)
        .values_list("equipamento_id", flat=True)
        .distinct()
    )
