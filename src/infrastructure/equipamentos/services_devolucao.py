"""Service de devolucao de equipamento (T-EQP-051 / US-EQP-006
AC-EQP-006-4 / ISO 17025 cl. 7.4.5).

Orquestra o encerramento do ciclo do laboratorio:
1. Valida que o recebimento esta em `status_fluxo_lab=aguardando_devolucao`
   — defesa em camadas com trigger PG `transicao_status_fluxo_lab`
   (que tambem bloqueia transicoes invalidas).
2. Valida `condicao_visual_devolucao` em enum.
3. Valida que a foto foi enviada (Marco 2 dogfooding: obrigatoria
   sempre; Wave A diferencia por perfil).
4. Calcula `termo_aceite_hash` = HMAC-SHA256 salt-tenant de
   `{texto_termo|usuario_id|ip_hash|aceite_em_iso}` (prova
   anti-adulteracao).
5. Cria `EquipamentoDevolucao` (1:1 com recebimento).
6. Transiciona `recebimento.status_fluxo_lab` -> `devolvido`.
7. Atualiza `Equipamento.status` -> `ativo` (sai de `em_calibracao_lab`).
8. Publica `equipamento.devolvido` (payload sanitizado com
   `foto_sha256` + `termo_aceite_hash` — NUNCA texto cru).

Defesas:
- `EquipamentoDevolucao` imutavel pos-INSERT (trigger PG).
- `EquipamentoRecebimento.foto_sha256` da devolucao tambem imutavel
  (trigger T-EQP-058 aplica nos novos campos? Nao — esses campos sao
  da TABELA `equipamentos_devolucao`. Imutabilidade total via trigger
  `devolucao_imutavel_trg`).
- OneToOne com recebimento garante 1 devolucao por recebimento
  (DB-level).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from django.db import IntegrityError, ProgrammingError, transaction

from src.infrastructure.audit.event_helpers import publicar_evento
from src.infrastructure.audit.services import hashear_pii_com_salt_tenant
from src.infrastructure.equipamentos.models import (
    CondicaoVisualChegada,
    Equipamento,
    EquipamentoDevolucao,
    EquipamentoRecebimento,
    EquipamentoStatus,
    StatusFluxoLab,
)
from src.infrastructure.equipamentos.services_foto_storage import (
    FotoInvalida,
    preparar_foto,
)
from src.infrastructure.equipamentos.validators import (
    TEXTO_TERMO_DEVOLUCAO_VERSAO_CANONICA,
    texto_termo_devolucao,
)


class DevolucaoInvalida(Exception):
    """Base de erros do service de devolucao."""


class StatusFluxoLabNaoAguardando(DevolucaoInvalida):
    """`recebimento.status_fluxo_lab != 'aguardando_devolucao'`."""


class DevolucaoDuplicada(DevolucaoInvalida):
    """Recebimento ja tem devolucao gravada (OneToOne)."""


class CondicaoDevolucaoInvalida(DevolucaoInvalida):
    """`condicao_visual_devolucao` fora do enum."""


class FotoObrigatoria(DevolucaoInvalida):
    """Marco 2 dogfooding: foto obrigatoria sempre."""


class TermoVersaoInvalida(DevolucaoInvalida):
    """Versao do termo nao reconhecida em Marco 2."""


@dataclass(frozen=True)
class DadosDevolucao:
    condicao_visual_devolucao: str
    foto_bytes: bytes
    foto_mime_type: str
    termo_versao_id: str = TEXTO_TERMO_DEVOLUCAO_VERSAO_CANONICA
    ip_hash: str = ""


@dataclass(frozen=True)
class ResultadoDevolucao:
    devolucao: EquipamentoDevolucao
    foto_storage_key: str
    foto_sha256: str
    termo_aceite_hash: str
    cadeia_linha_id: UUID
    outbox_enfileirado: bool


def devolver_equipamento(
    *,
    tenant_id: UUID,
    equipamento: Equipamento,
    recebimento: EquipamentoRecebimento,
    devolvido_por_id: UUID,
    dados: DadosDevolucao,
    causation_id: UUID | None = None,
) -> ResultadoDevolucao:
    """Encerra o ciclo de manuseio: cria devolucao + transiciona
    `recebimento.status_fluxo_lab` para `devolvido` + atualiza
    `Equipamento.status` para `ativo`.

    Pre-condicoes (fail-fast):
    - `recebimento.status_fluxo_lab == 'aguardando_devolucao'`.
    - `recebimento` nao tem devolucao previa (OneToOne).
    - `condicao_visual_devolucao` em enum.
    - `dados.foto_bytes` presente (Marco 2 obrigatoria; Wave A
      diferencia por perfil).
    - `dados.termo_versao_id == TEXTO_TERMO_DEVOLUCAO_VERSAO_CANONICA`.
    """
    if recebimento.status_fluxo_lab != StatusFluxoLab.AGUARDANDO_DEVOLUCAO.value:
        raise StatusFluxoLabNaoAguardando(
            f"recebimento.status_fluxo_lab='{recebimento.status_fluxo_lab}' "
            f"— devolucao exige 'aguardando_devolucao'."
        )

    if dados.condicao_visual_devolucao not in CondicaoVisualChegada.values:
        raise CondicaoDevolucaoInvalida(
            f"condicao_visual_devolucao '{dados.condicao_visual_devolucao}' "
            "invalida."
        )

    if not dados.foto_bytes:
        raise FotoObrigatoria(
            "Foto obrigatoria na devolucao (Marco 2 dogfooding; Wave A "
            "diferencia por perfil A/B/C/D)."
        )

    if dados.termo_versao_id != TEXTO_TERMO_DEVOLUCAO_VERSAO_CANONICA:
        raise TermoVersaoInvalida(
            f"termo_versao_id '{dados.termo_versao_id}' nao reconhecido "
            f"em Marco 2 (atual: {TEXTO_TERMO_DEVOLUCAO_VERSAO_CANONICA})."
        )

    # OneToOne — checagem defensiva (DB tambem garante via constraint).
    if EquipamentoDevolucao.objects.filter(
        recebimento_id=recebimento.id
    ).exists():
        raise DevolucaoDuplicada(
            "recebimento ja tem devolucao gravada — devolucao e terminal e unica."
        )

    causation_id = causation_id or uuid4()

    # Foto: prepara ANTES do INSERT do devolucao — evita UPDATE pos-INSERT
    # bloqueado pelo trigger imutabilidade.
    try:
        preparada = preparar_foto(
            conteudo_bytes=dados.foto_bytes, mime_type=dados.foto_mime_type
        )
    except FotoInvalida:
        raise

    # Termo aceite hash (HMAC salt-tenant — defesa anti-adulteracao).
    aceite_em = datetime.now(UTC).isoformat()
    payload_aceite = (
        f"{texto_termo_devolucao(dados.termo_versao_id)}|"
        f"{devolvido_por_id}|{dados.ip_hash}|{aceite_em}"
    )
    termo_aceite_hash = hashear_pii_com_salt_tenant(payload_aceite, tenant_id)

    with transaction.atomic():
        devolucao = EquipamentoDevolucao.objects.create(
            tenant_id=tenant_id,
            recebimento=recebimento,
            condicao_visual_devolucao=dados.condicao_visual_devolucao,
            foto_storage_key=preparada.storage_key,
            foto_sha256=preparada.foto_sha256,
            termo_devolucao_versao_id=dados.termo_versao_id,
            termo_aceite_hash=termo_aceite_hash,
            devolvido_por_id=devolvido_por_id,
        )

        # Persiste BLOB da foto na tabela paralela
        # `EquipamentoDevolucaoFoto` (OneToOne com devolucao).
        from src.infrastructure.equipamentos.models import (
            EquipamentoDevolucaoFoto,
        )

        EquipamentoDevolucaoFoto.objects.create(
            tenant_id=tenant_id,
            devolucao=devolucao,
            storage_key=preparada.storage_key,
            conteudo_bytes=preparada.bytes_limpos,
            mime_type=preparada.mime_type,
            tamanho_bytes=preparada.tamanho_bytes,
        )

        # Transiciona recebimento.status_fluxo_lab -> devolvido (trigger
        # PG `transicao_status_fluxo_lab` valida; estados intermediarios
        # sao bloqueados).
        try:
            EquipamentoRecebimento.objects.filter(id=recebimento.id).update(
                status_fluxo_lab=StatusFluxoLab.DEVOLVIDO.value
            )
        except (IntegrityError, ProgrammingError) as exc:
            raise StatusFluxoLabNaoAguardando(
                f"transicao status_fluxo_lab para 'devolvido' bloqueada: {exc}"
            ) from exc

        # Atualiza Equipamento.status -> ativo (sai de em_calibracao_lab).
        try:
            Equipamento.objects.filter(id=equipamento.id).update(
                status=EquipamentoStatus.ATIVO.value
            )
        except (IntegrityError, ProgrammingError):
            # Equipamento pode estar em estado nao-em_calibracao_lab
            # (raro mas possivel — admin moveu manualmente). Devolucao
            # permanece gravada; status do equipamento mantido.
            pass

        recebimento.refresh_from_db()
        equipamento.refresh_from_db()

        # P-EQP-S3 / RAT-EQP-FOTO — payload sanitizado.
        evento = publicar_evento(
            acao="equipamento.devolvido",
            tenant_id=tenant_id,
            usuario_id=devolvido_por_id,
            causation_id=causation_id,
            payload={
                "tenant_id": str(tenant_id),
                "equipamento_id": str(equipamento.id),
                "recebimento_id": str(recebimento.id),
                "devolucao_id": str(devolucao.id),
                "condicao_visual_devolucao": (
                    devolucao.condicao_visual_devolucao
                ),
                "foto_sha256": devolucao.foto_sha256,
                "termo_versao_id": devolucao.termo_devolucao_versao_id,
                "termo_aceite_hash": termo_aceite_hash,
                "devolvido_em": devolucao.devolvido_em.isoformat(),
            },
            resource_summary=(
                f"equipamento:{equipamento.id}:devolvido:{devolucao.id}"
            ),
        )

    return ResultadoDevolucao(
        devolucao=devolucao,
        foto_storage_key=preparada.storage_key,
        foto_sha256=preparada.foto_sha256,
        termo_aceite_hash=termo_aceite_hash,
        cadeia_linha_id=evento.cadeia_linha_id,
        outbox_enfileirado=evento.outbox_enfileirado,
    )
