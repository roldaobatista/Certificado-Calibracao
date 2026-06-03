"""Job `verificar_vigencia_acreditacao_perfil_a` — T-SAN-PERFIL-036.

Sprint 3 P5 do saneamento ADR-0067.
AC-SAN-PERFIL-004-8 + S5 plan.md ("verificacao periodica de vigencia").

Itera todos os tenants Perfil A e:
  - Alerta gerente Aferê se acreditacao vence em <=60 dias.
  - Alerta CRITICO se acreditacao ja vencida (predicate `tenant_perfil_e({"A"})`
    ja bloqueia uso, mas alerta operacional e necessario para acao humana).

Defesa contra alegacao de ma-fe da seguradora (S5 plan.md — Lei 4.594/64
art. 22 + CC art. 765): seguradora pode rescindir apolice retroativamente
se houver tenant Perfil A com acreditacao vencida operando sem flag.
Job mensal demonstra processo de verificacao continuo (boa-fe Afere).

NOTA M9 (T-LIC-051 refino): o cache `tenants.acreditacao_vigencia_fim` JA E
populado pelo modulo `licencas-acreditacoes` via `aplicar_evento_cgcre`
(ADR-0079). Este job agora alerta sobre o VENCIMENTO REAL da acreditacao
(precedencia sobre a janela legada de suspensao) alem de:
  - Marca alerta operacional se `acreditacao_suspensa_ate` esta proxima
    de vencer (tenant A legado sem licenca cadastrada — vigencia_fim None).
  - Verifica que perfil A tem `acreditacao_cgcre_numero` preenchido
    (defesa contra estado inconsistente).
Vigencia por escopo CGCRE (grandeza × faixa × procedimento) fica no
read-model do M9; este job usa a vigencia agregada do cache.

Funcao pura: recebe lista de snapshots + `agora` + janelas. Caller
(adapter Django) le DB, chama essa funcao, publica alertas via bus.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from uuid import UUID

# Janela default de aviso antecipado (S5 plan.md = 60 dias).
JANELA_AVISO_DIAS_DEFAULT = 60


@dataclass(frozen=True, slots=True)
class TenantPerfilASnapshot:
    """Snapshot leve do tenant Perfil A pra verificacao de vigencia."""

    tenant_id: UUID
    slug: str
    perfil_regulatorio: str  # esperado "A"
    acreditacao_cgcre_numero: str | None
    acreditacao_suspensa_em: dt.date | None
    acreditacao_suspensa_ate: dt.date | None
    # M9 T-LIC-051 (refino): cache de vigencia da acreditacao CGCRE, agora populado
    # pelo modulo licencas-acreditacoes via `aplicar_evento_cgcre` (ADR-0079). `None`
    # = tenant A legado sem licenca cadastrada (cai no caminho antigo por suspensao).
    acreditacao_vigencia_fim: dt.date | None = None


@dataclass(frozen=True, slots=True)
class AlertaVigenciaAcreditacao:
    """Saida do job — caller publica via bus / notifica gerente."""

    tenant_id: UUID
    tenant_slug: str
    severidade: str  # "AVISO" | "CRITICO" | "INCONSISTENCIA"
    motivo: str
    proxima_acao: str


def verificar_vigencia_acreditacao_perfil_a(
    snapshots: list[TenantPerfilASnapshot],
    *,
    agora: dt.date,
    janela_aviso_dias: int = JANELA_AVISO_DIAS_DEFAULT,
) -> list[AlertaVigenciaAcreditacao]:
    """Verifica vigencia de tenants Perfil A. Retorna lista de alertas.

    Args:
        snapshots: lista de tenants Perfil A do banco.
        agora: data corrente (injetada — testes determinismticos).
        janela_aviso_dias: dias antes do vencimento para emitir AVISO (default 60).

    Returns:
        Lista de alertas (vazia se tudo OK). Caller publica via bus/email.

    Severidades:
        AVISO: suspensao_ate em [agora, agora + 60d] — operador prepara renovacao.
        CRITICO: suspensao_ate < agora — predicate ja bloqueia, mas operacional
                 precisa agir (renovar, rebaixar para B, ou pedir reabertura CGCRE).
        INCONSISTENCIA: perfil A sem acreditacao_cgcre_numero preenchido
                        (estado de bug — historico_perfil tem promocao para A mas
                        coluna nao foi populada). Defesa contra ma-fe seguradora.
    """
    alertas: list[AlertaVigenciaAcreditacao] = []

    for snap in snapshots:
        if snap.perfil_regulatorio != "A":
            continue

        # INCONSISTENCIA — Perfil A sem numero RBC (estado bug)
        if not snap.acreditacao_cgcre_numero:
            alertas.append(
                AlertaVigenciaAcreditacao(
                    tenant_id=snap.tenant_id,
                    tenant_slug=snap.slug,
                    severidade="INCONSISTENCIA",
                    motivo=(
                        f"Tenant {snap.slug} esta marcado como perfil A mas nao "
                        f"tem acreditacao_cgcre_numero preenchido. Estado de bug "
                        f"(possivel resultado de promocao malformada). "
                        f"INV-TENANT-PERFIL-007 quebrada."
                    ),
                    proxima_acao=(
                        "Investigar historico_perfil deste tenant. Se promocao "
                        "para A foi indevida, usar aplicar_evento_cgcre direcao="
                        "correcao_administrativa rebaixando para B. Se foi correta, "
                        "popular acreditacao_cgcre_numero via correcao_administrativa "
                        "(nao via UPDATE direto — bloqueado por hook + trigger)."
                    ),
                )
            )
            continue

        # M9 T-LIC-051 (refino) — vigencia REAL da acreditacao CGCRE (cache populado
        # via aplicar_evento_cgcre / ADR-0079). Fonte de verdade do vencimento; tem
        # precedencia sobre a janela legada de suspensao.
        if snap.acreditacao_vigencia_fim is not None:
            prazo_aviso = agora + dt.timedelta(days=janela_aviso_dias)
            if snap.acreditacao_vigencia_fim < agora:
                alertas.append(
                    AlertaVigenciaAcreditacao(
                        tenant_id=snap.tenant_id,
                        tenant_slug=snap.slug,
                        severidade="CRITICO",
                        motivo=(
                            f"Tenant {snap.slug} (perfil A) tem acreditacao CGCRE com "
                            f"vigencia_fim={snap.acreditacao_vigencia_fim.isoformat()} "
                            f"JA VENCIDA. acreditacao_vigente_para_rbc rebaixa emissao "
                            f"RBC->nao-RBC na data de emissao (INV-CER-CGCRE-VIG-001)."
                        ),
                        proxima_acao=(
                            "Renovar a acreditacao no modulo licencas-acreditacoes "
                            "(renovar_documento sincroniza o cache via "
                            "aplicar_evento_cgcre direcao=renovacao_vigencia_cgcre). "
                            "Se nao houve renovacao CGCRE: rebaixar para B."
                        ),
                    )
                )
                continue
            if agora <= snap.acreditacao_vigencia_fim <= prazo_aviso:
                dias_restantes = (snap.acreditacao_vigencia_fim - agora).days
                alertas.append(
                    AlertaVigenciaAcreditacao(
                        tenant_id=snap.tenant_id,
                        tenant_slug=snap.slug,
                        severidade="AVISO",
                        motivo=(
                            f"Tenant {snap.slug} (perfil A) tem acreditacao CGCRE "
                            f"vencendo em {dias_restantes} dias "
                            f"({snap.acreditacao_vigencia_fim.isoformat()})."
                        ),
                        proxima_acao=(
                            "Iniciar renovacao da acreditacao junto a CGCRE e cadastrar "
                            "a nova vigencia (renovar_documento) antes do vencimento."
                        ),
                    )
                )
                continue

        # Sem janela de suspensao = vigencia plena (modulo licencas-acreditacoes
        # Wave A vai trazer vigencia por escopo; ate la, considera "OK").
        if snap.acreditacao_suspensa_ate is None:
            continue

        # CRITICO — suspensao ja terminou (suspensa_ate < agora) mas tenant
        # continua marcado como A. Caso especial: lab nao reabilitou apos
        # suspensao temporaria. Predicate ja bloqueia, mas operador deve agir.
        if snap.acreditacao_suspensa_ate < agora:
            alertas.append(
                AlertaVigenciaAcreditacao(
                    tenant_id=snap.tenant_id,
                    tenant_slug=snap.slug,
                    severidade="CRITICO",
                    motivo=(
                        f"Tenant {snap.slug} (perfil A) tem suspensao_ate="
                        f"{snap.acreditacao_suspensa_ate.isoformat()} JA VENCIDO. "
                        f"Predicate tenant_perfil_e({{'A'}}) esta bloqueando emissao "
                        f"de certificados RBC. Lab precisa reabilitar com CGCRE OU "
                        f"ser rebaixado formalmente."
                    ),
                    proxima_acao=(
                        "Contatar lab. Se CGCRE reabilitou: usar aplicar_evento_cgcre "
                        "direcao=correcao_administrativa removendo flags suspensao. "
                        "Se nao reabilitou em 90 dias da data prevista: rebaixar para "
                        "B via aplicar_evento_cgcre direcao=cancelamento_cgcre."
                    ),
                )
            )
            continue

        # AVISO — suspensao_ate em [agora, agora + janela_aviso_dias]
        # Vale tambem como aviso de "vigencia geral acabando" enquanto modulo
        # licencas-acreditacoes Wave A nao chega.
        prazo_aviso = agora + dt.timedelta(days=janela_aviso_dias)
        if agora <= snap.acreditacao_suspensa_ate <= prazo_aviso:
            dias_restantes = (snap.acreditacao_suspensa_ate - agora).days
            alertas.append(
                AlertaVigenciaAcreditacao(
                    tenant_id=snap.tenant_id,
                    tenant_slug=snap.slug,
                    severidade="AVISO",
                    motivo=(
                        f"Tenant {snap.slug} (perfil A) tem suspensao_ate em "
                        f"{dias_restantes} dias ({snap.acreditacao_suspensa_ate.isoformat()}). "
                        f"Janela de aviso antecipado ({janela_aviso_dias}d) atingida."
                    ),
                    proxima_acao=(
                        "Contatar lab para confirmar status de reabilitacao CGCRE. "
                        "Se reabilitou: usar aplicar_evento_cgcre direcao="
                        "correcao_administrativa para limpar flags. Se nao "
                        "reabilitou: planejar rebaixamento."
                    ),
                )
            )

    return alertas
