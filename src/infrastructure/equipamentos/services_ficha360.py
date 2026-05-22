"""Service de montagem da ficha 360 do Equipamento (T-EQP-024 + T-EQP-030
+ T-EQP-031 / US-EQP-003 AC-EQP-003-1).

Monta dict pronto pra serializacao DRF — agnostico de HTTP. Util tambem
pra render no Django admin / management commands / drill.

Campos:
- `equipamento`: dados base (id, tag, ns, fabricante, modelo, status,
  cliente_atual_id, localizacao_fisica, criado_em).
- `perfil_no_momento_do_cadastro` (P-EQP-R1 / AC-EQP-003-7): bloco
  `perfil_tenant_snapshot` imutavel — mesmo se o tenant promove
  posteriormente, a ficha mostra o perfil VALIDO no momento.
- `versoes`: lista de `EquipamentoVersao` (campo, motivo, data) — sem
  hashes brutos, sem motivo_detalhe cru.
- `aprovacoes`: lista de `AprovacaoPendenteEquipamentoVersao` ativas.
- `certificados`: porta `query_service.equipamentos_com_cert_vigente`
  retorna bool (Marco 2 stub; Wave A expande lista detalhada).
- `os` (ordens de servico): stub vazio Marco 2 (Wave A).
- `eventos`: ultimos 50 eventos sanitizados do `Auditoria` filtrados
  por `payload_jsonb.equipamento_id`.

NAO faz acesso de log (`AcessoDadosCliente`) — isso e responsabilidade
do viewset (chama ANTES de invocar este service, dentro do mesmo tx).
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from src.infrastructure.audit.models import Auditoria
from src.infrastructure.audit.services import sanitizar_payload_audit
from src.infrastructure.certificados.query_service import tem_emitido
from src.infrastructure.equipamentos.models import (
    AprovacaoPendenteEquipamentoVersao,
    ConsentimentoHistoricoEquipamento,
    Equipamento,
    EquipamentoVersao,
    NivelConsentimentoHistorico,
    StatusAprovacaoVersao,
    TransferenciaEquipamentoAceite,
)

LIMITE_EVENTOS_FICHA = 50

# T-EQP-029 / AC-EQP-003-6 — texto canonico do banner (lista FECHADA,
# nao compõe inline; mudar texto exige revisao do advogado-saas-regulado).
BANNER_HISTORICO_OCULTO_CESSIONARIO = (
    "Historico preservado e confidencial conforme RBC ISO/IEC 17025 "
    "cl. 4.2. Para acessar versoes/eventos anteriores a esta "
    "transferencia, solicite consentimento expresso ao cedente."
)


def _avaliar_filtro_historico_cessionario(
    equipamento: Equipamento,
) -> tuple[str, str, str | None]:
    """T-EQP-029 — determina filtro de historico para cessionario sem
    consentimento.

    Regra:
    - Procura a TransferenciaEquipamentoAceite EFETIVADA mais recente
      do equipamento; se o `cliente_atual_id` bate com a do cessionario
      e existe um `ConsentimentoHistoricoEquipamento` (nao revogado),
      o nivel manda. Senao: trata como `nada` (cessionario sem prova).
    - Equipamento sem historico de transferencia OU cliente_atual ==
      cedente: sem filtro (proprietario original ve tudo).

    Retorna `(nivel_efetivo, banner, transferencia_em_iso)`:
    - `nivel_efetivo`: 'nada' / 'resumo' / 'completo' / 'sem_filtro'.
    - `banner`: texto a exibir ou '' quando sem_filtro.
    - `transferencia_em_iso`: corte temporal (criado_em da
      transferencia efetivada) para filtrar versoes/eventos; None
      quando sem_filtro.
    """
    transferencia = (
        TransferenciaEquipamentoAceite.objects.filter(
            equipamento_id=equipamento.id,
            status="efetivada",
        )
        .order_by("-efetivada_em")
        .first()
    )
    if transferencia is None:
        return ("sem_filtro", "", None)
    if equipamento.cliente_atual_id != transferencia.cessionario_cliente_id:
        # Equipamento ja saiu daquele cessionario (nova transferencia?)
        # ou cliente_atual_id desincronizou. Defesa: tratar sem_filtro.
        return ("sem_filtro", "", None)

    consentimento = (
        ConsentimentoHistoricoEquipamento.objects.filter(
            transferencia_origem_id=transferencia.id,
            revogado_em__isnull=True,
        )
        .order_by("-concedido_em")
        .first()
    )
    if consentimento is None:
        nivel = NivelConsentimentoHistorico.NADA.value
    else:
        nivel = consentimento.nivel

    if nivel == NivelConsentimentoHistorico.COMPLETO.value:
        return ("completo", "", None)

    corte = (
        transferencia.efetivada_em.isoformat()
        if transferencia.efetivada_em
        else transferencia.solicitado_em.isoformat()
    )
    return (nivel, BANNER_HISTORICO_OCULTO_CESSIONARIO, corte)


def construir_ficha_360(
    equipamento: Equipamento,
    *,
    usuario_id: Any = None,  # unused em Marco 2; reservado pra ABAC Wave A
) -> dict[str, Any]:
    """Monta ficha 360 do equipamento.

    Caller responsavel por:
    1. Definir `app.active_tenant_id` (run_in_tenant_context) — RLS
       filtra versoes/aprovacoes/certificados/eventos.
    2. Gravar `AcessoDadosCliente` ANTES (INV-013).
    3. Authz `equipamentos.ficha360` (RequireAuthz no viewset).

    T-EQP-029: filtra historico (versoes + eventos) quando cliente_atual
    e cessionario pos-transferencia sem consentimento (`nada`) ou com
    consentimento parcial (`resumo`). Cessionario com consentimento
    `completo` ve tudo. Equipamento sem historico de transferencia ou
    com cliente_atual igual ao cedente original ve tudo.
    """
    _ = usuario_id  # reservado para ABAC por usuario Wave A
    nivel_filtro, banner_historico, corte_iso = (
        _avaliar_filtro_historico_cessionario(equipamento)
    )

    versoes_qs = EquipamentoVersao.objects.filter(
        equipamento_id=equipamento.id
    )
    # T-EQP-029: nivel `nada` -> versoes anteriores ao corte ocultas.
    if nivel_filtro == NivelConsentimentoHistorico.NADA.value and corte_iso:
        versoes_qs = versoes_qs.filter(criado_em__gte=corte_iso)
    versoes = (
        versoes_qs.order_by("-criado_em")
        .values(
            "id",
            "campo",
            "motivo_mudanca",
            "snapshot_schema_version" if False else "snapshot_jsonb",
            "criado_em",
            "criado_por_id",
        )[:50]
    )
    versoes_dump = [
        {
            "id": str(v["id"]),
            "campo": v["campo"],
            "motivo_mudanca": v["motivo_mudanca"],
            "criado_em": v["criado_em"].isoformat(),
            "criado_por_id": str(v["criado_por_id"]),
        }
        for v in versoes
    ]

    aprovacoes_ativas = (
        AprovacaoPendenteEquipamentoVersao.objects.filter(
            equipamento_id=equipamento.id,
            status=StatusAprovacaoVersao.PENDENTE,
        )
        .order_by("-solicitado_em")
        .values("id", "campo", "motivo_mudanca", "solicitado_em", "sla_vencimento")[:20]
    )
    aprovacoes_dump = [
        {
            "id": str(a["id"]),
            "campo": a["campo"],
            "motivo_mudanca": a["motivo_mudanca"],
            "solicitado_em": a["solicitado_em"].isoformat(),
            "sla_vencimento": a["sla_vencimento"].isoformat(),
        }
        for a in aprovacoes_ativas
    ]

    eventos_qs = Auditoria.objects.filter(
        payload_jsonb__equipamento_id=str(equipamento.id),
    )
    # T-EQP-029: nivel `nada` -> eventos anteriores ao corte ocultos.
    if nivel_filtro == NivelConsentimentoHistorico.NADA.value and corte_iso:
        eventos_qs = eventos_qs.filter(timestamp__gte=corte_iso)
    eventos = (
        eventos_qs.order_by("-timestamp")
        .values("id", "action", "timestamp", "payload_jsonb")[:LIMITE_EVENTOS_FICHA]
    )
    eventos_dump = [
        {
            "id": str(e["id"]),
            "action": e["action"],
            "timestamp": e["timestamp"].isoformat(),
            # Defesa em profundidade: sanitiza payload (mesmo padrao
            # da visao 360 do cliente — CONCERN auditor Seguranca).
            "payload": sanitizar_payload_audit(e["payload_jsonb"]),
        }
        for e in eventos
    ]

    return {
        "equipamento": {
            "id": str(equipamento.id),
            "tenant_id": str(equipamento.tenant_id),
            "tag": equipamento.tag,
            "numero_serie": equipamento.numero_serie,
            "fabricante": equipamento.fabricante,
            "modelo": equipamento.modelo,
            "faixa": equipamento.faixa,
            "classe": equipamento.classe,
            "status": equipamento.status,
            "cliente_atual_id": (
                str(equipamento.cliente_atual_id)
                if equipamento.cliente_atual_id
                else None
            ),
            "localizacao_fisica": equipamento.localizacao_fisica,
            "criado_em": equipamento.criado_em.isoformat(),
        },
        # AC-EQP-003-7 / P-EQP-R1: bloco fixo "Perfil no momento do
        # cadastro" — usa snapshot imutavel mesmo se tenant promoveu
        # depois (via promover_perfil_equipamento_snapshot).
        "perfil_no_momento_do_cadastro": {
            "snapshot": equipamento.perfil_tenant_snapshot,
            "snapshot_schema_version": equipamento.snapshot_schema_version,
        },
        "versoes": versoes_dump,
        "aprovacoes_pendentes": aprovacoes_dump,
        "certificados": {
            "tem_vigente": tem_emitido(equipamento.id),
            # Wave A expande com lista detalhada (numero, emitido_em,
            # rt_signatario_hash, link_pdf). Marco 2 stub apenas
            # bool atende AC-EQP-003-1 mais P-EQP-T3 (anti-oracle:
            # mesmo Escopo B retorna apenas bool).
        },
        "ordens_servico": [],  # Stub Wave A (porta OSQueryService).
        "eventos": eventos_dump,
        # T-EQP-029 / AC-EQP-003-6 — flag de historico filtrado pra UI.
        # `nivel_consentimento_historico` em 'nada'/'resumo'/'completo'/
        # 'sem_filtro' (cedente original ou sem transferencia).
        "aviso_historico_filtrado": {
            "ativo": bool(banner_historico),
            "nivel_consentimento_historico": nivel_filtro,
            "banner": banner_historico,
            "corte_em_iso": corte_iso,
        },
    }


def descrever_finalidade(finalidade: str) -> str:
    """Mapeia finalidade enum -> texto legivel pra response (UI/help)."""
    descricoes = {
        "atendimento_pos_venda": "Atendimento pos-venda do cliente",
        "preparar_orcamento": "Preparar orcamento de calibracao",
        "executar_os": "Executar ordem de servico",
        "emitir_documento_fiscal": "Emitir documento fiscal",
        "auditoria_interna": "Auditoria interna",
        "atendimento_lgpd_titular": "Atendimento LGPD titular",
        "investigacao_incidente": "Investigacao de incidente",
        "cobranca_inadimplencia": "Cobranca inadimplencia",
    }
    return descricoes.get(finalidade, finalidade)


def equipamento_id_from_uuid(valor: str) -> UUID:
    """Helper de coerce — levanta ValueError em malformados."""
    return UUID(str(valor))
