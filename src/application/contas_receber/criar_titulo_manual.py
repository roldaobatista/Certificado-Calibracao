"""Use case `criar_titulo_manual` — US-CR-001 lançamento manual (T-CR-030).

Fluxo (D-CR-13):
  1. Deriva `categoria_receita` se não informada (pelo `perfil_no_evento` — D-CR-5).
  2. Valida `categoria_permitida` perfil-aware NO USE CASE (ADR-0073/INV-FIN-PERFIL-001).
     Mismatch → levanta `CategoriaReceitaExigePerfilA` (view mapeia → 403 +
     evento `contas_receber.categoria_receita_bloqueada`).
  3. Exige cliente via `cliente_referencia_hash` + `cliente_key_id` (D-CR-16).
  4. Cria `Titulo` estado=emitido. NÃO publica evento — a view publica (molde fiscal).
  5. Persiste via `repo.salvar_novo_titulo`.

`perfil_no_evento` vem resolvido server-side pelo caller (view, molde fiscal D-CR-6).
Todo valor monetário = `Dinheiro` (centavos). Sem gateway.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from uuid import UUID, uuid4

from src.domain.contas_receber.categoria import (
    categoria_permitida,
    categoria_por_perfil_evento,
)
from src.domain.contas_receber.entities import Titulo
from src.domain.contas_receber.enums import (
    CategoriaReceita,
    EstadoTitulo,
    MeioCobranca,
    OrigemTitulo,
)
from src.domain.contas_receber.erros import ClienteObrigatorio
from src.domain.contas_receber.portas import TituloRepository
from src.domain.shared.value_objects import Dinheiro, ReferenciaPIIAnonimizavel


@dataclass(frozen=True, slots=True)
class CriarTituloManualInput:
    """Payload de criação manual.

    `perfil_no_evento` vem server-side (ContextVar via `obter_perfil_tenant_corrente`).
    `categoria_receita` é opcional: se None, derivada automaticamente pelo perfil
    (D-CR-5). Se informada, é validada contra o perfil.

    `cliente_referencia_hash` + `cliente_key_id` são obrigatórios (D-CR-16).
    `cliente_atual_id` é opcional (FK lógica; pode ser None se cliente anonimizado).
    """

    tenant_id: UUID
    cliente_referencia_hash: str
    cliente_key_id: str
    valor_centavos: int
    data_vencimento: date
    meio: MeioCobranca
    perfil_no_evento: str  # CHAR(1): A/B/C/D — server-side
    origem: OrigemTitulo = OrigemTitulo.MANUAL
    cliente_atual_id: UUID | None = None
    categoria_receita: CategoriaReceita | None = None
    metadata: dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.cliente_referencia_hash:
            raise ClienteObrigatorio(
                "criar_titulo_manual: cliente_referencia_hash é obrigatório (D-CR-16)."
            )
        if not self.cliente_key_id:
            raise ClienteObrigatorio("criar_titulo_manual: cliente_key_id é obrigatório (D-CR-16).")
        if self.valor_centavos <= 0:
            raise ValueError("criar_titulo_manual: valor_centavos deve ser > 0.")
        if not self.perfil_no_evento:
            raise ValueError("criar_titulo_manual: perfil_no_evento é obrigatório (D-CR-6).")


@dataclass(frozen=True, slots=True)
class CriarTituloManualOutput:
    titulo: Titulo
    categoria_derivada: bool  # True se categoria foi auto-derivada pelo perfil


def executar(
    inp: CriarTituloManualInput,
    *,
    repo: TituloRepository,
) -> CriarTituloManualOutput:
    """Cria título manual. Idempotência de negócio: sem id de origem (manual).

    Retorna o título criado. Evento WORM/outbox publicado pela view (molde fiscal).
    """
    # 1. Deriva ou usa a categoria informada (D-CR-5)
    categoria_derivada = False
    if inp.categoria_receita is None:
        categoria = categoria_por_perfil_evento(inp.perfil_no_evento)
        categoria_derivada = True
    else:
        categoria = inp.categoria_receita

    # 2. Valida permissão perfil × categoria (ADR-0073 / INV-FIN-PERFIL-001)
    # Levanta CategoriaReceitaExigePerfilA se mismatch → view mapeia 403.
    categoria_permitida(categoria, inp.perfil_no_evento)

    # 3. Monta referência PII segura do cliente (D-CR-16 / ADR-0032)
    cliente_referencia = ReferenciaPIIAnonimizavel(
        uuid_atual_id=inp.cliente_atual_id,
        hash_original=inp.cliente_referencia_hash,
        key_id=inp.cliente_key_id,
    )

    # 4. Cria entidade imutável
    agora = datetime.now(UTC)
    titulo = Titulo(
        titulo_id=uuid4(),
        tenant_id=inp.tenant_id,
        cliente_referencia=cliente_referencia,
        valor_original=Dinheiro(centavos=inp.valor_centavos, moeda="BRL"),
        data_emissao=agora.date(),
        data_vencimento=inp.data_vencimento,
        estado=EstadoTitulo.EMITIDO,
        meio=inp.meio,
        categoria_receita=categoria,
        perfil_no_evento=inp.perfil_no_evento,
        origem=inp.origem,
        revision=0,
        criado_em=agora,
    )

    # 5. Persiste
    repo.salvar_novo_titulo(titulo)

    return CriarTituloManualOutput(titulo=titulo, categoria_derivada=categoria_derivada)
