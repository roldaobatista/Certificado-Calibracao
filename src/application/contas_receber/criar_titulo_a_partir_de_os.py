"""Use case `criar_titulo_a_partir_de_os` — US-CR-001 auto-faturamento (T-CR-041).

Gatilho canônico = `os.concluida` enriquecido no OUTBOX (D-CR-12). O consumer
(`infrastructure/contas_receber/consumers/os_eventos.py`) chama este use case com
os dados já extraídos do envelope. Diferenças vs. `criar_titulo_manual`:

  1. `origem = OS` + `os_id_origem` obrigatório (FK lógica da OS).
  2. Idempotência de NEGÓCIO por `os_id` (INV-CR-OS-TITULO-UNICO): se já existe
     título ativo (não cancelado) para a OS, NÃO cria outro — retorna `ja_existia`.
     O banco garante em último caso via `UNIQUE(tenant_id, os_id_origem) WHERE
     estado != cancelado`.
  3. `perfil_no_evento` vem do ENVELOPE (`envelope["perfil_no_evento"]`), NUNCA
     relido de `obter_perfil_tenant_corrente()` no worker (D-CR-6 fail-closed —
     pegaria o perfil ATUAL e furaria a defesa CGCRE cl. 8.4 se o tenant mudou
     de perfil entre o fato gerador e o processamento). `None` → `PerfilIndeterminado`.
  4. Vencimento = data de emissão + `prazo_vencimento_dias` (default 30 — ADR-0043;
     prazo por cliente `Cliente.prazo_dias` é diferido — campo ainda não existe).

NÃO publica evento — o consumer publica `contas_receber.titulo_emitido` + `os.faturada`
na MESMA `transaction.atomic` (aberta pelo `@consumer_idempotente`). Valor já chega
em centavos (`int`) — a borda OS→CR carimba centavos no outbox (imune ao sanitizador
de auditoria; o conversor de string `valor_decimal_str_para_dinheiro` fica para a
fronteira de gateway/webhook que recebe string decimal).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from src.domain.contas_receber.categoria import categoria_por_perfil_evento
from src.domain.contas_receber.entities import Titulo
from src.domain.contas_receber.enums import (
    EstadoTitulo,
    MeioCobranca,
    OrigemTitulo,
)
from src.domain.contas_receber.erros import ClienteObrigatorio, PerfilIndeterminado
from src.domain.contas_receber.portas import TituloRepository
from src.domain.shared.value_objects import Dinheiro, ReferenciaPIIAnonimizavel

# Default ADR-0043 quando o cliente não tem prazo configurado (campo
# `Cliente.prazo_dias` ainda não existe — prazo por cliente é diferido).
PRAZO_VENCIMENTO_PADRAO_DIAS = 30


@dataclass(frozen=True, slots=True)
class CriarTituloAPartirDeOSInput:
    """Payload de auto-faturamento (consumer de `os.concluida`).

    Todos os campos vêm do envelope enriquecido (D-CR-12), exceto `perfil_no_evento`
    que vem do nível do envelope (`envelope["perfil_no_evento"]`), não do payload.
    `valor_centavos` já chega convertido a centavos pela borda OS→CR.
    """

    tenant_id: UUID
    os_id: UUID
    cliente_referencia_hash: str
    cliente_key_id: str
    valor_centavos: int
    perfil_no_evento: str | None  # do envelope; None → fail-closed
    cliente_atual_id: UUID | None = None
    meio: MeioCobranca = MeioCobranca.BOLETO
    prazo_vencimento_dias: int = PRAZO_VENCIMENTO_PADRAO_DIAS
    metadata: dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.cliente_referencia_hash:
            raise ClienteObrigatorio(
                "criar_titulo_a_partir_de_os: cliente_referencia_hash é obrigatório (D-CR-16)."
            )
        if not self.cliente_key_id:
            raise ClienteObrigatorio(
                "criar_titulo_a_partir_de_os: cliente_key_id é obrigatório (D-CR-16)."
            )
        if self.valor_centavos <= 0:
            # OS sem valor faturável (todas atividades canceladas — INV-OS-FAT-001)
            # é tratada como no-op pelo CONSUMER antes de chegar aqui; se chegou,
            # é inconsistência de dados.
            raise ValueError("criar_titulo_a_partir_de_os: valor_centavos deve ser > 0.")
        if self.prazo_vencimento_dias < 0:
            raise ValueError("criar_titulo_a_partir_de_os: prazo_vencimento_dias deve ser >= 0.")


@dataclass(frozen=True, slots=True)
class CriarTituloAPartirDeOSOutput:
    """Resultado do auto-faturamento.

    `ja_existia=True` quando a idempotência de negócio (INV-CR-OS-TITULO-UNICO)
    detectou um título ativo pré-existente para a OS — neste caso `titulo` é o
    novo título NÃO criado e o consumer NÃO republica eventos.
    """

    titulo: Titulo | None
    ja_existia: bool


def executar(
    inp: CriarTituloAPartirDeOSInput,
    *,
    repo: TituloRepository,
) -> CriarTituloAPartirDeOSOutput:
    """Cria título a partir de OS concluída. Idempotente por `os_id`.

    Levanta `PerfilIndeterminado` (fail-closed) se `perfil_no_evento` ausente.
    NÃO publica evento — responsabilidade do consumer (mesmo `atomic`).
    """
    # 1. Idempotência de negócio (INV-CR-OS-TITULO-UNICO): 1 OS → 1 título ativo.
    if repo.existe_titulo_ativo_para_os(tenant_id=inp.tenant_id, os_id=inp.os_id):
        return CriarTituloAPartirDeOSOutput(titulo=None, ja_existia=True)

    # 2. Perfil do envelope obrigatório (D-CR-6 fail-closed). NUNCA reler no worker.
    if not inp.perfil_no_evento:
        raise PerfilIndeterminado(
            "criar_titulo_a_partir_de_os: perfil_no_evento ausente no envelope de "
            "os.concluida (D-CR-6 — fail-closed, dead-letter)."
        )

    # 3. Categoria derivada do perfil (A→RBC; B/C→NAO_RBC; D→BASICA).
    #    `categoria_por_perfil_evento` levanta PerfilIndeterminado se perfil inválido.
    categoria = categoria_por_perfil_evento(inp.perfil_no_evento)

    # 4. Referência PII segura do cliente (D-CR-16 / ADR-0032).
    cliente_referencia = ReferenciaPIIAnonimizavel(
        uuid_atual_id=inp.cliente_atual_id,
        hash_original=inp.cliente_referencia_hash,
        key_id=inp.cliente_key_id,
    )

    # 5. Cria entidade imutável. Vencimento = emissão + prazo (default 30 — ADR-0043).
    agora = datetime.now(UTC)
    data_emissao = agora.date()
    data_vencimento = data_emissao + timedelta(days=inp.prazo_vencimento_dias)
    titulo = Titulo(
        titulo_id=uuid4(),
        tenant_id=inp.tenant_id,
        cliente_referencia=cliente_referencia,
        valor_original=Dinheiro(centavos=inp.valor_centavos, moeda="BRL"),
        data_emissao=data_emissao,
        data_vencimento=data_vencimento,
        estado=EstadoTitulo.EMITIDO,
        meio=inp.meio,
        categoria_receita=categoria,
        perfil_no_evento=inp.perfil_no_evento,
        origem=OrigemTitulo.OS,
        os_id_origem=inp.os_id,
        revision=0,
        criado_em=agora,
    )

    # 6. Persiste. O UNIQUE parcial do banco é a última linha de defesa contra
    #    corrida entre workers (o consumer também serializa via advisory lock).
    repo.salvar_novo_titulo(titulo)

    return CriarTituloAPartirDeOSOutput(titulo=titulo, ja_existia=False)
