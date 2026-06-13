"""Use cases de cadastro, edição e desligamento de colaboradores (T-COL-030).

cadastrar_colaborador  — CPF VO + dedup→409; grava base legal por vínculo.
editar_colaborador     — CPF imutável; atualiza demais campos.
desligar_colaborador   — cascade revoga papéis + publica Colaborador.Desligado
                         via outbox NA MESMA transação (D-COL-10 / TL-COL-13);
                         idempotente por chave estável colaborador_id:data_desligamento.

Refs: AC-COL-01/06/06-2; D-COL-3/8/10/13; INV-COL-CPF/-DESLIGAMENTO-CASCADE;
      ADV-COL-01; TL-COL-02/13.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from src.domain.rh_frota_qualidade.colaboradores.base_legal import (
    BASE_LEGAL_POR_VINCULO_E_CATEGORIA,
)
from src.domain.rh_frota_qualidade.colaboradores.entities import Colaborador
from src.domain.rh_frota_qualidade.colaboradores.enums import (
    PapelColaborador,
    Vinculo,
)
from src.domain.rh_frota_qualidade.colaboradores.erros import (
    ColaboradorInativo,
    DuplicateCpf,
)
from src.domain.rh_frota_qualidade.colaboradores.regras import (
    montar_payload_desligamento,
    validar_comissao,
)
from src.domain.rh_frota_qualidade.colaboradores.repository import (
    ColaboradorRepository,
    PapelRepository,
)
from src.domain.shared.value_objects import CPF

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ComandoCadastrarColaborador:
    """Input do use case de cadastro."""

    tenant_id: UUID
    nome: str
    cpf_value: str
    email: str
    telefone: str
    vinculo: Vinculo
    data_admissao: date
    comissao_default_pct: Decimal
    observacao: str = ""
    usuario_id: UUID | None = None


@dataclass(frozen=True)
class ComandoEditarColaborador:
    """Input do use case de edição. CPF não pode ser alterado (D-COL-2)."""

    tenant_id: UUID
    colaborador_id: UUID
    nome: str | None = None
    email: str | None = None
    telefone: str | None = None
    vinculo: Vinculo | None = None
    data_admissao: date | None = None
    comissao_default_pct: Decimal | None = None
    observacao: str | None = None
    usuario_id: UUID | None = None


@dataclass(frozen=True)
class ComandoDesligarColaborador:
    """Input do use case de desligamento."""

    tenant_id: UUID
    colaborador_id: UUID
    data_desligamento: date
    motivo_desligamento: str
    # Para eventos: quem está desligando
    ator_id: UUID | None = None


def cadastrar_colaborador(
    cmd: ComandoCadastrarColaborador,
    *,
    repo_colab: ColaboradorRepository,
) -> UUID:
    """Cadastra colaborador novo (AC-COL-01 / INV-COL-CPF).

    Valida CPF via VO; dedup por CPF no tenant → 409 DUPLICATE_CPF.
    Grava base legal por vínculo (ADV-COL-01 / D-COL-6); o mapa mora no domínio.

    Returns:
        UUID do colaborador criado.
    Raises:
        CpfInvalido: CPF inválido (VO).
        DuplicateCpf: CPF já ativo no tenant.
        ComissaoForaDaFaixa: comissão fora de 0..100.
    """
    cpf = CPF(cmd.cpf_value)  # Levanta CpfInvalido se inválido
    validar_comissao(comissao_pct=cmd.comissao_default_pct)

    # Dedup CPF: UNIQUE parcial no banco + verificação antecipada no use case
    existente = repo_colab.obter_por_cpf(
        tenant_id=cmd.tenant_id,
        cpf_value=cpf.value,
    )
    if existente is not None:
        raise DuplicateCpf(
            f"CPF {cpf.formatado()} já cadastrado para colaborador ativo no tenant "
            "(INV-COL-CPF). Re-cadastro permitido somente após soft-delete."
        )

    # Base legal por vínculo disponível em domínio (ADV-COL-01)
    # Extrai base legal para categoria "identificacao" (principal) como log de referência.
    base_legal_identificacao = BASE_LEGAL_POR_VINCULO_E_CATEGORIA.get(
        (cmd.vinculo, "identificacao"), ""
    )
    logger.debug(
        "cadastrar_colaborador base_legal_vinculo",
        extra={
            "vinculo": cmd.vinculo.value,
            "base_legal_identificacao": base_legal_identificacao,
        },
    )

    colaborador_id = uuid4()
    colaborador = Colaborador(
        id=colaborador_id,
        tenant_id=cmd.tenant_id,
        nome=cmd.nome,
        cpf=cpf,
        email=cmd.email,
        telefone=cmd.telefone,
        vinculo=cmd.vinculo,
        data_admissao=cmd.data_admissao,
        comissao_default_pct=cmd.comissao_default_pct,
        observacao=cmd.observacao,
        usuario_id=cmd.usuario_id,
    )
    repo_colab.salvar(colaborador)

    logger.info(
        "colaborador cadastrado",
        extra={
            "colaborador_id": str(colaborador_id),
            "tenant_id": str(cmd.tenant_id),
            "vinculo": cmd.vinculo.value,
        },
    )
    return colaborador_id


def editar_colaborador(
    cmd: ComandoEditarColaborador,
    *,
    repo_colab: ColaboradorRepository,
) -> None:
    """Edita colaborador (AC-COL-01 / D-COL-2: CPF imutável pós-criação).

    Aplica somente campos fornecidos (partial update). CPF NÃO pode ser alterado.

    Raises:
        ColaboradorInativo: colaborador desligado ou soft-deletado.
        ComissaoForaDaFaixa: comissão fora de 0..100.
    """
    colab = repo_colab.obter(tenant_id=cmd.tenant_id, colaborador_id=cmd.colaborador_id)
    if colab is None or not colab.ativo:
        raise ColaboradorInativo(
            f"Colaborador {cmd.colaborador_id} está inativo ou não existe "
            "(D-COL-3 / INV-COLABORADOR-INATIVO)."
        )

    if cmd.comissao_default_pct is not None:
        validar_comissao(comissao_pct=cmd.comissao_default_pct)

    colaborador_atualizado = Colaborador(
        id=colab.id,
        tenant_id=colab.tenant_id,
        nome=cmd.nome if cmd.nome is not None else colab.nome,
        cpf=colab.cpf,  # CPF IMUTÁVEL (D-COL-2)
        email=cmd.email if cmd.email is not None else colab.email,
        telefone=cmd.telefone if cmd.telefone is not None else colab.telefone,
        vinculo=cmd.vinculo if cmd.vinculo is not None else colab.vinculo,
        data_admissao=cmd.data_admissao if cmd.data_admissao is not None else colab.data_admissao,
        comissao_default_pct=(
            cmd.comissao_default_pct
            if cmd.comissao_default_pct is not None
            else colab.comissao_default_pct
        ),
        observacao=cmd.observacao if cmd.observacao is not None else colab.observacao,
        usuario_id=cmd.usuario_id if cmd.usuario_id is not None else colab.usuario_id,
        foto_storage_key=colab.foto_storage_key,
        data_desligamento=colab.data_desligamento,
        motivo_desligamento=colab.motivo_desligamento,
        deletado_em=colab.deletado_em,
        deletado_por_usuario_id=colab.deletado_por_usuario_id,
        deletado_motivo=colab.deletado_motivo,
    )
    repo_colab.salvar(colaborador_atualizado)


def desligar_colaborador(
    cmd: ComandoDesligarColaborador,
    *,
    repo_colab: ColaboradorRepository,
    repo_papel: PapelRepository,
    tenant_id_para_evento: UUID,
) -> None:
    """Desliga colaborador (AC-COL-06 / D-COL-10 / INV-COL-DESLIGAMENTO-CASCADE).

    Dentro de transaction.atomic (garantida pelo caller / view):
      1. Verifica que colaborador está ativo (409 se já desligado).
      2. Registra data_desligamento + motivo.
      3. Revoga todos os papéis ativos (INV-COL-DESLIGAMENTO-CASCADE).
      4. Publica `colaborador.desligado` via outbox=True NA MESMA transação (D-COL-10).
         Chave idempotente estável: colaborador_id:data_desligamento (TL-COL-13).

    Idempotente: 2ª chamada com mesma (colaborador_id, data_desligamento) encontra
    colaborador já desligado → 409 ColaboradorInativo. O outbox tem UNIQUE
    (causation_id, acao) garantido pelo event_helpers — sem evento duplicado.

    Raises:
        ColaboradorInativo: colaborador já desligado ou soft-deletado.
    """
    colab = repo_colab.obter(tenant_id=cmd.tenant_id, colaborador_id=cmd.colaborador_id)
    if colab is None or not colab.ativo:
        raise ColaboradorInativo(
            f"Colaborador {cmd.colaborador_id} já está inativo ou não existe "
            "(D-COL-3). Desligamento idempotente: segunda chamada retorna 409."
        )

    # Verifica se era signatário (para payload do evento)
    papeis = repo_papel.listar_por_colaborador(
        tenant_id=cmd.tenant_id,
        colaborador_id=cmd.colaborador_id,
    )
    papeis_ativos = [
        p for p in papeis
        if p.revogado_em is None
        and (p.data_fim is None or p.data_fim >= cmd.data_desligamento)
    ]
    is_rt_signatario = any(p.papel == PapelColaborador.SIGNATARIO for p in papeis_ativos)
    tipos_servico_assinava: list[str] = []  # stub — preenchido por consumer RT

    momento_revogacao = datetime.combine(cmd.data_desligamento, datetime.min.time()).replace(
        tzinfo=UTC
    )

    # 1. Registrar desligamento no banco
    repo_colab.desligar(
        tenant_id=cmd.tenant_id,
        colaborador_id=cmd.colaborador_id,
        data_desligamento=cmd.data_desligamento,
        motivo_desligamento=cmd.motivo_desligamento,
    )

    # 2. Cascade: revogar todos os papéis ativos
    n_revogados = repo_papel.revogar_todos_ativos(
        tenant_id=cmd.tenant_id,
        colaborador_id=cmd.colaborador_id,
        revogado_em=momento_revogacao,
    )

    # 3. Publicar evento via outbox (D-COL-10 / TL-COL-02)
    # Import local para evitar ciclo infra → application
    from src.infrastructure.audit.event_helpers import publicar_evento
    from src.infrastructure.calibracao.lgpd import (
        derivar_hash_texto_canonicalizado,
    )

    motivo_hash = derivar_hash_texto_canonicalizado(
        texto=cmd.motivo_desligamento,
        tenant_id=tenant_id_para_evento,
    )

    payload_v9 = montar_payload_desligamento(
        colaborador_id=cmd.colaborador_id,
        data_desligamento=cmd.data_desligamento,
        is_rt_signatario=is_rt_signatario,
        tipos_servico_assinava=tipos_servico_assinava,
    )
    # Enriquece payload com motivo_hash (D-COL-8 / ADV-COL-06)
    payload_v9 = {**payload_v9, "motivo_hash": motivo_hash}

    # Chave idempotente estável = colaborador_id:data_desligamento (TL-COL-13)
    chave_idempotente = f"{cmd.colaborador_id}:{cmd.data_desligamento}"
    import uuid as _uuid
    causation_id = _uuid.uuid5(
        _uuid.NAMESPACE_URL,
        f"colaborador.desligado:{chave_idempotente}",
    )

    publicar_evento(
        acao="colaborador.desligado",
        payload=payload_v9,
        causation_id=causation_id,
        tenant_id=tenant_id_para_evento,
        usuario_id=cmd.ator_id,
        resource_summary=f"colaborador:{cmd.colaborador_id}",
        outbox=True,
        cadeia=True,
    )

    logger.info(
        "colaborador desligado",
        extra={
            "colaborador_id": str(cmd.colaborador_id),
            "tenant_id": str(cmd.tenant_id),
            "n_papeis_revogados": n_revogados,
            "is_rt_signatario": is_rt_signatario,
        },
    )
