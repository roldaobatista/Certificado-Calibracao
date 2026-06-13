"""Regras de domínio puro do módulo `colaboradores` (T-COL-013).

Funções PURAS (sem I/O, sem Django, sem banco). Todas as decisões de negócio
que envolvem colaboradores vivem aqui:

  pode_atribuir_signatario  — valida identidade + escopo + perfil do tenant.
  validar_dono_unico        — garante unicidade de DONO ativo por tenant.
  pendencia_cnh_motorista   — sinaliza pendência de CNH (sem levantar erro — R-COL-1).
  coerencia_documento_vinculo — CTPS incompatível com PJ/TERCEIRIZADO.
  derivar_ativo             — `ativo` a partir de desligamento + soft-delete.
  cascade_revoga_papeis     — revoga todos os papéis ativos de um colaborador.
  montar_payload_desligamento — payload v9 para evento `Colaborador.Desligado`.

Refs: D-COL-10/11/13; INV-COL-SIGNATARIO-IDENTIDADE/-ESCOPO/-DONO-UNICO;
      R-COL-1; TL-COL-01/11/13.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from .entities import PapelColaboradorAtribuido
from .enums import TipoDocumento, Vinculo
from .erros import (
    ComissaoForaDaFaixa,
    DonoJaExiste,
    SignatarioRtNaoCasa,
    SignatarioSemEscopo,
    SignatarioSemUsuario,
)

# ---------------------------------------------------------------------------
# Constantes de validação
# ---------------------------------------------------------------------------

_VINCULOS_SEM_CTPS: frozenset[Vinculo] = frozenset({Vinculo.PJ, Vinculo.TERCEIRIZADO})

_COMISSAO_MIN = Decimal("0")
_COMISSAO_MAX = Decimal("100")


# ---------------------------------------------------------------------------
# Regras públicas
# ---------------------------------------------------------------------------


def pode_atribuir_signatario(
    *,
    usuario_id: UUID | None,
    rt_casa: bool,
    escopo_vigente: bool,
    perfil_tenant: str,
) -> None:
    """Valida se o colaborador pode receber o papel SIGNATARIO (D-COL-11).

    Levanta exceção se qualquer condição falhar:
      1. `usuario_id` deve ser não-None (D-COL-2 / INV-COL-SIGNATARIO-IDENTIDADE).
      2. `rt_casa` → RTCompetencia vigente casa com `colaborador.usuario_id`
         (INV-COL-SIGNATARIO-IDENTIDADE — casa a PESSOA, não só "FK RT existe").
      3. `escopo_vigente` → escopo da RTCompetencia abrange a data de atribuição
         (INV-COL-SIGNATARIO-ESCOPO / INV-003).

    `perfil_tenant` controla o nível de bloqueio:
      'A' → bloqueio HARD (levanta exceção em todos os casos).
      'B'/'C'/'D' → configurável (Wave B/C — por ora também bloqueia; placeholder
                   para afrouxamento futuro via feature flag ADR-0006).

    Args:
      usuario_id:     UUID do usuário associado ao colaborador (ou None).
      rt_casa:        True se RTCompetencia vigente tem mesmo `usuario_id`.
      escopo_vigente: True se escopo do RT abrange a data de atribuição.
      perfil_tenant:  Perfil regulatório do tenant ('A'/'B'/'C'/'D' — ADR-0067).

    Raises:
      SignatarioSemUsuario: colaborador sem `usuario_id`.
      SignatarioRtNaoCasa: RTCompetencia não casa com `usuario_id`.
      SignatarioSemEscopo: escopo do RT não vigente na data.
    """
    # Bloqueio #1 — identidade: colaborador DEVE ter login associado
    if usuario_id is None:
        raise SignatarioSemUsuario(
            "SIGNATARIO exige usuario_id não-nulo " "(INV-COL-SIGNATARIO-IDENTIDADE / D-COL-11)."
        )

    # Bloqueio #2 — RTCompetencia deve casar com o mesmo usuario_id
    if not rt_casa:
        raise SignatarioRtNaoCasa(
            "RTCompetencia vigente não casa com colaborador.usuario_id "
            "(INV-COL-SIGNATARIO-IDENTIDADE / D-COL-11). "
            "A verdade probatória mora no RT (WORM), não no colaborador."
        )

    # Bloqueio #3 — escopo vigente na data de atribuição (INV-003)
    # Por ora bloqueio HARD para todos os perfis (perfil A sempre; B/C/D
    # configurável via feature flag em Wave B — GATE-COL-PERFIL-MATRIZ).
    if not escopo_vigente:
        raise SignatarioSemEscopo(
            f"Escopo do RTCompetencia não vigente na data de atribuição "
            f"(INV-COL-SIGNATARIO-ESCOPO / perfil_tenant={perfil_tenant!r}). "
            "Bloqueio HARD perfil A; B/C/D: GATE-COL-PERFIL-MATRIZ."
        )


def validar_dono_unico(*, dono_ja_existe: bool) -> None:
    """Valida que não existe DONO ativo para o tenant (INV-COL-DONO-UNICO).

    Partial unique no banco garante no nível de persistência (D-COL-4).
    Esta função é a regra de domínio puro que precede o advisory lock
    (ADR-0065 / TL-COL-11).

    Args:
      dono_ja_existe: True se já existe papel DONO ativo (data_fim IS NULL
                      AND revogado_em IS NULL) para o tenant.

    Raises:
      DonoJaExiste: quando já existe um DONO ativo no tenant.
    """
    if dono_ja_existe:
        raise DonoJaExiste(
            "Já existe um colaborador com papel DONO ativo neste tenant "
            "(INV-COL-DONO-UNICO). Revogar o DONO atual antes de atribuir novo."
        )


def pendencia_cnh_motorista(*, tem_cnh: bool) -> bool:
    """Determina se há pendência de CNH para um MOTORISTA_UMC (R-COL-1).

    NÃO levanta exceção (R-COL-1: salvar com pendência, sem erro no cadastro).
    O bloqueio real acontece na alocação (frota/agenda), fora desta frente.

    Args:
      tem_cnh: True se o colaborador possui CNH com validade cadastrada.

    Returns:
      True se há pendência (sem CNH = pendência); False se CNH presente.
    """
    return not tem_cnh


def coerencia_documento_vinculo(
    *,
    tipo: TipoDocumento,
    vinculo: Vinculo,
) -> bool:
    """Verifica coerência entre tipo de documento e vínculo empregatício.

    CTPS é incompatível com PJ e TERCEIRIZADO (minimização art. 6º III LGPD
    / INV-COL-DOC-VINCULO / ADV-COL-01). Retorna False como ALERTA (não 422).

    Args:
      tipo:    Tipo do documento sendo anexado.
      vinculo: Vínculo empregatício do colaborador.

    Returns:
      True se o documento é coerente com o vínculo; False = alerta de
      incompatibilidade (use case deve registrar aviso, não bloquear).
    """
    if tipo == TipoDocumento.CTPS and vinculo in _VINCULOS_SEM_CTPS:
        return False
    return True


def derivar_ativo(
    *,
    data_desligamento: date | None,
    deletado_em: datetime | None,
) -> bool:
    """Deriva o estado `ativo` do colaborador (D-COL-3 / spec §4).

    Colaborador é ativo se não foi desligado (negócio) nem soft-deletado (correção).

    Args:
      data_desligamento: data de desligamento de negócio; None = não desligado.
      deletado_em:       timestamp de soft-delete; None = não deletado.

    Returns:
      True se ativo; False caso contrário.
    """
    return data_desligamento is None and deletado_em is None


def cascade_revoga_papeis(
    *,
    papeis: list[PapelColaboradorAtribuido],
    momento: datetime,
) -> list[PapelColaboradorAtribuido]:
    """Revoga todos os papéis ativos de um colaborador no momento dado.

    Chamada pelo use case de desligamento: data_desligamento → revoga papéis
    (INV-COL-DESLIGAMENTO-CASCADE / D-COL-3). Revogação seta `revogado_em`,
    nunca deleta a linha (audit).

    Papéis já revogados (revogado_em IS NOT NULL) ou com data_fim no passado
    são ignorados (não modificados).

    Args:
      papeis:  Lista de todos os PapelColaboradorAtribuido do colaborador.
      momento: Datetime de referência para a revogação (= data_desligamento).

    Returns:
      Nova lista de PapelColaboradorAtribuido com os ativos revogados
      (frozen dataclass → retorna novos objetos).
    """
    resultado: list[PapelColaboradorAtribuido] = []
    for papel in papeis:
        # Já revogado → mantém sem alteração
        if papel.revogado_em is not None:
            resultado.append(papel)
            continue
        # Vigência encerrada (data_fim no passado em relação ao momento) → mantém
        if papel.data_fim is not None and papel.data_fim < momento.date():
            resultado.append(papel)
            continue
        # Ativo → revoga agora
        resultado.append(
            PapelColaboradorAtribuido(
                id=papel.id,
                colaborador_id=papel.colaborador_id,
                papel=papel.papel,
                data_inicio=papel.data_inicio,
                data_fim=papel.data_fim,
                revogado_em=momento,
                responsabilidade_tecnica_id=papel.responsabilidade_tecnica_id,
                pendencia_cnh=papel.pendencia_cnh,
            )
        )
    return resultado


def montar_payload_desligamento(
    *,
    colaborador_id: UUID,
    data_desligamento: date,
    is_rt_signatario: bool,
    tipos_servico_assinava: list[str],
) -> dict[str, object]:
    """Monta payload v9 do evento `Colaborador.Desligado` (D-COL-10 / TL-COL-13).

    Payload completo para o outbox transacional (outbox=True). Os 6 consumers
    (INV-INT-011) plugam handlers depois sem retrofit do publisher.

    `comissoes_pendentes_count` é stub=0 até GATE-COL-COMISSAO-COUNT (módulo
    `comissoes` ainda inexistente — D-COL-10).

    `chave_idempotente` estável → deduplicação pelos consumers
    (TL-COL-13 / ADR-0033): f"{colaborador_id}:{data_desligamento}".

    Args:
      colaborador_id:         UUID do colaborador desligado.
      data_desligamento:      Data efetiva do desligamento.
      is_rt_signatario:       True se o colaborador tinha papel SIGNATARIO ativo.
      tipos_servico_assinava: Lista de tipos de serviço que assinava (via RT).

    Returns:
      dict com payload v9 completo (JSON-serializable via str(UUID) e str(date)).
    """
    chave_idempotente = f"{colaborador_id}:{data_desligamento}"
    return {
        "colaborador_id": str(colaborador_id),
        "is_rt_signatario": is_rt_signatario,
        "tipos_servico_assinava": tipos_servico_assinava,
        "comissoes_pendentes_count": 0,  # stub — GATE-COL-COMISSAO-COUNT
        "chave_idempotente": chave_idempotente,
    }


def validar_comissao(*, comissao_pct: Decimal) -> None:
    """Valida faixa de comissão default (D-COL-9 / spec §4).

    CHECK 0..100 no banco (Fatia 1b); esta função é a regra de domínio
    que o use case aplica antes de persistir.

    Args:
      comissao_pct: Percentual de comissão default (Decimal).

    Raises:
      ComissaoForaDaFaixa: quando fora do intervalo [0, 100].
    """
    if comissao_pct < _COMISSAO_MIN or comissao_pct > _COMISSAO_MAX:
        raise ComissaoForaDaFaixa(
            f"comissao_default_pct deve estar em 0..100 (veio {comissao_pct}) "
            "— D-COL-9 / CHECK 0..100."
        )


def validar_catalogo_xor_livre(
    *,
    catalogo_id: UUID | None,
    descricao_livre: str | None,
) -> None:
    """Valida que Habilidade tem catalogo_id XOR descricao_livre (D-COL-5).

    Exatamente um deve ser não-None (CHECK na migration / spec §4).

    Args:
      catalogo_id:     UUID do catálogo (ou None).
      descricao_livre: Descrição livre (ou None).

    Raises:
      ValueError: quando ambos são None ou ambos são não-None.
    """
    tem_catalogo = catalogo_id is not None
    tem_livre = descricao_livre is not None and descricao_livre.strip() != ""
    if tem_catalogo == tem_livre:
        raise ValueError(
            "Habilidade exige catalogo_id XOR descricao_livre "
            "(exatamente um deve ser preenchido — D-COL-5)."
        )
